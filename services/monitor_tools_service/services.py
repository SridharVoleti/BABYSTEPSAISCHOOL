"""
2026-03-04: Monitor Tools Service business logic (BS-MON-005/006/007).

Covers GradeBook, Homework, and Timetable operations.
"""

from datetime import date  # 2026-03-04: Date type
from typing import Optional  # 2026-03-04: Type hints

from django.contrib.auth.models import User  # 2026-03-04: Monitor User
from django.db.models import Avg, Count, Q  # 2026-03-04: Aggregation
from django.utils import timezone  # 2026-03-04: Timezone-aware now()

from services.auth_service.models import Student  # 2026-03-04: Student

from .models import GradeBookEntry, HomeworkAssignment, HomeworkSubmission, TimetableSlot


# ============================================================
# Grade Book Service
# ============================================================

class GradeBookService:
    """2026-03-04: CRUD and reporting for GradeBookEntry."""

    @staticmethod
    def add_grade(
        student: Student,
        subject: str,
        term: str,
        assessment_type: str,
        title: str,
        score: float,
        max_score: float = 100.0,
        remarks: str = '',
        recorded_by: Optional[User] = None,
        date_recorded: Optional[date] = None,
    ) -> GradeBookEntry:
        """
        2026-03-04: Record a new grade for a student.

        Args:
            student: Target student.
            subject: Subject name (e.g. 'Science').
            term: 'T1', 'T2', or 'T3'.
            assessment_type: 'formative', 'summative', or 'project'.
            title: Name of the assessment.
            score: Marks obtained.
            max_score: Total marks (default 100).
            remarks: Optional teacher comment.
            recorded_by: Monitor user.
            date_recorded: Defaults to today.

        Returns:
            Saved GradeBookEntry.
        """
        return GradeBookEntry.objects.create(
            student=student,
            subject=subject,
            term=term,
            assessment_type=assessment_type,
            title=title,
            score=score,
            max_score=max_score,
            remarks=remarks,
            recorded_by=recorded_by,
            date_recorded=date_recorded or timezone.localdate(),
        )

    @staticmethod
    def get_student_grades(
        student: Student,
        subject: Optional[str] = None,
        term: Optional[str] = None,
    ) -> list:
        """
        2026-03-04: Fetch all grades for a student with optional filters.

        Returns:
            List of GradeBookEntry objects.
        """
        qs = GradeBookEntry.objects.filter(student=student)
        if subject:
            qs = qs.filter(subject=subject)
        if term:
            qs = qs.filter(term=term)
        return list(qs.order_by('-date_recorded'))

    @staticmethod
    def get_class_grades(grade: int, subject: str, term: str) -> list:
        """
        2026-03-04: Fetch all grades for a class in a subject/term.

        Returns:
            List of GradeBookEntry objects.
        """
        return list(
            GradeBookEntry.objects.filter(
                student__grade=grade, subject=subject, term=term
            ).select_related('student').order_by('student__full_name')
        )

    @staticmethod
    def get_student_report_card(student: Student, term: str) -> dict:
        """
        2026-03-04: Generate a term report card with per-subject averages.

        Returns:
            Dict: {subject → {avg_score, letter_grade, entries_count}}
        """
        entries = GradeBookEntry.objects.filter(student=student, term=term)
        subjects = entries.values_list('subject', flat=True).distinct()

        report = {}
        for subject in subjects:
            subj_entries = entries.filter(subject=subject)
            scores = [e.percentage for e in subj_entries]
            avg = round(sum(scores) / len(scores), 1) if scores else 0.0
            report[subject] = {
                'avg_percentage': avg,
                'letter_grade': _percentage_to_letter(avg),
                'entries_count': len(scores),
            }
        return report


def _percentage_to_letter(pct: float) -> str:
    """2026-03-04: Convert percentage to letter grade."""
    if pct >= 90:
        return 'A+'
    elif pct >= 80:
        return 'A'
    elif pct >= 70:
        return 'B'
    elif pct >= 60:
        return 'C'
    elif pct >= 50:
        return 'D'
    return 'F'


# ============================================================
# Homework Service
# ============================================================

