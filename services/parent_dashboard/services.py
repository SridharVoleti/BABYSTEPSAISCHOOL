"""
2026-02-19: Parent Dashboard business logic.

Purpose:
    Service layer for aggregating child learning data for parent view.
    Reads from auth_service, teaching_engine, and learning_engine models.
"""

from datetime import date, timedelta  # 2026-02-19: Date arithmetic

from django.db.models import Sum  # 2026-02-19: Aggregation
from django.utils import timezone  # 2026-02-19: Timezone-aware now()

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import (  # 2026-02-19: Teaching models
    ConceptMastery, TutoringSession,
)
from .models import ParentalControls  # 2026-02-19: Our model


def _get_monday(today):
    """
    2026-02-19: Return the Monday date of the current week.

    Args:
        today: A date object.

    Returns:
        date: Monday of the same week.
    """
    return today - timedelta(days=today.weekday())  # 2026-02-19: Monday = weekday 0


def _safe_streak(student):
    """
    2026-02-19: Return streak_days for a student; 0 if no learning profile.

    Args:
        student: Student model instance.

    Returns:
        int: Current streak days.
    """
    if not student.user:  # 2026-02-19: No linked Django user
        return 0
    try:
        return student.user.learning_profile.current_streak_days  # 2026-02-19: Profile exists
    except Exception:  # 2026-02-19: No learning profile
        return 0


def _safe_active_minutes(student, today):
    """
    2026-02-19: Return today_active_minutes for a student; 0 if no record.

    Args:
        student: Student model instance.
        today: Date object for today.

    Returns:
        int: Minutes spent learning today.
    """
    if not student.user:  # 2026-02-19: No linked Django user
        return 0
    try:
        activity = student.user.daily_activities.filter(
            activity_date=today
        ).first()  # 2026-02-19: Today's record
        return activity.time_spent_minutes if activity else 0
    except Exception:  # 2026-02-19: No activity record
        return 0


def _build_concept_name(cm):
    """
    2026-02-19: Build human-readable concept name from ConceptMastery.

    Format: '{subject} Week {week_number} Day {day_number}'

    Args:
        cm: ConceptMastery instance.

    Returns:
        str: Human-readable concept name.
    """
    try:
        lesson = cm.lesson  # 2026-02-19: Related TeachingLesson
        return f"{lesson.subject} Week {lesson.week_number} Day {cm.day_number}"
    except Exception:  # 2026-02-19: Fallback
        return f"Day {cm.day_number}"


