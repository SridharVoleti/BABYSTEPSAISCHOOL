"""
2026-02-19: Parent Dashboard models.

Purpose:
    Define database models for the Parent Dashboard module (BS-PAR).
    Currently covers parental controls per student.
"""

import uuid  # 2026-02-19: UUID for primary keys

from django.db import models  # 2026-02-19: Django ORM

from services.auth_service.models import Student  # 2026-02-19: Student FK


class ParentalControls(models.Model):
    """
    2026-02-19: Per-student parental control settings.

    Parents set screen time limits, learning schedules, and
    control AI conversation log visibility per child.
    """

    id = models.UUIDField(  # 2026-02-19: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.OneToOneField(  # 2026-02-19: One settings record per student
        Student,
        on_delete=models.CASCADE,
        related_name='parental_controls',
    )
    daily_time_limit_minutes = models.IntegerField(  # 2026-02-19: Daily screen time cap
        default=120,
        help_text='Daily time limit in minutes (15-480)',
    )
    schedule_enabled = models.BooleanField(  # 2026-02-19: Learning schedule on/off
        default=False
    )
    schedule_start_time = models.TimeField(  # 2026-02-19: When learning window opens
        null=True, blank=True
    )
    schedule_end_time = models.TimeField(  # 2026-02-19: When learning window closes
        null=True, blank=True
    )
    ai_log_enabled = models.BooleanField(  # 2026-02-19: Parent can view AI chat log
        default=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-19: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-19: Last updated

    class Meta:
        """2026-02-19: Model metadata."""

        verbose_name = 'Parental Controls'  # 2026-02-19: Admin display
        verbose_name_plural = 'Parental Controls'  # 2026-02-19: Admin plural

    def __str__(self):
        """2026-02-19: String representation."""
        return f"Controls for {self.student.full_name}"
