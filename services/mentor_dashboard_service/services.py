"""
2026-03-06: Mentor Dashboard business logic (BS-MNT).

Purpose:
    Service layer for mentor-facing operations: student grid with color-coded
    performance, comprehension review queue, AI weekly summaries, and parent
    message drafting.
"""

import logging  # 2026-03-06: Logging
from datetime import date, timedelta  # 2026-03-06: Date arithmetic

from django.db.models import Avg  # 2026-03-06: Aggregation
from django.utils import timezone  # 2026-03-06: Timezone-aware now()

from services.auth_service.models import Student  # 2026-03-06: Student model
from services.comprehension_service.models import ComprehensionQuestionResponse  # 2026-03-06: Review targets
from services.communication_service.models import MessageThread  # 2026-03-06: Parent messages
from services.llm_service.factory import get_llm_provider  # 2026-03-06: LLM abstraction
from services.teaching_engine.models import DayProgress, StudentLessonProgress  # 2026-03-06: Progress models

from .models import ComprehensionReview, MentorAssignment, WeeklySummary  # 2026-03-06: Our models

logger = logging.getLogger(__name__)  # 2026-03-06: Module logger


def _get_monday(for_date=None):
    """
    2026-03-06: Return the Monday of the week containing for_date (default today).

    Args:
        for_date: Optional date object. Defaults to today.

    Returns:
        date: Monday of that week.
    """
    d = for_date or date.today()  # 2026-03-06: Default to today
    return d - timedelta(days=d.weekday())  # 2026-03-06: weekday() 0=Monday


def _safe_last_active(student):
    """
    2026-03-06: Return the date of the student's most recent day progress, or None.

    Args:
        student: Student instance.

    Returns:
        date | None: Date of latest DayProgress update, or None if none.
    """
    try:
        latest = (
            DayProgress.objects.filter(
                lesson_progress__student=student
            )
            .order_by('-lesson_progress__updated_at')
            .select_related('lesson_progress')
            .first()
        )
        if latest:
            return latest.lesson_progress.updated_at.date()  # 2026-03-06: Date portion
    except Exception as exc:  # 2026-03-06: Defensive — don't break the dashboard
        logger.warning("_safe_last_active error for student %s: %s", student.id, exc)
    return None  # 2026-03-06: No activity found


def _safe_streak(student):
    """
    2026-03-06: Return current streak_days for a student; 0 if no learning profile.

    Args:
        student: Student instance.

    Returns:
        int: Current streak.
    """
    try:
        return student.user.learning_profile.current_streak_days  # 2026-03-06: From learning_engine
    except Exception:
        return 0  # 2026-03-06: No profile yet


def _compute_color(avg_stars, last_active):
    """
    2026-03-06: Determine color-coded performance status.

    Rules:
        GREEN: avg_stars ≥ 3.5 AND last_active ≤ 2 days ago
        AMBER: avg_stars 2-3.5 OR last_active 3-7 days ago
        RED:   avg_stars < 2 OR last_active > 7 days ago
        GREY:  no activity (last_active is None)

    Args:
        avg_stars: float or None
        last_active: date or None

    Returns:
        str: 'green' | 'amber' | 'red' | 'grey'
    """
    if last_active is None:  # 2026-03-06: No activity
        return 'grey'

    days_since = (date.today() - last_active).days  # 2026-03-06: Days since last active

    if days_since > 7 or (avg_stars is not None and avg_stars < 2):  # 2026-03-06: Critical
        return 'red'

    if days_since >= 3 or (avg_stars is not None and avg_stars < 3.5):  # 2026-03-06: Attention
        return 'amber'

    return 'green'  # 2026-03-06: On-track


