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
)
from .content_loader import TeachingContentLoader  # 2026-02-17: Content loader

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

        # 2026-02-17: Update DayProgress
        day_progress.status = 'completed'  # 2026-02-17: Mark done
        day_progress.practice_score = score  # 2026-02-17: Set score
        day_progress.questions_attempted = len(practice_answers)  # 2026-02-17: Attempted
        day_progress.questions_correct = correct_count  # 2026-02-17: Correct
        day_progress.time_spent_seconds = time_spent  # 2026-02-17: Time
        day_progress.completed_at = timezone.now()  # 2026-02-17: Completion time
        day_progress.revision_completed = True  # 2026-02-17: Revision done (implicit)
        day_progress.save()  # 2026-02-17: Persist

        # 2026-02-17: Update lesson progress
        progress.total_score += score  # 2026-02-17: Cumulative score
        statuses = progress.day_statuses or {}  # 2026-02-17: Day statuses
        statuses[str(day_number)] = 'completed'  # 2026-02-17: Mark day done

        # 2026-02-17: Advance to next day
        if day_number < 4:  # 2026-02-17: More days
            progress.current_day = day_number + 1  # 2026-02-17: Next day
            statuses[str(day_number + 1)] = 'not_started'  # 2026-02-17: Unlock next
        else:  # 2026-02-17: Day 4 done, unlock assessment
            progress.current_day = 5  # 2026-02-17: Assessment day
            statuses['5'] = 'not_started'  # 2026-02-17: Unlock assessment

        progress.day_statuses = statuses  # 2026-02-17: Update
        progress.save()  # 2026-02-17: Persist

        logger.info(  # 2026-02-17: Log
            f"Student {student.id} completed {lesson_id} day {day_number}: "
            f"{correct_count}/{total_count} ({score}%)"
        )

        return {  # 2026-02-17: Return result
            'success': True,
            'lesson_id': lesson_id,
            'day_number': day_number,
            'score': score,
            'questions_correct': correct_count,
            'questions_total': total_count,
            'next_day': day_number + 1 if day_number < 4 else 5,
            'assessment_unlocked': day_number == 4,
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
