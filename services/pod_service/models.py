"""
2026-03-04: Pod Management & AI Student Monitoring models (BS-POD + BS-MON).

Purpose:
    Data models for student pods, enrollments, attention tracking,
    alert management, and monitor dashboard. Supports groups of up
    to 5 students, real-time heartbeat monitoring, and parent alerts.
"""

import uuid  # 2026-03-04: UUID primary keys

from django.db import models  # 2026-03-04: ORM base
from django.utils import timezone  # 2026-03-04: Timezone-aware timestamps

from services.auth_service.models import Student  # 2026-03-04: Student model


class Pod(models.Model):
    """
    2026-03-04: A learning pod — a group of up to 5 students.

    Pods are managed by admin. Students join via PodEnrollment.
    Each pod has a subject focus (or 'All') and a grade level.
    """

    id = models.UUIDField(  # 2026-03-04: UUID primary key
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    name = models.CharField(  # 2026-03-04: Human-readable pod name
        max_length=100,
        help_text='E.g. "Pod Alpha – Grade 6"',
    )
    grade = models.IntegerField(  # 2026-03-04: Grade 1-12
        help_text='Grade level (1-12)',
    )
    subject_focus = models.CharField(  # 2026-03-04: Optional subject
        max_length=100,
        blank=True,
        default='All',
        help_text='Subject focus, or "All" for multi-subject pods',
    )
    max_size = models.IntegerField(  # 2026-03-04: Pod cap (default 5)
        default=5,
    )
    is_active = models.BooleanField(default=True)  # 2026-03-04: Soft delete
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-04: Creation time
    updated_at = models.DateTimeField(auto_now=True)  # 2026-03-04: Last update

    class Meta:
        """2026-03-04: Pod metadata."""

        ordering = ['grade', 'name']  # 2026-03-04: Ordered by grade then name

    def __str__(self):
        """2026-03-04: Human-readable representation."""
        return f"{self.name} (Grade {self.grade})"

    @property
    def active_enrollment_count(self):
        """2026-03-04: Count of active enrollments in this pod."""
        return self.enrollments.filter(is_active=True).count()  # 2026-03-04: Active count


class PodEnrollment(models.Model):
    """
    2026-03-04: Links a student to a pod.

    A student may only be in one active pod at a time.
    Admin controls enrollment via Django admin or API.
    """

    id = models.UUIDField(  # 2026-03-04: UUID primary key
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    pod = models.ForeignKey(  # 2026-03-04: Pod reference
        Pod,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )
    student = models.ForeignKey(  # 2026-03-04: Student reference
        Student,
        on_delete=models.CASCADE,
        related_name='pod_enrollments',
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)  # 2026-03-04: Enrollment time
    is_active = models.BooleanField(default=True)  # 2026-03-04: Active flag

    class Meta:
        """2026-03-04: Enrollment metadata."""

        unique_together = ('pod', 'student')  # 2026-03-04: One enrollment per pod/student pair
        ordering = ['enrolled_at']  # 2026-03-04: Oldest first

    def __str__(self):
        """2026-03-04: Human-readable representation."""
        return f"{self.student.full_name} → {self.pod.name}"


class StudentSession(models.Model):
    """
    2026-03-04: Tracks a student's active learning session within a pod.

    Created when a student starts a lesson. Updated via heartbeat pings
    every 30 seconds. Attention score is updated by camera events.
    """

    student = models.ForeignKey(  # 2026-03-04: Session owner
        Student,
        on_delete=models.CASCADE,
        related_name='learning_sessions',
    )
    pod_enrollment = models.ForeignKey(  # 2026-03-04: Active enrollment
        PodEnrollment,
        on_delete=models.CASCADE,
        related_name='sessions',
    )
    session_start = models.DateTimeField(  # 2026-03-04: When session started
        default=timezone.now,
    )
    last_heartbeat = models.DateTimeField(  # 2026-03-04: Last ping (indexed)
        default=timezone.now,
        db_index=True,
    )
    attention_score = models.FloatField(  # 2026-03-04: 0.0-1.0 (camera-derived)
        default=1.0,
        help_text='0.0=not focusing, 1.0=fully focused',
    )
    is_active = models.BooleanField(  # 2026-03-04: True if heartbeat < 90s ago
        default=True,
    )

    class Meta:
        """2026-03-04: Session metadata."""

        ordering = ['-session_start']  # 2026-03-04: Newest first

    def __str__(self):
        """2026-03-04: Human-readable representation."""
        return f"{self.student.full_name} session @ {self.session_start:%Y-%m-%d %H:%M}"

    @property
    def is_heartbeat_alive(self):
        """2026-03-04: Returns True if heartbeat received within the last 90 seconds."""
        from datetime import timedelta  # 2026-03-04: Local import
        cutoff = timezone.now() - timedelta(seconds=90)  # 2026-03-04: 90s threshold
        return self.last_heartbeat >= cutoff  # 2026-03-04: Still alive?


# 2026-03-04: Attention event type choices
ATTENTION_EVENT_TYPES = [
    ('not_visible', 'Face Not Visible'),
    ('not_looking', 'Not Looking at Screen'),
    ('sleeping', 'Appears to be Sleeping'),
    ('inactive', 'No Interaction (Inactive)'),
]


class AttentionEvent(models.Model):
    """
    2026-03-04: Records a single attention anomaly detected client-side.

    The frontend detects face/gaze events via camera and POSTs them here.
    The AI system logs what action was taken and whether it escalated to parent.
    """

    student = models.ForeignKey(  # 2026-03-04: Student who triggered event
        Student,
        on_delete=models.CASCADE,
        related_name='attention_events',
    )
    session = models.ForeignKey(  # 2026-03-04: Active session
        StudentSession,
        on_delete=models.CASCADE,
        related_name='attention_events',
        null=True,
        blank=True,
    )
    event_type = models.CharField(  # 2026-03-04: Type of attention issue
        max_length=30,
        choices=ATTENTION_EVENT_TYPES,
    )
    detected_at = models.DateTimeField(  # 2026-03-04: When event was detected
        default=timezone.now,
        db_index=True,
    )
    ai_response = models.CharField(  # 2026-03-04: What the AI said/did
        max_length=500,
        blank=True,
        default='',
    )
    escalated = models.BooleanField(  # 2026-03-04: Whether parent was alerted
        default=False,
    )
    escalation_count = models.IntegerField(  # 2026-03-04: How many times escalated
        default=0,
    )

    class Meta:
        """2026-03-04: AttentionEvent metadata."""

        ordering = ['-detected_at']  # 2026-03-04: Newest first

    def __str__(self):
        """2026-03-04: Human-readable representation."""
        return f"{self.student.full_name} – {self.event_type} @ {self.detected_at:%H:%M}"


# 2026-03-04: Monitor alert type choices
ALERT_TYPE_CHOICES = [
    ('parent_alert', 'Parent Alert (WhatsApp)'),
    ('monitor_flag', 'Monitor Flag (dashboard)'),
    ('help_request', 'Student Help Request'),
]


class MonitorAlert(models.Model):
    """
    2026-03-04: A monitor or parent-facing alert about a student's session.

    Created by AlertService when attention events escalate or when
    a student presses the "Need Help" button.
    """

    student = models.ForeignKey(  # 2026-03-04: Alert subject
        Student,
        on_delete=models.CASCADE,
        related_name='monitor_alerts',
    )
    alert_type = models.CharField(  # 2026-03-04: Alert category
        max_length=30,
        choices=ALERT_TYPE_CHOICES,
    )
    message = models.TextField()  # 2026-03-04: Alert message
    is_resolved = models.BooleanField(default=False)  # 2026-03-04: Resolved flag
    created_at = models.DateTimeField(  # 2026-03-04: Alert timestamp
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        """2026-03-04: MonitorAlert metadata."""

        ordering = ['-created_at']  # 2026-03-04: Newest first

    def __str__(self):
        """2026-03-04: Human-readable representation."""
        return f"[{self.alert_type}] {self.student.full_name} – {self.message[:60]}"