class ParentDashboardService:
    """
    2026-02-19: Aggregates learning data for parent dashboard.

    All methods verify parent ownership before returning data.
    """

    @staticmethod
    def get_dashboard(parent):
        """
        2026-02-19: Return overview data for all active children.

        Args:
            parent: Parent model instance.

        Returns:
            dict: {'children': [ChildProgressDict, ...]}
        """
        today = timezone.now().date()  # 2026-02-19: Current date
        monday = _get_monday(today)  # 2026-02-19: Week start

        children = []
        for student in parent.students.filter(is_active=True):  # 2026-02-19: Active only
            # 2026-02-19: Streak from learning profile
            streak_days = _safe_streak(student)

            # 2026-02-19: Total stars across all concept mastery records
            total_stars = (
                ConceptMastery.objects.filter(student=student)
                .aggregate(total=Sum('best_star_rating'))['total'] or 0
            )

            # 2026-02-19: Minutes active today
            today_active_minutes = _safe_active_minutes(student, today)

            # 2026-02-19: Concepts mastered today (is_mastered=True, updated today)
            today_mastered_qs = ConceptMastery.objects.filter(
                student=student,
                is_mastered=True,
                updated_at__date=today,
            ).select_related('lesson')  # 2026-02-19: Prefetch lesson

            today_mastered = [
                {
                    'concept_name': _build_concept_name(cm),
                    'stars': cm.best_star_rating,
                }
                for cm in today_mastered_qs
            ]

            # 2026-02-19: Stars earned this week
            week_stars = (
                ConceptMastery.objects.filter(
                    student=student,
                    updated_at__date__gte=monday,
                )
                .aggregate(total=Sum('best_star_rating'))['total'] or 0
            )

            # 2026-02-19: Concepts mastered this week
            week_concepts = ConceptMastery.objects.filter(
                student=student,
                is_mastered=True,
                updated_at__date__gte=monday,
            ).count()

            # 2026-02-19: Alerts: < 3 stars AND >= 2 attempts (struggling)
            alert_qs = ConceptMastery.objects.filter(
                student=student,
                best_star_rating__lt=3,
                attempts_count__gte=2,
            ).select_related('lesson')

            alerts = [
                {
                    'type': 'low_stars',
                    'concept_name': _build_concept_name(cm),
                    'stars': cm.best_star_rating,
                    'attempts': cm.attempts_count,
                }
                for cm in alert_qs
            ]

            children.append({
                'student_id': str(student.id),
                'display_name': student.full_name,
                'grade': student.grade,
                'streak_days': streak_days,
                'total_stars': total_stars,
                'today_active_minutes': today_active_minutes,
                'today_mastered': today_mastered,
                'week_stars': week_stars,
                'week_concepts': week_concepts,
                'alerts': alerts,
            })

        return {'children': children}

    @staticmethod
    def get_progress_detail(parent, student_id):
        """
        2026-02-19: Return drill-down progress grouped by subject → lesson → day.

        Args:
            parent: Parent model instance.
            student_id: UUID of the student.

        Returns:
            dict: {'student_id', 'display_name', 'subjects': {...}}
            or None if student not owned by parent.
        """
        student = (  # 2026-02-19: Ownership check
            parent.students.filter(id=student_id, is_active=True).first()
        )
        if not student:
            return None

        # 2026-02-19: Fetch all mastery records with lesson prefetched
        masteries = ConceptMastery.objects.filter(
            student=student
        ).select_related('lesson').order_by('lesson__subject', 'lesson__week_number', 'day_number')

        # 2026-02-19: Group by subject → lesson title → days
        subjects = {}
        for cm in masteries:
            lesson = cm.lesson
            subject = lesson.subject  # 2026-02-19: e.g. 'English'
            lesson_key = lesson.lesson_id  # 2026-02-19: Unique lesson ID

            if subject not in subjects:
                subjects[subject] = {}

            if lesson_key not in subjects[subject]:
                subjects[subject][lesson_key] = {
                    'lesson_id': lesson.lesson_id,
                    'title': lesson.title,
                    'week_number': lesson.week_number,
                    'days': [],
                }

            subjects[subject][lesson_key]['days'].append({
                'day_number': cm.day_number,
                'best_star_rating': cm.best_star_rating,
                'is_mastered': cm.is_mastered,
                'attempts_count': cm.attempts_count,
            })

        # 2026-02-19: Convert to list-based structure
        subjects_list = {}
        for subject, lessons_dict in subjects.items():
            subjects_list[subject] = list(lessons_dict.values())

        return {
            'student_id': str(student.id),
            'display_name': student.full_name,
            'grade': student.grade,
            'subjects': subjects_list,
        }

    @staticmethod
    def get_parental_controls(parent, student_id):
        """
        2026-02-19: Get parental controls for a student, creating defaults if needed.

        Args:
            parent: Parent model instance.
            student_id: UUID of the student.

        Returns:
            ParentalControls instance or None if student not owned.
        """
        student = (  # 2026-02-19: Ownership check
            parent.students.filter(id=student_id, is_active=True).first()
        )
        if not student:
            return None

        controls, _ = ParentalControls.objects.get_or_create(  # 2026-02-19: Auto-create
            student=student
        )
        return controls

    @staticmethod
    def update_parental_controls(parent, student_id, data):
        """
        2026-02-19: Update parental controls settings.

        Args:
            parent: Parent model instance.
            student_id: UUID of the student.
            data: dict of fields to update.

        Returns:
            ParentalControls instance or None if student not owned.
        """
        student = (  # 2026-02-19: Ownership check
            parent.students.filter(id=student_id, is_active=True).first()
        )
        if not student:
            return None

        controls, _ = ParentalControls.objects.get_or_create(  # 2026-02-19: Get or create
            student=student
        )

        # 2026-02-19: Update only provided fields
        allowed_fields = {
            'daily_time_limit_minutes', 'schedule_enabled',
            'schedule_start_time', 'schedule_end_time', 'ai_log_enabled',
        }
        for field, value in data.items():
            if field in allowed_fields:  # 2026-02-19: Whitelist
                setattr(controls, field, value)

        controls.save()  # 2026-02-19: Persist
        return controls

    @staticmethod
    def get_conversation_log(parent, student_id):
        """
        2026-02-19: Return all AI tutoring messages for a student.

        Parents can always see the conversation log regardless of
        ai_log_enabled (that setting is for in-app visibility).

        Args:
            parent: Parent model instance.
            student_id: UUID of the student.

        Returns:
            dict: {'student_id', 'sessions': [...]} or None if not owned.
        """
        student = (  # 2026-02-19: Ownership check
            parent.students.filter(id=student_id, is_active=True).first()
        )
        if not student:
            return None

        sessions = TutoringSession.objects.filter(  # 2026-02-19: All sessions
            student=student
        ).order_by('created_at').select_related('lesson_progress__lesson')

        session_list = []
        for session in sessions:
            lesson_id = None
            day_number = session.day_number
            if session.lesson_progress:  # 2026-02-19: Lesson context
                lesson_id = session.lesson_progress.lesson.lesson_id

            session_list.append({
                'session_id': str(session.id),
                'lesson_id': lesson_id,
                'day_number': day_number,
                'messages': session.messages or [],
                'created_at': session.created_at.isoformat(),
            })

        return {
            'student_id': str(student.id),
            'display_name': student.full_name,
            'sessions': session_list,
        }
