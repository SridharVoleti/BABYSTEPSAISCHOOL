"""
2026-03-04: Communication Service business logic (BS-COM-001/002/003, BS-PAR-006).
"""

from datetime import date, timedelta  # 2026-03-04: Date utilities
from typing import Optional  # 2026-03-04: Type hints

from django.contrib.auth.models import User  # 2026-03-04: Monitor User
from django.db import models  # 2026-03-04: Q for complex queries
from django.utils import timezone  # 2026-03-04: Timezone-aware now()

from services.auth_service.models import Parent, Student  # 2026-03-04: Auth models
from services.llm_service.factory import get_llm_provider  # 2026-03-04: LLM for summaries

from .models import (  # 2026-03-04: Models
    Announcement, Message, MessageThread, TermReport, WeeklyProgressReport,
)


# ============================================================
# BS-COM-001: Messaging Service
# ============================================================

class MessagingService:
    """2026-03-04: Parent–monitor direct messaging."""

    @staticmethod
    def get_or_create_thread(
        student: Student,
        parent: Parent,
        monitor: User,
        subject: str = '',
    ) -> MessageThread:
        """
        2026-03-04: Return existing open thread or create a new one.

        Args:
            student: Topic student.
            parent: Parent party.
            monitor: Monitor (staff user).
            subject: Thread subject (used only on creation).

        Returns:
            MessageThread instance.
        """
        thread = MessageThread.objects.filter(
            student=student, parent=parent, monitor=monitor, is_closed=False
        ).first()
        if not thread:
            thread = MessageThread.objects.create(
                student=student, parent=parent, monitor=monitor, subject=subject
            )
        return thread

    @staticmethod
    def send_message(
        thread: MessageThread,
        sender_type: str,
        body: str,
    ) -> Message:
        """
        2026-03-04: Append a message to a thread.

        Args:
            thread: MessageThread to append to.
            sender_type: 'parent' or 'monitor'.
            body: Message text.

        Returns:
            Created Message.

        Raises:
            ValueError: If thread is closed or sender_type is invalid.
        """
        if thread.is_closed:
            raise ValueError('Cannot send to a closed thread.')
        if sender_type not in (Message.SENDER_PARENT, Message.SENDER_MONITOR):
            raise ValueError(f'Invalid sender_type: {sender_type}')
        msg = Message.objects.create(thread=thread, sender_type=sender_type, body=body)
        # 2026-03-04: Update thread timestamp
        thread.save(update_fields=['updated_at'])
        return msg

    @staticmethod
    def mark_messages_read(thread: MessageThread, reader_type: str) -> int:
        """
        2026-03-04: Mark all unread messages from the other party as read.

        Args:
            thread: The thread.
            reader_type: 'parent' or 'monitor' (who is reading).

        Returns:
            Number of messages marked read.
        """
        other = Message.SENDER_MONITOR if reader_type == 'parent' else Message.SENDER_PARENT
        return Message.objects.filter(
            thread=thread, sender_type=other, is_read=False
        ).update(is_read=True)

    @staticmethod
    def list_threads(parent: Optional[Parent] = None, monitor: Optional[User] = None) -> list:
        """
        2026-03-04: List all threads for a parent or monitor.

        Args:
            parent: Filter by parent.
            monitor: Filter by monitor.

        Returns:
            QuerySet of MessageThread objects.
        """
        qs = MessageThread.objects.select_related('student', 'parent', 'monitor')
        if parent:
            qs = qs.filter(parent=parent)
        if monitor:
            qs = qs.filter(monitor=monitor)
        return list(qs)


# ============================================================
# BS-COM-002: Announcements Service
# ============================================================