class MentorDashboardService:
    """
    2026-03-06: Business logic for all mentor dashboard operations.

    All methods accept a mentor_user (Django User with is_staff=True) as
    the first argument to enforce access scoping.
    """

    # ------------------------------------------------------------------
    # Student grid
    # ------------------------------------------------------------------

    @staticmethod
    def get_assigned_students(mentor_user):
        """
        2026-03-06: Return active Student objects assigned to this mentor.

        Args:
            mentor_user: Django User (is_staff=True).

        Returns:
            QuerySet[Student]: Assigned active students.
        """
        return Student.objects.filter(  # 2026-03-06: Only active assignments
            mentor_assignments__mentor=mentor_user,
            mentor_assignments__is_active=True,
        ).distinct()

    @staticmethod
    def get_student_grid(mentor_user):
        """
        2026-03-06: Return color-coded performance grid for all assigned students.

        Each dict contains:
            student_id, student_name, grade, color, avg_stars,
            mastered_concepts, streak_days, last_active (ISO date or None),
            pending_reviews (count of un-reviewed low-score responses).

        Args:
            mentor_user: Django User (is_staff=True).

        Returns:
            list[dict]: One entry per assigned student.
        """
        students = MentorDashboardService.get_assigned_students(mentor_user)
        result = []

        for student in students:
            # 2026-03-06: Compute average star rating from all DayProgress records
            agg = DayProgress.objects.filter(
                lesson_progress__student=student
            ).aggregate(avg=Avg('mastery_star_rating'))
            avg_stars = agg['avg']  # 2026-03-06: None if no records

            last_active = _safe_last_active(student)  # 2026-03-06: Most recent activity date

            # 2026-03-06: Count mastered concepts
            try:
                from services.teaching_engine.models import ConceptMastery  # 2026-03-06: Lazy import
                mastered = ConceptMastery.objects.filter(
                    student=student, is_mastered=True
                ).count()
            except Exception:
                mastered = 0  # 2026-03-06: Model may not exist in all envs

            # 2026-03-06: Pending review count (low-scoring or LLM-error responses not yet reviewed)
            reviewed_ids = ComprehensionReview.objects.filter(
                reviewed_by=mentor_user,
                response__student=student,
            ).values_list('response_id', flat=True)

            pending_reviews = ComprehensionQuestionResponse.objects.filter(
                student=student,
            ).exclude(
                id__in=reviewed_ids,
            ).filter(
                models.Q(marks_awarded__lt=models.F('marks_available')) |
                models.Q(llm_error=True)
            ).count()

            result.append({
                'student_id': str(student.id),
                'student_name': student.full_name,
                'grade': student.grade,
                'color': _compute_color(avg_stars, last_active),
                'avg_stars': round(avg_stars, 2) if avg_stars is not None else None,
                'mastered_concepts': mastered,
                'streak_days': _safe_streak(student),
                'last_active': last_active.isoformat() if last_active else None,
                'pending_reviews': pending_reviews,
            })

        return result  # 2026-03-06: Full grid

    @staticmethod
    def get_student_detail(mentor_user, student_id):
        """
        2026-03-06: Return full lesson/day breakdown for one assigned student.

        Args:
            mentor_user: Django User (is_staff=True).
            student_id: UUID string.

        Returns:
            dict | None: Detail data or None if not assigned.
        """
        student = MentorDashboardService.get_assigned_students(mentor_user).filter(
            id=student_id
        ).first()

        if not student:  # 2026-03-06: Not assigned or not found
            return None

        # 2026-03-06: Gather all lesson progress records
        lessons = StudentLessonProgress.objects.filter(student=student).select_related('lesson')
        lesson_data = []

        for lp in lessons:
            days = list(
                DayProgress.objects.filter(lesson_progress=lp).order_by('day_number').values(
                    'day_number', 'status', 'mastery_star_rating', 'mastery_passed',
                    'comprehension_score', 'practice_score', 'read_along_score',
                )
            )
            lesson_data.append({
                'lesson_id': lp.lesson.lesson_id,
                'lesson_title': lp.lesson.title,
                'subject': lp.lesson.subject,
                'iq_level': lp.iq_level,
                'status': lp.status,
                'current_day': lp.current_day,
                'days': days,
            })

        # 2026-03-06: Spaced repetition queue size
        sr_queue = 0
        try:
            from services.spaced_repetition_service.models import SpacedRepetitionRecord  # 2026-03-06: Lazy
            sr_queue = SpacedRepetitionRecord.objects.filter(
                student=student
            ).exclude(box=5).count()
        except Exception:
            pass  # 2026-03-06: Service may not be available

        return {
            'student_id': str(student.id),
            'student_name': student.full_name,
            'grade': student.grade,
            'streak_days': _safe_streak(student),
            'lessons': lesson_data,
            'spaced_repetition_queue': sr_queue,
        }

    # ------------------------------------------------------------------
    # Comprehension review queue
    # ------------------------------------------------------------------

    @staticmethod
    def get_review_queue(mentor_user, reviewed=False):
        """
        2026-03-06: Return comprehension responses needing mentor spot-check.

        Filters to assigned students. Returns partial-credit and LLM-error
        responses. If reviewed=True, returns already-reviewed responses instead.

        Args:
            mentor_user: Django User (is_staff=True).
            reviewed: bool — if True, return already-reviewed; else un-reviewed.

        Returns:
            list[dict]: Queue items with question/response/score data.
        """
        assigned_students = MentorDashboardService.get_assigned_students(mentor_user)

        reviewed_ids = ComprehensionReview.objects.filter(
            reviewed_by=mentor_user
        ).values_list('response_id', flat=True)

        qs = ComprehensionQuestionResponse.objects.filter(
            student__in=assigned_students,
        ).select_related('student', 'lesson')

        if reviewed:  # 2026-03-06: Show already-reviewed items
            qs = qs.filter(id__in=reviewed_ids)
        else:  # 2026-03-06: Show un-reviewed items needing attention
            qs = qs.exclude(id__in=reviewed_ids).filter(
                models.Q(marks_awarded__lt=models.F('marks_available')) |
                models.Q(llm_error=True)
            )

        result = []
        for resp in qs:
            result.append({
                'id': str(resp.id),
                'student_name': resp.student.full_name,
                'lesson_title': resp.lesson.title,
                'day_number': resp.day_number,
                'question_text': resp.question_text,
                'marks_available': resp.marks_available,
                'marks_awarded': resp.marks_awarded,
                'student_text': resp.student_text,
                'llm_feedback': resp.llm_feedback,
                'llm_error': resp.llm_error,
                'reviewed': str(resp.id) in [str(r) for r in reviewed_ids],
            })

        return result  # 2026-03-06: Queue items

    @staticmethod
    def submit_review(mentor_user, response_id, score, notes=''):
        """
        2026-03-06: Create or update a ComprehensionReview for a response.

        Validates that the response belongs to an assigned student before saving.

        Args:
            mentor_user: Django User (is_staff=True).
            response_id: UUID of the ComprehensionQuestionResponse.
            score: int 0-5 mentor quality score.
            notes: str optional notes.

        Returns:
            ComprehensionReview | None: Created/updated review, or None if not authorized.
        """
        assigned_students = MentorDashboardService.get_assigned_students(mentor_user)

        response = ComprehensionQuestionResponse.objects.filter(
            id=response_id,
            student__in=assigned_students,
        ).first()

        if not response:  # 2026-03-06: Not found or not assigned
            return None

        review, _ = ComprehensionReview.objects.update_or_create(
            response=response,
            reviewed_by=mentor_user,
            defaults={
                'mentor_score': score,
                'mentor_notes': notes,
            },
        )
        return review  # 2026-03-06: Saved review

    # ------------------------------------------------------------------
    # AI weekly summary
    # ------------------------------------------------------------------

    @staticmethod
    def get_or_generate_weekly_summary(mentor_user, student_id):
        """
        2026-03-06: Return existing summary for current week, or generate a new one.

        Args:
            mentor_user: Django User (is_staff=True).
            student_id: UUID string.

        Returns:
            WeeklySummary | None: Summary instance or None if student not assigned.
        """
        student = MentorDashboardService.get_assigned_students(mentor_user).filter(
            id=student_id
        ).first()

        if not student:  # 2026-03-06: Not assigned
            return None

        week_start = _get_monday()  # 2026-03-06: This week's Monday

        existing = WeeklySummary.objects.filter(
            student=student, week_start=week_start
        ).first()

        if existing:  # 2026-03-06: Already generated this week
            return existing

        return MentorDashboardService._generate_summary(mentor_user, student, week_start)

    @staticmethod
    def generate_fresh_summary(mentor_user, student_id):
        """
        2026-03-06: Force-regenerate the weekly summary for the current week.

        Deletes the existing summary if present, then generates a new one.

        Args:
            mentor_user: Django User (is_staff=True).
            student_id: UUID string.

        Returns:
            WeeklySummary | None: New summary or None if not assigned.
        """
        student = MentorDashboardService.get_assigned_students(mentor_user).filter(
            id=student_id
        ).first()

        if not student:  # 2026-03-06: Not assigned
            return None

        week_start = _get_monday()  # 2026-03-06: This week

        # 2026-03-06: Delete existing to allow regeneration
        WeeklySummary.objects.filter(student=student, week_start=week_start).delete()

        return MentorDashboardService._generate_summary(mentor_user, student, week_start)

    @staticmethod
    def _generate_summary(mentor_user, student, week_start):
        """
        2026-03-06: Internal — build performance data and call LLM for summary.

        Args:
            mentor_user: Django User (is_staff=True).
            student: Student instance.
            week_start: date — Monday of the week to summarise.

        Returns:
            WeeklySummary: Persisted summary instance.
        """
        week_end = week_start + timedelta(days=6)  # 2026-03-06: Sunday

        # 2026-03-06: Gather this week's day progress records
        day_progresses = DayProgress.objects.filter(
            lesson_progress__student=student,
            lesson_progress__updated_at__date__range=(week_start, week_end),
        ).select_related('lesson_progress__lesson')

        lessons_completed = day_progresses.filter(
            status__in=['day_complete', 'completed']
        ).count()

        agg = day_progresses.aggregate(avg=Avg('mastery_star_rating'))
        avg_stars = agg['avg'] or 0.0  # 2026-03-06: Default to 0.0 if none

        comp_scores = list(
            day_progresses.values_list('comprehension_score', flat=True)
        )
        prac_scores = list(
            day_progresses.values_list('practice_score', flat=True)
        )

        # 2026-03-06: Build LLM prompt
        prompt = (
            f"Student: {student.full_name}, Grade: {student.grade}, "
            f"Week of: {week_start.isoformat()}\n"
            f"Lessons completed: {lessons_completed}, "
            f"Avg stars: {avg_stars:.1f}\n"
            f"Comprehension scores: {comp_scores}\n"
            f"Practice scores: {prac_scores}\n\n"
            "Write 3 short paragraphs: overall summary, strengths (2-3 points), "
            "areas for improvement (2-3 points). "
            "Keep it warm, encouraging, and factual. Max 200 words."
        )
        system_prompt = (
            "You are an educational mentor writing a concise weekly progress "
            "report for a parent."
        )

        summary_text = ''  # 2026-03-06: Default if LLM fails
        strengths = []  # 2026-03-06: Default empty
        areas = []  # 2026-03-06: Default empty

        try:
            llm = get_llm_provider()  # 2026-03-06: Factory — provider from settings
            response = llm.chat(message=prompt, system_prompt=system_prompt)
            summary_text = response.text  # 2026-03-06: Full narrative
        except Exception as exc:  # 2026-03-06: Graceful fallback
            logger.warning("LLM summary generation failed for %s: %s", student.id, exc)
            summary_text = (
                f"{student.full_name} completed {lessons_completed} lessons this week "
                f"with an average of {avg_stars:.1f} stars."
            )

        # 2026-03-06: Persist and return
        return WeeklySummary.objects.create(
            student=student,
            week_start=week_start,
            summary_text=summary_text,
            strengths=strengths,
            areas_for_improvement=areas,
            lessons_completed=lessons_completed,
            avg_star_rating=round(avg_stars, 2),
            generated_by=mentor_user,
        )

    # ------------------------------------------------------------------
    # Parent message drafting
    # ------------------------------------------------------------------

    @staticmethod
    def draft_parent_message(mentor_user, student_id, context_hint=''):
        """
        2026-03-06: Generate a draft message to the student's parent via LLM.

        Args:
            mentor_user: Django User (is_staff=True).
            student_id: UUID string.
            context_hint: Optional hint about focus (e.g. "concern about attendance").

        Returns:
            str | None: Draft message text, or None if student not assigned.
        """
        student = MentorDashboardService.get_assigned_students(mentor_user).filter(
            id=student_id
        ).first()

        if not student:  # 2026-03-06: Not assigned
            return None

        # 2026-03-06: Get latest weekly summary for context
        summary = WeeklySummary.objects.filter(student=student).first()
        perf_context = ''
        if summary:
            perf_context = (
                f"This week: {summary.lessons_completed} lessons completed, "
                f"avg {summary.avg_star_rating:.1f} stars."
            )

        prompt = (
            f"Draft a brief, warm parent message about {student.full_name} "
            f"(Grade {student.grade}). {perf_context} "
            f"Additional context: {context_hint or 'general weekly check-in'}. "
            "Keep the tone professional but friendly. Max 100 words."
        )
        system_prompt = "You are a school mentor messaging a parent about their child's progress."

        try:
            llm = get_llm_provider()  # 2026-03-06: LLM factory
            response = llm.chat(message=prompt, system_prompt=system_prompt)
            return response.text  # 2026-03-06: Draft text
        except Exception as exc:  # 2026-03-06: Graceful fallback
            logger.warning("LLM draft_message failed for %s: %s", student.id, exc)
            return (
                f"Dear Parent, I wanted to share a quick update about "
                f"{student.full_name}'s progress this week. {perf_context} "
                "Please feel free to reach out with any questions."
            )

    # ------------------------------------------------------------------
    # Parent message threads
    # ------------------------------------------------------------------

    @staticmethod
    def get_message_threads(mentor_user):
        """
        2026-03-06: Return all MessageThread records where this mentor is the monitor.

        Delegates to communication_service MessageThread filtering.

        Args:
            mentor_user: Django User (is_staff=True).

        Returns:
            QuerySet[MessageThread]: Active threads for this mentor.
        """
        return MessageThread.objects.filter(monitor=mentor_user).select_related(
            'student', 'parent'
        )


# 2026-03-06: Import models here to avoid circular import (models uses services constants)
from django.db import models  # noqa: E402  2026-03-06: Needed for Q/F in get_student_grid
