"""
2026-03-04: Attendance Service models (BS-ATT).

Purpose:
    Track daily student attendance. Records are created automatically
    when a student logs in (auto) or manually by a monitor/teacher.
"""

import uuid  # 2026-03-04: UUID primary keys

from django.db import models  # 2026-03-04: Django ORM

from services.auth_service.models import Student  # 2026-03-04: Student FK


class AttendanceRecord(models.Model):
    """
    2026-03-04: One attendance record per student per date.

    Created automatically on login or manually by a monitor.
    Unique constraint enforces one record per (student, date).
    """

    STATUS_PRESENT = 'present'  # 2026-03-04: Student attended
    STATUS_ABSENT = 'absent'    # 2026-03-04: Student did not attend
    STATUS_LATE = 'late'        # 2026-03-04: Student logged in late
    STATUS_EXCUSED = 'excused'  # 2026-03-04: Approved absence

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'Present'),
        (STATUS_ABSENT, 'Absent'),
        (STATUS_LATE, 'Late'),
        (STATUS_EXCUSED, 'Excused'),
    ]

    RECORDED_AUTO = 'auto'      # 2026-03-04: Recorded via student login
    RECORDED_MONITOR = 'monitor'  # 2026-03-04: Recorded manually by monitor
    RECORDED_SYSTEM = 'system'  # 2026-03-04: End-of-day system job

    RECORDED_BY_CHOICES = [
        (RECORDED_AUTO, 'Auto (login)'),
        (RECORDED_MONITOR, 'Monitor'),
        (RECORDED_SYSTEM, 'System'),
    ]

    id = models.UUIDField(  # 2026-03-04: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-04: Which student
        Student,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        db_index=True,
    )
    date = models.DateField(db_index=True)  # 2026-03-04: Calendar date (no time)
    status = models.CharField(  # 2026-03-04: Attendance status
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT,
    )
    check_in_time = models.DateTimeField(  # 2026-03-04: First login timestamp
        null=True, blank=True
    )
    check_out_time = models.DateTimeField(  # 2026-03-04: Last activity timestamp
        null=True, blank=True
    )
    session_duration_minutes = models.IntegerField(  # 2026-03-04: Minutes active (computed)
        null=True, blank=True
    )
    recorded_by = models.CharField(  # 2026-03-04: How it was recorded
        max_length=10,
        choices=RECORDED_BY_CHOICES,
        default=RECORDED_AUTO,
    )
    notes = models.TextField(blank=True, default='')  # 2026-03-04: Monitor notes
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-04: Record creation
    updated_at = models.DateTimeField(auto_now=True)  # 2026-03-04: Last update

    class Meta:
        """2026-03-04: Model metadata."""

        unique_together = ('student', 'date')  # 2026-03-04: One record per student per day
        ordering = ['-date', 'student']  # 2026-03-04: Most recent first
        indexes = [
            models.Index(fields=['date', 'student']),  # 2026-03-04: Daily roster query
        ]

    def __str__(self):
        """2026-03-04: String representation."""
        return f'{self.student.full_name} — {self.date} — {self.status}'