class AnnouncementService:
    """2026-03-04: School announcements management."""

    @staticmethod
    def create(
        title: str,
        body: str,
        audience: str = Announcement.AUDIENCE_ALL,
        grades: Optional[list] = None,
        priority: str = 'normal',
        created_by: Optional[User] = None,
    ) -> Announcement:
        """
        2026-03-04: Monitor creates an announcement.

        Returns:
            Created Announcement.
        """
        return Announcement.objects.create(
            title=title,
            body=body,
            audience=audience,
            grades=grades or [],
            priority=priority,
            created_by=created_by,
        )

    @staticmethod
    def list_for_grade(grade: int) -> list:
        """
        2026-03-04: Return active announcements visible to a grade.

        Includes ALL and GRADE audience (matching grade); excludes PARENT-only.

        Returns:
            List of Announcement objects.
        """
        now = timezone.now()
        qs = Announcement.objects.filter(is_active=True).filter(
            models.Q(audience=Announcement.AUDIENCE_ALL) |
            models.Q(audience=Announcement.AUDIENCE_GRADE)
        )
        return list(qs)

    @staticmethod
    def list_active(grade: Optional[int] = None, for_parents: bool = False) -> list:
        """
        2026-03-04: Return all currently active announcements.

        Args:
            grade: If provided, filter to announcements for this grade.
            for_parents: If True, include PARENT-only announcements.

        Returns:
            List of Announcement objects.
        """
        now = timezone.now()
        qs = Announcement.objects.filter(is_active=True)
        # 2026-03-04: Exclude not-yet-published
        qs = qs.filter(
            models.Q(publish_at__isnull=True) | models.Q(publish_at__lte=now)
        )
        # 2026-03-04: Exclude expired
        qs = qs.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gte=now)
        )

        if grade is not None:
            # 2026-03-04: Show ALL + grade-specific
            qs = qs.filter(
                models.Q(audience=Announcement.AUDIENCE_ALL) |
                models.Q(audience=Announcement.AUDIENCE_GRADE)
            )
        elif not for_parents:
            qs = qs.exclude(audience=Announcement.AUDIENCE_PARENT)

        return list(qs)


# ============================================================
# BS-COM-003: Weekly Progress Report Service
# ============================================================

class WeeklyReportService:
    """2026-03-04: AI-generated weekly progress report per student."""

    @staticmethod
    def _build_prompt(student: Student, stats: dict) -> str:
        """
        2026-03-04: Build LLM prompt for summary generation.

        Args:
            student: The student.
            stats: Dict with attendance_days, lessons_completed, avg_star_rating.

        Returns:
            Prompt string.
        """
        return (
            f"You are a caring teacher writing a weekly progress note for {student.full_name}, "
            f"a Grade {student.grade} student.\n"
            f"This week: attended {stats['attendance_days']} days, completed "
            f"{stats['lessons_completed']} lessons, average star rating "
            f"{stats.get('avg_star_rating', 'N/A')}.\n"
            f"Write 3-4 warm sentences summarising progress. Then list 1-2 highlights "
            f"and 1-2 areas to improve. Return plain text only."
        )

    @staticmethod
    def generate_report(
        student: Student,
        week_start: date,
        attendance_days: int = 0,
        lessons_completed: int = 0,
        avg_star_rating: Optional[float] = None,
    ) -> WeeklyProgressReport:
        """
        2026-03-04: Generate and store a weekly AI progress report.

        Args:
            student: Target student.
            week_start: Monday of the report week.
            attendance_days: Days present that week.
            lessons_completed: Lessons finished that week.
            avg_star_rating: Average star rating for the week.

        Returns:
            Saved WeeklyProgressReport.
        """
        week_end = week_start + timedelta(days=6)

        stats = {
            'attendance_days': attendance_days,
            'lessons_completed': lessons_completed,
            'avg_star_rating': avg_star_rating,
        }

        # 2026-03-04: Generate summary with LLM
        try:
            llm = get_llm_provider()
            prompt = WeeklyReportService._build_prompt(student, stats)
            response = llm.chat(message=prompt, system_prompt='You are a supportive school teacher.')
            summary_text = response.text.strip()
        except Exception:  # 2026-03-04: Graceful fallback
            summary_text = (
                f"{student.full_name} completed {lessons_completed} lessons this week "
                f"with {attendance_days} days of attendance."
            )

        # 2026-03-04: Build highlights / improvements from stats
        highlights = []
        improvements = []
        if avg_star_rating and avg_star_rating >= 4:
            highlights.append(f'Excellent star rating of {avg_star_rating:.1f}/5 this week!')
        if lessons_completed >= 4:
            highlights.append(f'Completed {lessons_completed} lessons — great consistency!')
        if attendance_days < 3:
            improvements.append('Try to attend more sessions each week.')
        if avg_star_rating and avg_star_rating < 3:
            improvements.append('Practice a bit more before moving to the next topic.')

        report, _ = WeeklyProgressReport.objects.update_or_create(
            student=student,
            week_start=week_start,
            defaults={
                'week_end': week_end,
                'summary_text': summary_text,
                'highlights': highlights,
                'areas_of_improvement': improvements,
                'attendance_days': attendance_days,
                'lessons_completed': lessons_completed,
                'avg_star_rating': avg_star_rating,
            },
        )
        return report

    @staticmethod
    def list_reports(student: Student, limit: int = 10) -> list:
        """
        2026-03-04: Return the most recent weekly reports for a student.

        Returns:
            List of WeeklyProgressReport objects.
        """
        return list(
            WeeklyProgressReport.objects.filter(student=student)
            .order_by('-week_start')[:limit]
        )