class HomeworkService:
    """2026-03-04: CRUD and status management for homework."""

    @staticmethod
    def create_assignment(
        grade: int,
        subject: str,
        title: str,
        description: str,
        due_date: date,
        assigned_by: Optional[User] = None,
    ) -> HomeworkAssignment:
        """
        2026-03-04: Monitor creates a homework assignment for a grade.

        Returns:
            Created HomeworkAssignment.
        """
        return HomeworkAssignment.objects.create(
            grade=grade,
            subject=subject,
            title=title,
            description=description,
            due_date=due_date,
            assigned_by=assigned_by,
        )

    @staticmethod
    def list_assignments_for_grade(grade: int, active_only: bool = True) -> list:
        """
        2026-03-04: Return homework assignments for a grade.

        Args:
            grade: Class number.
            active_only: If True, only return non-hidden assignments.

        Returns:
            List of HomeworkAssignment objects.
        """
        qs = HomeworkAssignment.objects.filter(grade=grade)
        if active_only:
            qs = qs.filter(is_active=True)
        return list(qs.order_by('due_date'))

    @staticmethod
    def get_student_homework(student: Student) -> list:
        """
        2026-03-04: Return all active assignments for a student's grade,
        with their submission status merged in.

        Returns:
            List of dicts: {assignment, submission_status, note}
        """
        assignments = HomeworkAssignment.objects.filter(
            grade=student.grade, is_active=True
        ).order_by('due_date')

        submissions = {
            s.homework_id: s
            for s in HomeworkSubmission.objects.filter(student=student)
        }

        result = []
        for hw in assignments:
            sub = submissions.get(hw.pk)
            result.append({
                'id': str(hw.pk),
                'subject': hw.subject,
                'title': hw.title,
                'description': hw.description,
                'due_date': str(hw.due_date),
                'status': sub.status if sub else HomeworkSubmission.STATUS_PENDING,
                'note': sub.note if sub else '',
                'submitted_at': sub.submitted_at.isoformat() if sub and sub.submitted_at else None,
            })
        return result

    @staticmethod
    def mark_done(
        homework_id: str,
        student: Student,
        note: str = '',
    ) -> HomeworkSubmission:
        """
        2026-03-04: Parent/student marks homework as done.

        Returns:
            Updated HomeworkSubmission.
        """
        homework = HomeworkAssignment.objects.get(pk=homework_id)
        sub, _ = HomeworkSubmission.objects.update_or_create(
            homework=homework,
            student=student,
            defaults={
                'status': HomeworkSubmission.STATUS_DONE,
                'note': note,
                'submitted_at': timezone.now(),
            },
        )
        return sub

    @staticmethod
    def get_class_submissions(homework_id: str) -> list:
        """
        2026-03-04: Monitor views all student submissions for an assignment.

        Returns:
            List of HomeworkSubmission objects with student info.
        """
        return list(
            HomeworkSubmission.objects.filter(homework_id=homework_id)
            .select_related('student')
            .order_by('student__full_name')
        )


# ============================================================
# Timetable Service
# ============================================================

class TimetableService:
    """2026-03-04: CRUD for class timetable slots."""

    @staticmethod
    def add_slot(
        grade: int,
        day_of_week: int,
        start_time,
        end_time,
        subject: str,
        teacher_name: str = '',
        room: str = '',
        created_by: Optional[User] = None,
    ) -> TimetableSlot:
        """
        2026-03-04: Monitor adds a new timetable slot.

        Returns:
            Created TimetableSlot.
        """
        return TimetableSlot.objects.create(
            grade=grade,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            subject=subject,
            teacher_name=teacher_name,
            room=room,
            created_by=created_by,
        )

    @staticmethod
    def update_slot(slot_id: str, **fields) -> TimetableSlot:
        """
        2026-03-04: Update a timetable slot's fields.

        Args:
            slot_id: UUID of the slot.
            **fields: Fields to update.

        Returns:
            Updated TimetableSlot.

        Raises:
            TimetableSlot.DoesNotExist if not found.
        """
        slot = TimetableSlot.objects.get(pk=slot_id)
        for key, val in fields.items():
            setattr(slot, key, val)
        slot.save()
        return slot

    @staticmethod
    def delete_slot(slot_id: str) -> None:
        """2026-03-04: Soft-delete a timetable slot."""
        TimetableSlot.objects.filter(pk=slot_id).update(is_active=False)

    @staticmethod
    def get_timetable(grade: int) -> list:
        """
        2026-03-04: Return the full weekly timetable for a grade.

        Returns:
            List of TimetableSlot objects ordered by day, start_time.
        """
        return list(
            TimetableSlot.objects.filter(grade=grade, is_active=True)
            .order_by('day_of_week', 'start_time')
        )

    @staticmethod
    def get_today_schedule(grade: int) -> list:
        """
        2026-03-04: Return today's classes for a grade.

        Returns:
            List of TimetableSlot objects for today's day-of-week.
        """
        today = timezone.localdate()
        # 2026-03-04: Python weekday() → 0=Mon; our model → Mon=1
        day_num = today.weekday() + 1
        return list(
            TimetableSlot.objects.filter(
                grade=grade, day_of_week=day_num, is_active=True
            ).order_by('start_time')
        )
