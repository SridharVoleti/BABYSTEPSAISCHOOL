"""
2026-02-17: AI Teaching Engine business logic service.

Purpose:
    Core teaching operations: list lessons, start/complete days,
    get/submit weekly assessments. Delegates content loading to
    TeachingContentLoader and IQ level lookup to DiagnosticResult.
"""

import logging  # 2026-02-17: Logging

from django.utils import timezone  # 2026-02-17: Timezone-aware timestamps

from services.diagnostic_service.models import DiagnosticResult  # 2026-02-17: IQ level source
from .models import (  # 2026-02-17: Models
    TeachingLesson, StudentLessonProgress, DayProgress,
    WeeklyAssessmentAttempt,
    PracticeSession, PracticeResponse, ConceptMastery,  # 2026-02-18: Mastery practice models
)
from .content_loader import TeachingContentLoader  # 2026-02-17: Content loader
from .adaptive import AdaptiveEngine  # 2026-02-18: Adaptive difficulty engine

logger = logging.getLogger(__name__)  # 2026-02-17: Module logger


class TeachingService:
    """2026-02-17: Core AI Teaching Engine service with all business logic."""

    @classmethod
    def get_student_iq_level(cls, student):
        """
        2026-02-17: Get student's IQ level from diagnostic result.

        Falls back to 'standard' if no diagnostic result exists.

        Args:
            student: Student model instance.

        Returns:
            str: One of 'foundation', 'standard', 'advanced'.
        """
        result = DiagnosticResult.objects.filter(student=student).first()  # 2026-02-17: Lookup
        if not result:  # 2026-02-17: No diagnostic result
            return 'standard'  # 2026-02-17: Default fallback
        return result.overall_level  # 2026-02-17: From diagnostic

    @classmethod
    def list_lessons(cls, class_number, subject=None):
        """
        2026-02-17: List published lessons for a grade, optionally filtered by subject.

        Args:
            class_number: Grade number (1-12).
            subject: Optional subject filter.

        Returns:
            dict: Success response with list of lessons.
        """
        queryset = TeachingLesson.objects.filter(  # 2026-02-17: Published only
            class_number=class_number, status='published'
        )
        if subject:  # 2026-02-17: Optional subject filter
            queryset = queryset.filter(subject=subject)

        lessons = []  # 2026-02-17: Build list
        for lesson in queryset:  # 2026-02-17: Iterate
            lessons.append({  # 2026-02-17: Lesson summary
                'id': str(lesson.id),
                'lesson_id': lesson.lesson_id,
                'title': lesson.title,
                'subject': lesson.subject,
                'class_number': lesson.class_number,
                'chapter_title': lesson.chapter_title,
                'week_number': lesson.week_number,
                'character_name': lesson.character_name,
                'learning_objectives': lesson.learning_objectives,
            })

        return {'success': True, 'lessons': lessons}  # 2026-02-17: Return

    @classmethod
    def get_lesson_detail(cls, student, lesson_id):
        """
        2026-02-17: Get lesson detail with student's progress.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.

        Returns:
            dict: Lesson detail with progress info.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-17: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-17: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        # 2026-02-17: Get or default progress
        progress = StudentLessonProgress.objects.filter(
            student=student, lesson=lesson
        ).first()

        progress_data = None  # 2026-02-17: Default
        if progress:  # 2026-02-17: Has progress
            progress_data = {
                'current_day': progress.current_day,
                'iq_level': progress.iq_level,
                'day_statuses': progress.day_statuses,
                'status': progress.status,
                'total_score': progress.total_score,
                'assessment_score': progress.assessment_score,
                'assessment_star_rating': progress.assessment_star_rating,
            }

        return {  # 2026-02-17: Return detail
            'success': True,
            'lesson': {
                'id': str(lesson.id),
                'lesson_id': lesson.lesson_id,
                'title': lesson.title,
                'subject': lesson.subject,
                'class_number': lesson.class_number,
                'chapter_title': lesson.chapter_title,
                'week_number': lesson.week_number,
                'character_name': lesson.character_name,
                'learning_objectives': lesson.learning_objectives,
            },
            'progress': progress_data,
        }

    @classmethod
    def start_day(cls, student, lesson_id, day_number=None):
        """
        2026-02-17: Start a day's micro-lesson with IQ-appropriate content.

        Creates progress records on first access. Returns revision prompts
        (for days 2-4) and IQ-filtered teaching content.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.
            day_number: Optional day to start (defaults to current_day).

        Returns:
            dict: Day content with revision prompts and teaching material.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-17: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-17: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        # 2026-02-17: Get or create progress
        iq_level = cls.get_student_iq_level(student)  # 2026-02-17: IQ from diagnostic
        progress, created = StudentLessonProgress.objects.get_or_create(
            student=student, lesson=lesson,
            defaults={  # 2026-02-17: First time
                'iq_level': iq_level,
                'current_day': 1,
                'day_statuses': {'1': 'not_started', '2': 'not_started', '3': 'not_started', '4': 'not_started', '5': 'not_started'},
            }
        )

        if progress.status == 'completed':  # 2026-02-17: Already done
            return {
                'success': False,
                'error': 'Lesson already completed.',
                'code': 'LESSON_COMPLETED',
            }

        # 2026-02-17: Determine which day to start
        target_day = day_number if day_number else progress.current_day  # 2026-02-17: Default to current

        if target_day < 1 or target_day > 4:  # 2026-02-17: Validate
            return {
                'success': False,
                'error': 'Day number must be 1-4 for micro-lessons.',
                'code': 'INVALID_DAY',
            }

        # 2026-02-17: Check day sequence (can't skip ahead)
        if target_day > progress.current_day:  # 2026-02-17: Trying to skip
            return {
                'success': False,
                'error': f'Complete day {progress.current_day} first.',
                'code': 'DAY_NOT_UNLOCKED',
            }

        # 2026-02-18: Mastery gate check — previous day must be mastered (≥3 stars)
        if target_day > 1:  # 2026-02-18: Days 2-4 require previous day mastery
            prev_mastery = ConceptMastery.objects.filter(
                student=student, lesson=lesson, day_number=target_day - 1
            ).first()
            if prev_mastery and not prev_mastery.is_mastered:  # 2026-02-18: Not mastered
                return {
                    'success': False,
                    'error': f'Achieve 3+ stars on day {target_day - 1} mastery practice first.',
                    'code': 'MASTERY_GATE_LOCKED',
                }

        # 2026-02-17: Get or create DayProgress
        day_progress, day_created = DayProgress.objects.get_or_create(
            lesson_progress=progress, day_number=target_day,
            defaults={'status': 'not_started'}  # 2026-02-17: Default
        )

        # 2026-02-17: Update status if starting fresh
        if day_progress.status == 'not_started':  # 2026-02-17: First start
            if target_day > 1:  # 2026-02-17: Days 2-4 start with revision
                day_progress.status = 'revision'
            else:  # 2026-02-17: Day 1 goes straight to teaching
                day_progress.status = 'teaching'
            day_progress.started_at = timezone.now()  # 2026-02-17: Mark start
            day_progress.save()  # 2026-02-17: Persist

        # 2026-02-17: Update lesson progress day_statuses
        statuses = progress.day_statuses or {}  # 2026-02-17: Get current
        statuses[str(target_day)] = day_progress.status  # 2026-02-17: Update
        progress.day_statuses = statuses  # 2026-02-17: Set
        progress.save()  # 2026-02-17: Persist

        # 2026-02-17: Load content
        try:
            day_content = TeachingContentLoader.get_day_content(  # 2026-02-17: IQ-filtered
                lesson.content_json_path, target_day, progress.iq_level
            )
            revision_prompts = TeachingContentLoader.get_revision_prompts(  # 2026-02-17: Revision
                lesson.content_json_path, target_day, progress.iq_level
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-17: Content error
            logger.error(f"Content load error for {lesson_id} day {target_day}: {e}")
            return {
                'success': False,
                'error': 'Lesson content not available.',
                'code': 'CONTENT_ERROR',
            }

        logger.info(  # 2026-02-17: Log
            f"Student {student.id} started {lesson_id} day {target_day} ({progress.iq_level})"
        )

        return {  # 2026-02-17: Return day content
            'success': True,
            'lesson_id': lesson_id,
            'day_number': target_day,
            'iq_level': progress.iq_level,
            'day_status': day_progress.status,
            'revision_prompts': revision_prompts,
            'content': day_content,
        }

    @classmethod
    def complete_day(cls, student, lesson_id, day_number, practice_answers, time_spent):
        """
        2026-02-17: Complete a day's micro-lesson with practice scores.

        Scores practice answers, updates progress, and advances to next day.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.
            day_number: Day number (1-4) being completed.
            practice_answers: dict mapping question_id -> selected option index.
            time_spent: Time spent in seconds.

        Returns:
            dict: Completion result with score and next day info.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-17: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-17: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        progress = StudentLessonProgress.objects.filter(  # 2026-02-17: Get progress
            student=student, lesson=lesson
        ).first()

        if not progress:  # 2026-02-17: No progress
            return {
                'success': False,
                'error': 'Start the lesson first.',
                'code': 'NO_PROGRESS',
            }

        # 2026-02-17: Get DayProgress
        day_progress = DayProgress.objects.filter(
            lesson_progress=progress, day_number=day_number
        ).first()

        if not day_progress:  # 2026-02-17: Not started
            return {
                'success': False,
                'error': f'Start day {day_number} first.',
                'code': 'DAY_NOT_STARTED',
            }

        if day_progress.status == 'completed':  # 2026-02-17: Already done
            return {
                'success': False,
                'error': f'Day {day_number} already completed.',
                'code': 'DAY_COMPLETED',
            }

        # 2026-02-17: Score practice answers
        try:
            day_content = TeachingContentLoader.get_day_content(  # 2026-02-17: Load content
                lesson.content_json_path, day_number, progress.iq_level
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-17: Content error
            logger.error(f"Content load error: {e}")
            return {
                'success': False,
                'error': 'Lesson content not available.',
                'code': 'CONTENT_ERROR',
            }

        questions = day_content.get('practice_questions', [])  # 2026-02-17: Get questions
        correct_count = 0  # 2026-02-17: Score counter
        total_count = len(questions)  # 2026-02-17: Total questions

        for q in questions:  # 2026-02-17: Score each answer
            q_id = q.get('id')  # 2026-02-17: Question ID
            student_answer = practice_answers.get(q_id)  # 2026-02-17: Student's answer
            if student_answer is not None and student_answer == q.get('correct_answer'):  # 2026-02-17: Check
                correct_count += 1  # 2026-02-17: Correct

        score = (correct_count * 100 // total_count) if total_count > 0 else 0  # 2026-02-17: Percentage

        # 2026-02-18: Update DayProgress — transition to mastery_practice instead of completed
        day_progress.status = 'mastery_practice'  # 2026-02-18: Awaiting mastery practice
        day_progress.practice_score = score  # 2026-02-17: Set score
        day_progress.questions_attempted = len(practice_answers)  # 2026-02-17: Attempted
        day_progress.questions_correct = correct_count  # 2026-02-17: Correct
        day_progress.time_spent_seconds = time_spent  # 2026-02-17: Time
        day_progress.revision_completed = True  # 2026-02-17: Revision done (implicit)
        day_progress.save()  # 2026-02-17: Persist

        # 2026-02-18: Update lesson progress — don't advance current_day yet (mastery gate)
        progress.total_score += score  # 2026-02-17: Cumulative score
        statuses = progress.day_statuses or {}  # 2026-02-17: Day statuses
        statuses[str(day_number)] = 'mastery_practice'  # 2026-02-18: Awaiting mastery

        progress.day_statuses = statuses  # 2026-02-17: Update
        progress.save()  # 2026-02-17: Persist

        logger.info(  # 2026-02-17: Log
            f"Student {student.id} completed {lesson_id} day {day_number}: "
            f"{correct_count}/{total_count} ({score}%) — mastery practice next"
        )

        return {  # 2026-02-18: Return result with mastery_practice_required flag
            'success': True,
            'lesson_id': lesson_id,
            'day_number': day_number,
            'score': score,
            'questions_correct': correct_count,
            'questions_total': total_count,
            'mastery_practice_required': True,  # 2026-02-18: Signal to frontend
        }

    @classmethod
    def get_assessment(cls, student, lesson_id):
        """
        2026-02-17: Get Day 5 weekly assessment (blocked until days 1-4 done).

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.

        Returns:
            dict: Assessment questions or error if not unlocked.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-17: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-17: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        progress = StudentLessonProgress.objects.filter(  # 2026-02-17: Get progress
            student=student, lesson=lesson
        ).first()

        if not progress:  # 2026-02-17: No progress
            return {
                'success': False,
                'error': 'Start the lesson first.',
                'code': 'NO_PROGRESS',
            }

        # 2026-02-17: Check all 4 days completed
        if progress.current_day < 5:  # 2026-02-17: Not ready
            return {
                'success': False,
                'error': f'Complete all 4 micro-lessons first. Currently on day {progress.current_day}.',
                'code': 'ASSESSMENT_LOCKED',
            }

        # 2026-02-17: Load assessment from content
        try:
            assessment = TeachingContentLoader.get_assessment(  # 2026-02-17: Load
                lesson.content_json_path
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-17: Content error
            logger.error(f"Assessment load error for {lesson_id}: {e}")
            return {
                'success': False,
                'error': 'Assessment content not available.',
                'code': 'CONTENT_ERROR',
            }

        # 2026-02-17: Strip correct answers for client
        questions = []  # 2026-02-17: Client-safe questions
        for q in assessment.get('questions', []):  # 2026-02-17: Iterate
            questions.append({  # 2026-02-17: No correct_answer
                'id': q['id'],
                'type': q['type'],
                'question': q['question'],
                'options': q['options'],
                'points': q['points'],
            })

        # 2026-02-17: Get attempt count
        attempt_count = WeeklyAssessmentAttempt.objects.filter(
            lesson_progress=progress
        ).count()

        return {  # 2026-02-17: Return assessment
            'success': True,
            'lesson_id': lesson_id,
            'assessment_id': assessment.get('assessment_id'),
            'title': assessment.get('title'),
            'time_limit_minutes': assessment.get('time_limit_minutes'),
            'questions': questions,
            'attempt_number': attempt_count + 1,
        }

    @classmethod
    def submit_assessment(cls, student, lesson_id, answers, time_spent):
        """
        2026-02-17: Submit Day 5 weekly assessment and compute star rating.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.
            answers: dict mapping question_id -> selected option index.
            time_spent: Time spent in seconds.

        Returns:
            dict: Assessment result with score and star rating.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-17: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-17: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        progress = StudentLessonProgress.objects.filter(  # 2026-02-17: Get progress
            student=student, lesson=lesson
        ).first()

        if not progress:  # 2026-02-17: No progress
            return {
                'success': False,
                'error': 'Start the lesson first.',
                'code': 'NO_PROGRESS',
            }

        if progress.current_day < 5:  # 2026-02-17: Not unlocked
            return {
                'success': False,
                'error': 'Complete all 4 micro-lessons first.',
                'code': 'ASSESSMENT_LOCKED',
            }

        # 2026-02-17: Load assessment for scoring
        try:
            assessment = TeachingContentLoader.get_assessment(  # 2026-02-17: Load
                lesson.content_json_path
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-17: Content error
            logger.error(f"Assessment load error for {lesson_id}: {e}")
            return {
                'success': False,
                'error': 'Assessment content not available.',
                'code': 'CONTENT_ERROR',
            }

        # 2026-02-17: Score answers
        questions = assessment.get('questions', [])  # 2026-02-17: All questions
        total_points = 0  # 2026-02-17: Max possible
        earned_points = 0  # 2026-02-17: Earned

        for q in questions:  # 2026-02-17: Score each
            points = q.get('points', 1)  # 2026-02-17: Points per question
            total_points += points  # 2026-02-17: Add to total
            student_answer = answers.get(q['id'])  # 2026-02-17: Student's answer
            if student_answer is not None and student_answer == q.get('correct_answer'):  # 2026-02-17: Correct
                earned_points += points  # 2026-02-17: Award points

        # 2026-02-17: Calculate percentage and star rating
        percentage = (earned_points * 100 // total_points) if total_points > 0 else 0
        thresholds = assessment.get('star_thresholds', {})  # 2026-02-17: Rating thresholds
        star_rating = 0  # 2026-02-17: Default
        if percentage >= thresholds.get('three_stars', 80):  # 2026-02-17: 3 stars
            star_rating = 3
        elif percentage >= thresholds.get('two_stars', 60):  # 2026-02-17: 2 stars
            star_rating = 2
        elif percentage >= thresholds.get('one_star', 40):  # 2026-02-17: 1 star
            star_rating = 1

        # 2026-02-17: Get attempt number
        attempt_count = WeeklyAssessmentAttempt.objects.filter(
            lesson_progress=progress
        ).count()

        # 2026-02-17: Create attempt record
        attempt = WeeklyAssessmentAttempt.objects.create(
            lesson_progress=progress,
            attempt_number=attempt_count + 1,
            answers=answers,
            score=earned_points,
            total_points=total_points,
            star_rating=star_rating,
            time_spent_seconds=time_spent,
            submitted_at=timezone.now(),
        )

        # 2026-02-17: Update progress with best score
        if star_rating > progress.assessment_star_rating:  # 2026-02-17: New best
            progress.assessment_star_rating = star_rating
        progress.assessment_score = earned_points  # 2026-02-17: Latest score
        progress.status = 'completed'  # 2026-02-17: Mark lesson complete
        progress.completed_at = timezone.now()  # 2026-02-17: Completion time
        statuses = progress.day_statuses or {}  # 2026-02-17: Update day 5
        statuses['5'] = 'completed'  # 2026-02-17: Assessment done
        progress.day_statuses = statuses  # 2026-02-17: Set
        progress.save()  # 2026-02-17: Persist

        logger.info(  # 2026-02-17: Log
            f"Student {student.id} submitted assessment for {lesson_id}: "
            f"{earned_points}/{total_points} ({percentage}%) - {star_rating} stars"
        )

        return {  # 2026-02-17: Return result
            'success': True,
            'lesson_id': lesson_id,
            'attempt_number': attempt.attempt_number,
            'score': earned_points,
            'total_points': total_points,
            'percentage': percentage,
            'star_rating': star_rating,
        }


class MasteryPracticeService:
    """
    2026-02-18: Mastery practice service for adaptive post-lesson practice (BS-STR).

    Manages the adaptive mastery practice flow: starting sessions,
    submitting answers one at a time, computing star ratings, and
    enforcing the mastery gate for day progression.
    """

    @classmethod
    def start_practice(cls, student, lesson_id, day_number):
        """
        2026-02-18: Start a mastery practice session for a day.

        Creates a PracticeSession and returns the first question.
        Requires the day to be in 'mastery_practice' status.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.
            day_number: Day number (1-4).

        Returns:
            dict: Session info and first question, or error.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-18: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-18: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        progress = StudentLessonProgress.objects.filter(  # 2026-02-18: Get progress
            student=student, lesson=lesson
        ).first()

        if not progress:  # 2026-02-18: No progress
            return {
                'success': False,
                'error': 'Start the lesson first.',
                'code': 'NO_PROGRESS',
            }

        # 2026-02-18: Verify day is in mastery_practice status
        day_progress = DayProgress.objects.filter(
            lesson_progress=progress, day_number=day_number
        ).first()

        if not day_progress:  # 2026-02-18: Day not started
            return {
                'success': False,
                'error': f'Complete day {day_number} micro-lesson first.',
                'code': 'DAY_NOT_READY',
            }

        if day_progress.status == 'completed':  # 2026-02-18: Already completed
            return {
                'success': False,
                'error': f'Day {day_number} already completed.',
                'code': 'DAY_COMPLETED',
            }

        if day_progress.status != 'mastery_practice':  # 2026-02-18: Not ready
            return {
                'success': False,
                'error': f'Complete the micro-lesson for day {day_number} first.',
                'code': 'DAY_NOT_READY',
            }

        # 2026-02-18: Check for existing in-progress session
        existing_session = PracticeSession.objects.filter(
            student=student, lesson_progress=progress,
            day_number=day_number, status='in_progress'
        ).first()

        if existing_session:  # 2026-02-18: Resume existing session
            return cls._resume_session(existing_session, lesson)

        # 2026-02-18: Load practice bank
        try:
            day_bank = TeachingContentLoader.load_practice_bank(
                lesson.content_json_path, day_number
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-18: Content error
            logger.error(f"Practice bank load error for {lesson_id} day {day_number}: {e}")
            return {
                'success': False,
                'error': 'Practice content not available.',
                'code': 'CONTENT_ERROR',
            }

        # 2026-02-18: Determine question count and starting difficulty
        iq_level = progress.iq_level  # 2026-02-18: From lesson progress
        total_questions = AdaptiveEngine.get_total_questions(iq_level)  # 2026-02-18: Count
        starting_difficulty = AdaptiveEngine.get_starting_difficulty(iq_level)  # 2026-02-18: Difficulty

        # 2026-02-18: Get attempt number
        attempt_count = PracticeSession.objects.filter(
            student=student, lesson_progress=progress, day_number=day_number
        ).count()

        # 2026-02-18: Create session
        session = PracticeSession.objects.create(
            student=student,
            lesson_progress=progress,
            day_number=day_number,
            iq_level=iq_level,
            total_questions=total_questions,
            current_difficulty=starting_difficulty,
            attempt_number=attempt_count + 1,
        )

        # 2026-02-18: Select first question
        questions_bank = day_bank.get('questions', {})  # 2026-02-18: Get bank
        question, actual_difficulty = AdaptiveEngine.select_question(
            questions_bank, starting_difficulty, set()
        )

        if not question:  # 2026-02-18: No questions available
            return {
                'success': False,
                'error': 'No practice questions available.',
                'code': 'NO_QUESTIONS',
            }

        # 2026-02-18: Track administered question
        session.administered_question_ids = [question['id']]  # 2026-02-18: Track
        session.current_difficulty = actual_difficulty  # 2026-02-18: Actual difficulty
        session.same_difficulty_streak = 1  # 2026-02-18: First at this difficulty
        session.save()  # 2026-02-18: Persist

        logger.info(  # 2026-02-18: Log
            f"Student {student.id} started mastery practice for {lesson_id} "
            f"day {day_number} (attempt #{session.attempt_number}, {total_questions} Qs)"
        )

        return {  # 2026-02-18: Return session info + first question
            'success': True,
            'session_id': str(session.id),
            'lesson_id': lesson_id,
            'day_number': day_number,
            'iq_level': iq_level,
            'total_questions': total_questions,
            'current_question': 1,
            'question': cls._sanitize_question(question, actual_difficulty),
        }

    @classmethod
    def _resume_session(cls, session, lesson):
        """
        2026-02-18: Resume an in-progress practice session.

        Selects the next unanswered question.

        Args:
            session: PracticeSession instance.
            lesson: TeachingLesson instance.

        Returns:
            dict: Session info and next question.
        """
        try:
            day_bank = TeachingContentLoader.load_practice_bank(
                lesson.content_json_path, session.day_number
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-18: Content error
            logger.error(f"Practice bank resume error: {e}")
            return {
                'success': False,
                'error': 'Practice content not available.',
                'code': 'CONTENT_ERROR',
            }

        questions_bank = day_bank.get('questions', {})  # 2026-02-18: Get bank
        administered = set(session.administered_question_ids or [])  # 2026-02-18: Already used

        question, actual_difficulty = AdaptiveEngine.select_question(
            questions_bank, session.current_difficulty, administered
        )

        if not question:  # 2026-02-18: Exhausted
            return {
                'success': False,
                'error': 'No more practice questions available.',
                'code': 'QUESTIONS_EXHAUSTED',
            }

        # 2026-02-18: Track new question
        administered.add(question['id'])  # 2026-02-18: Add to set
        session.administered_question_ids = list(administered)  # 2026-02-18: Update
        session.save()  # 2026-02-18: Persist

        return {  # 2026-02-18: Return
            'success': True,
            'session_id': str(session.id),
            'lesson_id': lesson.lesson_id,
            'day_number': session.day_number,
            'iq_level': session.iq_level,
            'total_questions': session.total_questions,
            'current_question': session.questions_answered + 1,
            'question': cls._sanitize_question(question, actual_difficulty),
        }

    @classmethod
    def submit_answer(cls, student, session_id, question_id, answer,
                      time_taken=0, hints_used=0):
        """
        2026-02-18: Submit an answer for a mastery practice question.

        Checks correctness, updates adaptive state, and returns
        feedback + next question (or final result if complete).

        Args:
            student: Student model instance.
            session_id: PracticeSession UUID string.
            question_id: Question ID being answered.
            answer: Student's answer (type varies).
            time_taken: Seconds taken on this question.
            hints_used: Hints used on this question.

        Returns:
            dict: Feedback, next question, or final result.
        """
        session = PracticeSession.objects.filter(  # 2026-02-18: Lookup
            id=session_id, student=student, status='in_progress'
        ).first()

        if not session:  # 2026-02-18: Not found
            return {
                'success': False,
                'error': 'Practice session not found or already completed.',
                'code': 'SESSION_NOT_FOUND',
            }

        # 2026-02-18: Verify question was administered
        administered = session.administered_question_ids or []  # 2026-02-18: Get list
        if question_id not in administered:  # 2026-02-18: Not valid
            return {
                'success': False,
                'error': 'Question was not administered in this session.',
                'code': 'INVALID_QUESTION',
            }

        # 2026-02-18: Load the question from practice bank
        lesson = session.lesson_progress.lesson  # 2026-02-18: Get lesson
        try:
            day_bank = TeachingContentLoader.load_practice_bank(
                lesson.content_json_path, session.day_number
            )
        except (FileNotFoundError, ValueError) as e:  # 2026-02-18: Content error
            logger.error(f"Practice bank load error: {e}")
            return {
                'success': False,
                'error': 'Practice content not available.',
                'code': 'CONTENT_ERROR',
            }

        # 2026-02-18: Find the question in the bank
        question = cls._find_question(day_bank.get('questions', {}), question_id)
        if not question:  # 2026-02-18: Not found
            return {
                'success': False,
                'error': 'Question not found in practice bank.',
                'code': 'QUESTION_NOT_FOUND',
            }

        # 2026-02-18: Check answer
        is_correct, correct_answer, explanation = AdaptiveEngine.check_answer(
            question, answer
        )

        # 2026-02-18: Determine the difficulty of this question
        q_difficulty = cls._get_question_difficulty(
            day_bank.get('questions', {}), question_id
        )

        # 2026-02-18: Record response
        PracticeResponse.objects.create(
            session=session,
            question_id=question_id,
            concept_id=day_bank.get('concept_id', ''),
            difficulty=q_difficulty,
            question_type=question.get('type', 'mcq'),
            student_answer=answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
            time_taken_seconds=time_taken,
            hints_used=hints_used,
            position=session.questions_answered,
            feedback_text=explanation,
        )

        # 2026-02-18: Update session state
        session.questions_answered += 1  # 2026-02-18: Increment
        session.time_spent_seconds += time_taken  # 2026-02-18: Accumulate
        session.hints_used += hints_used  # 2026-02-18: Accumulate

        if is_correct:  # 2026-02-18: Correct answer
            session.questions_correct += 1
            session.consecutive_correct += 1
            session.consecutive_incorrect = 0
        else:  # 2026-02-18: Incorrect answer
            session.consecutive_incorrect += 1
            session.consecutive_correct = 0

        # 2026-02-18: Adapt difficulty
        new_difficulty = AdaptiveEngine.adapt_difficulty(
            session.current_difficulty,
            session.consecutive_correct,
            session.consecutive_incorrect,
            session.same_difficulty_streak,
        )

        if new_difficulty == session.current_difficulty:  # 2026-02-18: Same difficulty
            session.same_difficulty_streak += 1
        else:  # 2026-02-18: Difficulty changed
            session.current_difficulty = new_difficulty
            session.same_difficulty_streak = 1
            # 2026-02-18: Reset streaks on difficulty change
            session.consecutive_correct = 0
            session.consecutive_incorrect = 0

        session.save()  # 2026-02-18: Persist

        # 2026-02-18: Check if session is complete
        if session.questions_answered >= session.total_questions:
            return cls._complete_session(session, is_correct, correct_answer, explanation)

        # 2026-02-18: Select next question
        questions_bank = day_bank.get('questions', {})  # 2026-02-18: Get bank
        administered_set = set(session.administered_question_ids or [])

        next_question, actual_difficulty = AdaptiveEngine.select_question(
            questions_bank, session.current_difficulty, administered_set
        )

        if not next_question:  # 2026-02-18: Questions exhausted early
            return cls._complete_session(session, is_correct, correct_answer, explanation)

        # 2026-02-18: Track next question
        administered_set.add(next_question['id'])
        session.administered_question_ids = list(administered_set)
        session.save()  # 2026-02-18: Persist

        return {  # 2026-02-18: Feedback + next question
            'success': True,
            'session_id': str(session.id),
            'feedback': {
                'is_correct': is_correct,
                'correct_answer': correct_answer,
                'explanation': explanation,
            },
            'progress': {
                'questions_answered': session.questions_answered,
                'questions_correct': session.questions_correct,
                'total_questions': session.total_questions,
            },
            'next_question': cls._sanitize_question(next_question, actual_difficulty),
            'completed': False,
        }

    @classmethod
    def _complete_session(cls, session, last_is_correct, last_correct_answer,
                          last_explanation):
        """
        2026-02-18: Finalize a mastery practice session.

        Calculates star rating, updates ConceptMastery and DayProgress,
        and potentially advances to the next day.

        Args:
            session: PracticeSession instance.
            last_is_correct: Whether the last answer was correct.
            last_correct_answer: Correct answer for last question.
            last_explanation: Explanation for last question.

        Returns:
            dict: Final result with star rating and mastery status.
        """
        # 2026-02-18: Calculate final results
        star_rating = AdaptiveEngine.calculate_star_rating(
            session.questions_correct, session.questions_answered
        )
        percentage = (
            (session.questions_correct * 100.0) / session.questions_answered
            if session.questions_answered > 0 else 0.0
        )
        is_passed = AdaptiveEngine.is_mastery_passed(star_rating)

        # 2026-02-18: Update session
        session.status = 'completed'
        session.star_rating = star_rating
        session.percentage_correct = percentage
        session.save()

        # 2026-02-18: Update or create ConceptMastery
        lesson = session.lesson_progress.lesson  # 2026-02-18: Get lesson
        mastery, created = ConceptMastery.objects.get_or_create(
            student=session.student,
            lesson=lesson,
            day_number=session.day_number,
            defaults={
                'best_star_rating': star_rating,
                'attempts_count': 1,
                'is_mastered': is_passed,
            }
        )

        if not created:  # 2026-02-18: Update existing
            mastery.attempts_count += 1
            if star_rating > mastery.best_star_rating:  # 2026-02-18: New best
                mastery.best_star_rating = star_rating
            if is_passed:  # 2026-02-18: Mastered
                mastery.is_mastered = True
            mastery.save()

        # 2026-02-18: Update DayProgress
        day_progress = DayProgress.objects.filter(
            lesson_progress=session.lesson_progress,
            day_number=session.day_number
        ).first()

        if day_progress:  # 2026-02-18: Update mastery fields
            if star_rating > day_progress.mastery_star_rating:
                day_progress.mastery_star_rating = star_rating
            day_progress.mastery_passed = mastery.is_mastered

            # 2026-02-18: If mastered, advance to next day
            if mastery.is_mastered:
                day_progress.status = 'completed'
                day_progress.completed_at = timezone.now()
                day_progress.save()

                # 2026-02-18: Advance lesson progress
                progress = session.lesson_progress
                statuses = progress.day_statuses or {}
                statuses[str(session.day_number)] = 'completed'

                if session.day_number < 4:  # 2026-02-18: More days
                    progress.current_day = session.day_number + 1
                    statuses[str(session.day_number + 1)] = 'not_started'
                else:  # 2026-02-18: Day 4 done, unlock assessment
                    progress.current_day = 5
                    statuses['5'] = 'not_started'

                progress.day_statuses = statuses
                progress.save()
            else:
                day_progress.save()

        logger.info(  # 2026-02-18: Log
            f"Student {session.student.id} completed mastery practice "
            f"day {session.day_number}: {session.questions_correct}/"
            f"{session.questions_answered} ({percentage:.0f}%) - "
            f"{star_rating} stars {'PASSED' if is_passed else 'FAILED'}"
        )

        return {  # 2026-02-18: Final result
            'success': True,
            'session_id': str(session.id),
            'feedback': {
                'is_correct': last_is_correct,
                'correct_answer': last_correct_answer,
                'explanation': last_explanation,
            },
            'completed': True,
            'result': {
                'star_rating': star_rating,
                'percentage_correct': round(percentage, 1),
                'questions_correct': session.questions_correct,
                'questions_answered': session.questions_answered,
                'is_passed': is_passed,
                'attempt_number': session.attempt_number,
                'time_spent_seconds': session.time_spent_seconds,
            },
        }

    @classmethod
    def get_practice_status(cls, student, lesson_id):
        """
        2026-02-18: Get mastery practice status for all 4 days of a lesson.

        Args:
            student: Student model instance.
            lesson_id: TeachingLesson.lesson_id string.

        Returns:
            dict: Mastery status per day.
        """
        lesson = TeachingLesson.objects.filter(  # 2026-02-18: Lookup
            lesson_id=lesson_id, status='published'
        ).first()

        if not lesson:  # 2026-02-18: Not found
            return {
                'success': False,
                'error': 'Lesson not found.',
                'code': 'LESSON_NOT_FOUND',
            }

        days_status = []  # 2026-02-18: Build per-day status
        for day in range(1, 5):  # 2026-02-18: Days 1-4
            mastery = ConceptMastery.objects.filter(
                student=student, lesson=lesson, day_number=day
            ).first()

            if mastery:  # 2026-02-18: Has mastery record
                days_status.append({
                    'day_number': day,
                    'best_star_rating': mastery.best_star_rating,
                    'attempts_count': mastery.attempts_count,
                    'is_mastered': mastery.is_mastered,
                })
            else:  # 2026-02-18: No attempts
                days_status.append({
                    'day_number': day,
                    'best_star_rating': 0,
                    'attempts_count': 0,
                    'is_mastered': False,
                })

        return {  # 2026-02-18: Return
            'success': True,
            'lesson_id': lesson_id,
            'days': days_status,
        }

    @staticmethod
    def _sanitize_question(question, difficulty):
        """
        2026-02-18: Remove correct answer from question for client.

        Args:
            question: Full question dict from practice bank.
            difficulty: Difficulty level of the question.

        Returns:
            dict: Client-safe question without correct_answer.
        """
        sanitized = {  # 2026-02-18: Copy safe fields
            'id': question.get('id'),
            'type': question.get('type', 'mcq'),
            'question': question.get('question'),
            'difficulty': difficulty,
        }

        # 2026-02-18: Type-specific fields
        q_type = question.get('type', 'mcq')
        if q_type in ('mcq',):  # 2026-02-18: MCQ options
            sanitized['options'] = question.get('options', [])
        elif q_type == 'true_false':  # 2026-02-18: No extra fields needed
            sanitized['options'] = ['True', 'False']
        elif q_type == 'drag_order':  # 2026-02-18: Items to order
            sanitized['items'] = question.get('items', [])
        # 2026-02-18: numeric_fill needs no extra fields

        if question.get('hint'):  # 2026-02-18: Include hint if present
            sanitized['hint'] = question['hint']

        return sanitized

    @staticmethod
    def _find_question(questions_bank, question_id):
        """
        2026-02-18: Find a question by ID across all difficulty levels.

        Args:
            questions_bank: dict with 'easy', 'medium', 'hard' lists.
            question_id: Question ID to find.

        Returns:
            dict or None: The question dict, or None if not found.
        """
        for difficulty in ('easy', 'medium', 'hard'):  # 2026-02-18: Search all
            for q in questions_bank.get(difficulty, []):  # 2026-02-18: Iterate
                if q.get('id') == question_id:  # 2026-02-18: Match
                    return q
        return None  # 2026-02-18: Not found

    @staticmethod
    def _get_question_difficulty(questions_bank, question_id):
        """
        2026-02-18: Get the difficulty level of a question by ID.

        Args:
            questions_bank: dict with 'easy', 'medium', 'hard' lists.
            question_id: Question ID to find.

        Returns:
            str: Difficulty level, or 'medium' as default.
        """
        for difficulty in ('easy', 'medium', 'hard'):  # 2026-02-18: Search all
            for q in questions_bank.get(difficulty, []):  # 2026-02-18: Iterate
                if q.get('id') == question_id:  # 2026-02-18: Match
                    return difficulty
        return 'medium'  # 2026-02-18: Default
