"""
2026-02-19: Comprehension Capture Engine business logic (BS-CMP).

Purpose:
    Orchestrate comprehension submissions: anti-parroting check, LLM evaluation,
    weighted star formula, DayProgress update, and day unlock.
"""

import logging  # 2026-02-19: Logging
import math  # 2026-02-19: ceil()

from django.utils import timezone  # 2026-02-19: Timezone-aware timestamps

from services.teaching_engine.models import (  # 2026-02-19: Cross-app models
    TeachingLesson, DayProgress, StudentLessonProgress,
)
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-19: Loader
from .models import ComprehensionEvaluation, ComprehensionQuestionResponse  # 2026-02-19: Own models
from .parroting import is_parroting  # 2026-02-19: Anti-parroting
from .evaluator import evaluate_explanation, evaluate_key_points  # 2026-02-19: LLM evaluators

logger = logging.getLogger(__name__)  # 2026-02-19: Module logger


class ComprehensionService:
    """
    2026-02-19: Comprehension check service — evaluation, storage, day unlock.

    Sits between mastery practice (BS-STR) and day unlock. Students must pass
    the comprehension check before the next day is unlocked.
    """

    @staticmethod
    def _compute_weighted_score(
        practice_stars: int,
        comprehension_score: float,
        application_score: float = 50.0,
        retention_score: float = 50.0,
    ) -> float:
        """
        2026-02-19: Compute weighted composite score (0-100).

        Formula:
            (practice_stars / 5 × 100) × 0.30
            + comprehension_score × 0.40
            + application_score × 0.20
            + retention_score   × 0.10

        Args:
            practice_stars: Mastery practice stars (0-5).
            comprehension_score: Mean of 5 LLM dimensions (0-100).
            application_score: Placeholder score (default 50).
            retention_score: Placeholder score (default 50).

        Returns:
            float: Weighted score 0-100.
        """
        practice_pct = (practice_stars / 5.0) * 100.0  # 2026-02-19: Normalise to 0-100
        return (
            practice_pct * 0.30
            + comprehension_score * 0.40
            + application_score * 0.20
            + retention_score * 0.10
        )

    @staticmethod
    def _weighted_to_stars(weighted_score: float) -> int:
        """
        2026-02-19: Convert weighted score to star rating (0-5).

        star = min(5, ceil(weighted_score / 20))

        Args:
            weighted_score: Composite score 0-100.

        Returns:
            int: Star rating 0-5.
        """
        if weighted_score <= 0:  # 2026-02-19: Guard against zero
            return 0
        return min(5, math.ceil(weighted_score / 20.0))  # 2026-02-19: Formula

    @classmethod
    def submit_explanation(
        cls,
        student,
        lesson_id: str,
        day_number: int,
        student_text: str,
        practice_stars: int,
    ) -> dict:
        """
        2026-02-19: Submit a comprehension explanation and evaluate it.

        Flow:
        1. Load lesson summary via TeachingContentLoader.
        2. Check anti-parroting — if parroting, return early (no DB write).
        3. Run LLM evaluation across 5 dimensions.
        4. Compute comprehension_score (mean of 5 dims) and weighted_score.
        5. Persist ComprehensionEvaluation record.
        6. Update DayProgress: comprehension_score, weighted_star_rating,
           status → 'day_complete'. Also advance current_day if day < 4.
        7. Return full evaluation result with is_new_best flag.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson UUID string (primary key).
            day_number: Day number (1-4).
            student_text: The student's explanation text.
            practice_stars: Stars earned in mastery practice (0-5).

        Returns:
            dict with is_parroting, scores, weighted_star_rating, etc.
        """
        # 2026-02-19: Look up lesson by UUID primary key
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)  # 2026-02-19: UUID lookup
        except (TeachingLesson.DoesNotExist, Exception):
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        # 2026-02-19: Load lesson content for anti-parroting and topic
        try:
            day_content = TeachingContentLoader.get_day_content(
                lesson.content_json_path, day_number, 'standard'
            )
        except (FileNotFoundError, ValueError):
            day_content = {}  # 2026-02-19: Can't load → skip parroting check

        teaching_block = day_content.get('teaching_content', {})  # 2026-02-19: Lesson block
        lesson_summary = teaching_block.get(  # 2026-02-19: concept_text as summary
            'concept_text',
            teaching_block.get('text', str(teaching_block))
        )
        topic = day_content.get('title', lesson.title)  # 2026-02-19: Day title

        # 2026-02-19: Anti-parroting check
        parroting = is_parroting(student_text, lesson_summary)  # 2026-02-19: Check
        if parroting:  # 2026-02-19: Reject without DB write
            logger.info(  # 2026-02-19: Log detection
                f"Student {student.id} parroting detected on {lesson_id} day {day_number}"
            )
            return {
                'is_parroting': True,
                'message': 'Try explaining in your own words!',
            }

        # 2026-02-19: LLM evaluation
        eval_result = evaluate_explanation(student_text, lesson_summary, topic)  # 2026-02-19: Score

        # 2026-02-19: Compute comprehension_score (mean of 5 dims)
        dims = ['understanding', 'accuracy', 'own_words', 'depth', 'clarity']
        comprehension_score = sum(eval_result[d] for d in dims) / 5.0  # 2026-02-19: Mean

        # 2026-02-19: Weighted formula
        weighted_score = cls._compute_weighted_score(
            practice_stars, comprehension_score
        )
        weighted_star_rating = cls._weighted_to_stars(weighted_score)  # 2026-02-19: Stars

        # 2026-02-19: Attempt number = count of existing evals + 1
        attempt_number = ComprehensionEvaluation.objects.filter(
            student=student, lesson=lesson, day_number=day_number
        ).count() + 1  # 2026-02-19: Increment

        # 2026-02-19: Is this the best attempt?
        best_existing = ComprehensionEvaluation.objects.filter(
            student=student, lesson=lesson, day_number=day_number
        ).order_by('-weighted_star_rating').first()  # 2026-02-19: Best so far

        is_new_best = (
            best_existing is None
            or weighted_star_rating > best_existing.weighted_star_rating
        )  # 2026-02-19: New best flag

        # 2026-02-19: Persist evaluation record
        evaluation = ComprehensionEvaluation.objects.create(
            student=student,
            lesson=lesson,
            day_number=day_number,
            student_text=student_text,
            is_parroting=False,
            score_understanding=eval_result['understanding'],
            score_accuracy=eval_result['accuracy'],
            score_own_words=eval_result['own_words'],
            score_depth=eval_result['depth'],
            score_clarity=eval_result['clarity'],
            comprehension_score=comprehension_score,
            llm_feedback=eval_result.get('feedback', ''),
            llm_error=eval_result.get('llm_error', False),
            practice_stars=practice_stars,
            weighted_score=weighted_score,
            weighted_star_rating=weighted_star_rating,
            attempt_number=attempt_number,
        )

        # 2026-02-19: Update DayProgress
        progress = StudentLessonProgress.objects.filter(
            student=student, lesson=lesson
        ).first()

        if progress:  # 2026-02-19: Progress record exists
            day_prog = DayProgress.objects.filter(
                lesson_progress=progress, day_number=day_number
            ).first()

            if day_prog:  # 2026-02-19: Day record exists
                # 2026-02-19: Only update if this attempt improves the score
                if (
                    is_new_best
                    or day_prog.status not in ('day_complete', 'completed')
                ):
                    day_prog.comprehension_score = comprehension_score  # 2026-02-19: Store
                    day_prog.weighted_star_rating = weighted_star_rating  # 2026-02-19: Store
                    day_prog.status = 'day_complete'  # 2026-02-19: Final status
                    day_prog.completed_at = timezone.now()  # 2026-02-19: Mark done
                    day_prog.save()  # 2026-02-19: Persist

                # 2026-03-02: BS-CMP-003: Record self-explanation score in Phase 2 formula
                try:
                    from services.teaching_engine.weighted_stars import WeightedStarService  # 2026-03-02
                    WeightedStarService.record_self_explanation(day_prog, comprehension_score)
                except Exception as exc:  # 2026-03-02: Non-fatal
                    logger.warning("WeightedStarService.record_self_explanation failed: %s", exc)

                # 2026-02-19: Update lesson progress day_statuses
                statuses = progress.day_statuses or {}  # 2026-02-19: Get current
                statuses[str(day_number)] = 'day_complete'  # 2026-02-19: Update status

                if day_number < 4:  # 2026-02-19: Advance to next day
                    progress.current_day = day_number + 1  # 2026-02-19: Unlock next day
                    statuses[str(day_number + 1)] = statuses.get(
                        str(day_number + 1), 'not_started'
                    )
                else:  # 2026-02-19: Day 4 — unlock assessment (day 5)
                    progress.current_day = 5
                    statuses['5'] = statuses.get('5', 'not_started')

                progress.day_statuses = statuses  # 2026-02-19: Set
                progress.save()  # 2026-02-19: Persist

        logger.info(  # 2026-02-19: Log
            f"Student {student.id} comprehension day {day_number}: "
            f"score={comprehension_score:.1f} weighted={weighted_score:.1f} "
            f"stars={weighted_star_rating} (attempt #{attempt_number})"
        )

        return {  # 2026-02-19: Return full result
            'is_parroting': False,
            'comprehension_score': round(comprehension_score, 2),
            'weighted_star_rating': weighted_star_rating,
            'weighted_score': round(weighted_score, 2),
            'scores': {
                'understanding': eval_result['understanding'],
                'accuracy': eval_result['accuracy'],
                'own_words': eval_result['own_words'],
                'depth': eval_result['depth'],
                'clarity': eval_result['clarity'],
            },
            'feedback': eval_result.get('feedback', ''),
            'llm_error': eval_result.get('llm_error', False),
            'is_new_best': is_new_best,
            'attempt_number': attempt_number,
            'evaluation_id': str(evaluation.id),
        }

    @staticmethod
    def get_best_evaluation(student, lesson_id: str, day_number: int) -> dict | None:
        """
        2026-02-19: Return the best evaluation for a student/lesson/day, or None.

        "Best" is defined as the evaluation with the highest weighted_star_rating.
        Ties broken by most recent created_at.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson UUID string.
            day_number: Day number (1-4).

        Returns:
            dict with evaluation fields, or None if no evaluations exist.
        """
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)  # 2026-02-19: UUID lookup
        except TeachingLesson.DoesNotExist:
            return None  # 2026-02-19: Not found

        best = ComprehensionEvaluation.objects.filter(
            student=student, lesson=lesson, day_number=day_number
        ).order_by('-weighted_star_rating', '-created_at').first()  # 2026-02-19: Best

        if not best:  # 2026-02-19: No evaluations
            return None

        return {  # 2026-02-19: Return evaluation data
            'evaluation_id': str(best.id),
            'day_number': best.day_number,
            'comprehension_score': best.comprehension_score,
            'weighted_score': best.weighted_score,
            'weighted_star_rating': best.weighted_star_rating,
            'scores': {
                'understanding': best.score_understanding,
                'accuracy': best.score_accuracy,
                'own_words': best.score_own_words,
                'depth': best.score_depth,
                'clarity': best.score_clarity,
            },
            'feedback': best.llm_feedback,
            'llm_error': best.llm_error,
            'practice_stars': best.practice_stars,
            'attempt_number': best.attempt_number,
            'created_at': best.created_at.isoformat(),
        }

    # ── Marks-Based Question Methods (BS-CMP) ─────────────────────────────────

    @staticmethod
    def get_day_questions(lesson_id: str, day_number: int) -> list:
        """
        2026-02-21: Return the comprehension_questions list for a lesson day.

        Loads the content JSON via TeachingContentLoader and returns the
        comprehension_questions array. Returns an empty list for lessons that
        have no comprehension questions (backward-compatible).

        Args:
            lesson_id: TeachingLesson UUID string.
            day_number: Day number (1-4).

        Returns:
            list: Comprehension question dicts from the content JSON, or [].
        """
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)  # 2026-02-21: UUID lookup
        except (TeachingLesson.DoesNotExist, Exception):
            return []  # 2026-02-21: Lesson not found → empty list

        try:
            day_content = TeachingContentLoader.get_day_content(
                lesson.content_json_path, day_number, 'standard'
            )  # 2026-02-21: Load day content
        except (FileNotFoundError, ValueError):
            return []  # 2026-02-21: File or day not found → empty list

        return day_content.get('comprehension_questions', [])  # 2026-02-21: Backward-compatible

    @classmethod
    def submit_question_answer(
        cls,
        student,
        lesson_id: str,
        day_number: int,
        question_id: str,
        student_text: str,
        input_method: str,
    ) -> dict:
        """
        2026-02-21: Submit a student's answer to a marks-based comprehension question.

        Flow:
        1. Look up lesson by UUID.
        2. Load comprehension_questions from content JSON; find matching question_id.
        3. Extract key_points and question_text server-side (prevents gaming).
        4. Call evaluate_key_points() via LLM (falls back on error).
        5. Persist ComprehensionQuestionResponse record.
        6. If ALL questions for this day now have ≥1 response, update DayProgress:
           comprehension_score, weighted_star_rating, status='day_complete', advance current_day.
        7. Return evaluation result including is_new_best flag.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson UUID string.
            day_number: Day number (1-4).
            question_id: Question ID from the content JSON (e.g. "D1_CQ1").
            student_text: The student's typed or transcribed answer.
            input_method: 'typed' or 'spoken'.

        Returns:
            dict with marks_awarded, marks_available, key_points_covered,
            key_points_text, feedback, llm_error, attempt_number, is_new_best.
            Or error dict with 'code' key on failure.
        """
        # 2026-02-21: Look up lesson
        try:
            lesson = TeachingLesson.objects.get(id=lesson_id)  # 2026-02-21: UUID lookup
        except (TeachingLesson.DoesNotExist, Exception):
            return {'success': False, 'error': 'Lesson not found.', 'code': 'LESSON_NOT_FOUND'}

        # 2026-02-21: Load comprehension_questions from content JSON (server-side)
        try:
            day_content = TeachingContentLoader.get_day_content(
                lesson.content_json_path, day_number, 'standard'
            )
        except (FileNotFoundError, ValueError):
            return {'success': False, 'error': 'Day content not found.', 'code': 'DAY_NOT_FOUND'}

        all_questions = day_content.get('comprehension_questions', [])  # 2026-02-21: All Qs

        # 2026-02-21: Find the matching question by ID
        question_data = next(
            (q for q in all_questions if q.get('id') == question_id), None
        )
        if question_data is None:  # 2026-02-21: Not found
            return {
                'success': False,
                'error': f'Question {question_id!r} not found for day {day_number}.',
                'code': 'QUESTION_NOT_FOUND',
            }

        # 2026-02-21: Extract server-side fields (students cannot game key points)
        key_points = question_data.get('key_points', [])  # 2026-02-21: Authoritative points
        question_text = question_data.get('question', '')  # 2026-02-21: Question text
        model_answer = question_data.get('model_answer', '')  # 2026-02-21: Gold standard
        marks_available = question_data.get('marks', len(key_points))  # 2026-02-21: Marks

        # 2026-02-21: LLM evaluation of key points
        eval_result = evaluate_key_points(
            student_text=student_text,
            key_points=key_points,
            question=question_text,
            model_answer=model_answer,
        )

        covered = eval_result['covered']  # 2026-02-21: List of booleans
        marks_awarded = sum(1 for c in covered if c)  # 2026-02-21: Count True values
        feedback = eval_result.get('feedback', '')  # 2026-02-21: Encouraging sentence
        llm_error = eval_result.get('llm_error', False)  # 2026-02-21: Error flag

        # 2026-02-21: Attempt number = count of existing responses + 1
        attempt_number = ComprehensionQuestionResponse.objects.filter(
            student=student, lesson=lesson, day_number=day_number, question_id=question_id
        ).count() + 1

        # 2026-02-21: Is this the best attempt for this question?
        best_existing = ComprehensionQuestionResponse.objects.filter(
            student=student, lesson=lesson, day_number=day_number, question_id=question_id
        ).order_by('-marks_awarded').first()
        is_new_best = (
            best_existing is None
            or marks_awarded > best_existing.marks_awarded
        )

        # 2026-02-21: Persist the response record
        ComprehensionQuestionResponse.objects.create(
            student=student,
            lesson=lesson,
            day_number=day_number,
            question_id=question_id,
            question_text=question_text,
            marks_available=marks_available,
            student_text=student_text,
            input_method=input_method,
            key_points_covered=covered,
            marks_awarded=marks_awarded,
            llm_feedback=feedback,
            llm_error=llm_error,
            attempt_number=attempt_number,
        )

        # 2026-02-21: Check if ALL questions for this day have ≥1 response
        answered_ids = set(
            ComprehensionQuestionResponse.objects.filter(
                student=student, lesson=lesson, day_number=day_number
            ).values_list('question_id', flat=True).distinct()
        )
        all_question_ids = {q.get('id') for q in all_questions}
        all_answered = bool(all_question_ids) and (all_question_ids <= answered_ids)

        if all_answered:  # 2026-02-21: All questions answered → complete day
            cls._complete_day_via_comprehension(
                student, lesson, day_number, all_questions
            )

        logger.info(  # 2026-02-21: Log result
            f"Student {student.id} answered {question_id} day {day_number}: "
            f"{marks_awarded}/{marks_available} marks (attempt #{attempt_number})"
        )

        return {  # 2026-02-21: Return evaluation result
            'marks_awarded': marks_awarded,
            'marks_available': marks_available,
            'key_points_covered': covered,
            'key_points_text': key_points,  # 2026-02-21: Revealed after submission
            'feedback': feedback,
            'llm_error': llm_error,
            'attempt_number': attempt_number,
            'is_new_best': is_new_best,
        }

    @staticmethod
    def _complete_day_via_comprehension(student, lesson, day_number: int, all_questions: list):
        """
        2026-02-21: Update DayProgress when all comprehension questions are answered.

        Computes comprehension_score as total_marks_awarded / total_marks_available * 100.
        Sets weighted_star_rating = min(5, ceil(comprehension_score / 20)).
        Sets status = 'day_complete' and advances current_day.

        Args:
            student: Student model instance.
            lesson: TeachingLesson model instance.
            day_number: Day number (1-4).
            all_questions: Full list of comprehension question dicts for the day.
        """
        # 2026-02-21: Compute total marks available across all questions
        total_available = sum(q.get('marks', 0) for q in all_questions)

        if total_available == 0:  # 2026-02-21: Guard against zero division
            return

        # 2026-02-21: Aggregate best marks_awarded per question for this student+day
        total_awarded = 0
        for q in all_questions:  # 2026-02-21: Best attempt per question
            qid = q.get('id')
            best = ComprehensionQuestionResponse.objects.filter(
                student=student, lesson=lesson, day_number=day_number, question_id=qid
            ).order_by('-marks_awarded').first()
            if best:  # 2026-02-21: Take best attempt score
                total_awarded += best.marks_awarded

        comprehension_score = (total_awarded / total_available) * 100.0  # 2026-02-21: Percentage
        weighted_star_rating = min(5, math.ceil(comprehension_score / 20.0))  # 2026-02-21: Stars

        # 2026-02-21: Update DayProgress record
        progress = StudentLessonProgress.objects.filter(
            student=student, lesson=lesson
        ).first()

        if not progress:  # 2026-02-21: No progress record
            return

        day_prog = DayProgress.objects.filter(
            lesson_progress=progress, day_number=day_number
        ).first()

        if day_prog:  # 2026-02-21: Update existing DayProgress
            day_prog.comprehension_score = comprehension_score
            day_prog.weighted_star_rating = weighted_star_rating
            day_prog.status = 'day_complete'
            day_prog.completed_at = timezone.now()
            day_prog.save()

            # 2026-03-02: BS-CMP-003: Record self-explanation score in Phase 2 formula
            try:
                from services.teaching_engine.weighted_stars import WeightedStarService  # 2026-03-02
                WeightedStarService.record_self_explanation(day_prog, comprehension_score)
            except Exception as exc:  # 2026-03-02: Non-fatal
                logger.warning("WeightedStarService.record_self_explanation (question) failed: %s", exc)

        # 2026-02-21: Advance current_day in StudentLessonProgress
        statuses = progress.day_statuses or {}
        statuses[str(day_number)] = 'day_complete'

        if day_number < 4:  # 2026-02-21: Unlock next day
            progress.current_day = day_number + 1
            statuses[str(day_number + 1)] = statuses.get(str(day_number + 1), 'not_started')
        else:  # 2026-02-21: Day 4 → unlock assessment (day 5)
            progress.current_day = 5
            statuses['5'] = statuses.get('5', 'not_started')

        progress.day_statuses = statuses
        progress.save()

        logger.info(  # 2026-02-21: Log completion
            f"Day {day_number} completed via comprehension for student {student.id}: "
            f"score={comprehension_score:.1f}% stars={weighted_star_rating}"
        )
