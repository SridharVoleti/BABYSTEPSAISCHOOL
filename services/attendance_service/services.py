"""
2026-03-04: Attendance Service business logic (BS-ATT).

Purpose:
    Centralise all attendance operations: auto-checkin on login,
    manual marking by monitors, student history, class rosters,
    and monthly summary/report generation.
"""

from datetime import date, datetime, timedelta  # 2026-03-04: Date utilities
from typing import Optional  # 2026-03-04: Type hints

from django.db.models import Count, Q  # 2026-03-04: ORM aggregation
from django.utils import timezone  # 2026-03-04: Timezone-aware now()

from services.auth_service.models import Student  # 2026-03-04: Student model

from .models import AttendanceRecord  # 2026-03-04: Attendance model


class AttendanceService:
    """
    2026-03-04: Service class for all attendance operations.

    All public methods are static — no instance state required.
    """

    # 2026-03-04: Minutes after school start considered 'late'
    LATE_THRESHOLD_MINUTES = 30

    @staticmethod
    def auto_checkin(student: Student) -> AttendanceRecord:
        """
        2026-03-04: Auto-mark a student present when they log in.

        Idempotent — if a record already exists for today, returns it unchanged.
        Sets check_in_time only on first call of the day.

        Args:
            student: The Student logging in.

        Returns:
            The AttendanceRecord for today (created or existing).
        """
        today = timezone.localdate()  # 2026-03-04: Use server local date
        now = timezone.now()  # 2026-03-04: Current timestamp

        record, created = AttendanceRecord.objects.get_or_create(
            student=student,
            date=today,
            defaults={
                'status': AttendanceRecord.STATUS_PRESENT,
                'check_in_time': now,
                'recorded_by': AttendanceRecord.RECORDED_AUTO,
            },
        )
        return record  # 2026-03-04: Return existing or new record

    @staticmethod
    def auto_checkout(student: Student) -> Optional[AttendanceRecord]:
        """
        2026-03-04: Update check_out_time and compute session duration.

        Called when student's JWT expires or they explicitly log out.
        Safe to call multiple times — always updates to latest time.

        Args:
            student: The Student logging out.

        Returns:
            Updated AttendanceRecord or None if no check-in exists today.
        """
        today = timezone.localdate()  # 2026-03-04: Today's date
        now = timezone.now()  # 2026-03-04: Current timestamp

        try:
            record = AttendanceRecord.objects.get(student=student, date=today)
        except AttendanceRecord.DoesNotExist:
            return None  # 2026-03-04: No check-in found — nothing to update

        record.check_out_time = now  # 2026-03-04: Set checkout time

        if record.check_in_time:  # 2026-03-04: Compute duration
            delta = now - record.check_in_time
            record.session_duration_minutes = int(delta.total_seconds() / 60)

        record.save(update_fields=['check_out_time', 'session_duration_minutes', 'updated_at'])
        return record

    @staticmethod
    def mark_attendance(
        student: Student,
        target_date: date,
        status: str,
        notes: str = '',
    ) -> AttendanceRecord:
        """
        2026-03-04: Manually set a student's attendance status (by monitor).

        Creates or overwrites the record for the given date.

        Args:
            student: Target student.
            target_date: Date to mark.
            status: One of AttendanceRecord.STATUS_* constants.
            notes: Optional monitor notes.

        Returns:
            The updated AttendanceRecord.

        Raises:
            ValueError: If status is not a valid choice.
        """
        valid = {c[0] for c in AttendanceRecord.STATUS_CHOICES}
        if status not in valid:
            raise ValueError(f'Invalid status: {status}. Must be one of {valid}')

        record, _ = AttendanceRecord.objects.update_or_create(
            student=student,
            date=target_date,
            defaults={
                'status': status,
                'recorded_by': AttendanceRecord.RECORDED_MONITOR,
                'notes': notes,
            },
        )
        return record

    @staticmethod
    def get_class_attendance(grade: int, target_date: date) -> list:
        """
        2026-03-04: Return attendance roster for all students in a grade on a date.

        Students with no record are synthesised as absent.

        Args:
            grade: Class number (1-12).
            target_date: The date to query.

        Returns:
            List of dicts: {student_id, full_name, status, check_in_time,
                            session_duration_minutes, recorded_by, notes}
        """
        students = Student.objects.filter(  # 2026-03-04: All active students in grade
            grade=grade, is_active=True
        ).order_by('full_name')

        records = {  # 2026-03-04: Map student_id → record
            r.student_id: r
            for r in AttendanceRecord.objects.filter(
                student__in=students, date=target_date
            ).select_related('student')
        }

        roster = []
        for student in students:
            rec = records.get(student.pk)
            roster.append({
                'student_id': str(student.pk),
                'full_name': student.full_name,
                'status': rec.status if rec else AttendanceRecord.STATUS_ABSENT,
                'check_in_time': rec.check_in_time.isoformat() if rec and rec.check_in_time else None,
                'session_duration_minutes': rec.session_duration_minutes if rec else None,
                'recorded_by': rec.recorded_by if rec else AttendanceRecord.RECORDED_SYSTEM,
                'notes': rec.notes if rec else '',
                'record_id': str(rec.pk) if rec else None,
            })
        return roster

    @staticmethod
    def get_student_attendance(
        student: Student,
        start_date: date,
        end_date: date,
    ) -> list:
        """
        2026-03-04: Return all attendance records for a student in a date range.

        Args:
            student: The student.
            start_date: Inclusive start date.
            end_date: Inclusive end date.

        Returns:
            List of AttendanceRecord objects ordered by date ascending.
        """
        return list(
            AttendanceRecord.objects.filter(
                student=student,
                date__gte=start_date,
                date__lte=end_date,
            ).order_by('date')
        )

    @staticmethod
    def get_attendance_summary(student: Student, year: int, month: int) -> dict:
        """
        2026-03-04: Monthly attendance summary for a student.

        Args:
            student: The student.
            year: Calendar year.
            month: Calendar month (1-12).

        Returns:
            Dict with counts: present, absent, late, excused, total_school_days,
            attendance_percentage, avg_session_minutes.
        """
        from calendar import monthrange  # 2026-03-04: Month length

        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])

        records = AttendanceRecord.objects.filter(
            student=student,
            date__gte=start,
            date__lte=end,
        )

        counts = records.values('status').annotate(n=Count('status'))
        status_map = {row['status']: row['n'] for row in counts}

        present = status_map.get(AttendanceRecord.STATUS_PRESENT, 0)
        late = status_map.get(AttendanceRecord.STATUS_LATE, 0)
        absent = status_map.get(AttendanceRecord.STATUS_ABSENT, 0)
        excused = status_map.get(AttendanceRecord.STATUS_EXCUSED, 0)
        total = present + late + absent + excused

        # 2026-03-04: Attendance % = (present + late) / total
        attendance_pct = round((present + late) / total * 100, 1) if total > 0 else 0.0

        # 2026-03-04: Average session duration (only present/late days)
        durations = list(
            records.filter(
                status__in=[AttendanceRecord.STATUS_PRESENT, AttendanceRecord.STATUS_LATE],
                session_duration_minutes__isnull=False,
            ).values_list('session_duration_minutes', flat=True)
        )
        avg_session = round(sum(durations) / len(durations)) if durations else None

        return {
            'year': year,
            'month': month,
            'present': present,
            'late': late,
            'absent': absent,
            'excused': excused,
            'total_recorded_days': total,
            'attendance_percentage': attendance_pct,
            'avg_session_minutes': avg_session,
        }

    @staticmethod
    def mark_absent_batch(grade: int, target_date: date) -> int:
        """
        2026-03-04: System job — mark all students with no record as absent.

        Called at end of school day for students who never logged in.

        Args:
            grade: Class number.
            target_date: Date to fill.

        Returns:
            Number of absent records created.
        """
        students = Student.objects.filter(grade=grade, is_active=True)
        existing = set(
            AttendanceRecord.objects.filter(
                student__in=students, date=target_date
            ).values_list('student_id', flat=True)
        )

        to_create = [
            AttendanceRecord(
                student=s,
                date=target_date,
                status=AttendanceRecord.STATUS_ABSENT,
                recorded_by=AttendanceRecord.RECORDED_SYSTEM,
            )
            for s in students
            if s.pk not in existing
        ]
        AttendanceRecord.objects.bulk_create(to_create)
        return len(to_create)