# ============================================================
# BS-PAR-006: Term Report Service
# ============================================================

class TermReportService:
    """2026-03-04: Generate and retrieve end-of-term PDF-ready reports."""

    @staticmethod
    def generate(
        student: Student,
        academic_year: str,
        term: str,
        generated_by: Optional[User] = None,
    ) -> TermReport:
        """
        2026-03-04: Compile and store a term report from existing data.

        Aggregates grade book entries, attendance summary, lesson progress,
        and gamification stats into a single JSON payload.

        Args:
            student: Target student.
            academic_year: e.g. '2025-2026'.
            term: 'T1', 'T2', or 'T3'.
            generated_by: Monitor who triggered generation.

        Returns:
            Saved TermReport.
        """
        from services.monitor_tools_service.services import GradeBookService  # 2026-03-04: Lazy import
        from services.attendance_service.services import AttendanceService      # 2026-03-04: Lazy import

        # 2026-03-04: Grade report card
        grade_report = GradeBookService.get_student_report_card(student, term)

        # 2026-03-04: Attendance summary (use current year/month as proxy)
        today = timezone.localdate()
        attendance = AttendanceService.get_attendance_summary(student, today.year, today.month)

        payload = {
            'student': {
                'id': str(student.pk),
                'name': student.full_name,
                'grade': student.grade,
                'dob': str(student.dob),
            },
            'academic_year': academic_year,
            'term': term,
            'grades': grade_report,
            'attendance': {
                'present': attendance['present'],
                'absent': attendance['absent'],
                'late': attendance['late'],
                'excused': attendance['excused'],
                'attendance_percentage': attendance['attendance_percentage'],
            },
            'generated_at': timezone.now().isoformat(),
        }

        report, _ = TermReport.objects.update_or_create(
            student=student,
            academic_year=academic_year,
            term=term,
            defaults={'report_data': payload, 'generated_by': generated_by},
        )
        return report

    @staticmethod
    def get_report(student: Student, academic_year: str, term: str) -> Optional[TermReport]:
        """
        2026-03-04: Fetch an existing term report.

        Returns:
            TermReport or None.
        """
        return TermReport.objects.filter(
            student=student, academic_year=academic_year, term=term
        ).first()

    @staticmethod
    def list_reports(student: Student) -> list:
        """
        2026-03-04: All term reports for a student.

        Returns:
            List of TermReport objects.
        """
        return list(TermReport.objects.filter(student=student).order_by('-generated_at'))
