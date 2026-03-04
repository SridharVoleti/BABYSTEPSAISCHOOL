"""
2026-03-04: Communication Service models (BS-COM-001/002/003, BS-PAR-006).

Three sub-modules:
  - BS-COM-001: Message — parent↔monitor direct messaging thread
  - BS-COM-002: Announcement — school-wide or grade-level notice board
  - BS-COM-003: WeeklyProgressReport — AI-generated weekly summary per student
  - BS-PAR-006: TermReport — end-of-term PDF-ready report (JSON payload)
"""

import uuid

from django.contrib.auth.models import User
from django.db import models

from services.auth_service.models import Parent, Student


# ============================================================
# BS-COM-001: Parent–Monitor Messaging
# ============================================================

class MessageThread(models.Model):
    """
    2026-03-04: A conversation thread between a parent and a monitor.

    Each thread is tied to one student (the topic) and has two parties:
    the parent and the monitor.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(  # 2026-03-04: Topic of the thread
        Student, on_delete=models.CASCADE, related_name='message_threads'
    )
    parent = models.ForeignKey(  # 2026-03-04: Parent party
        Parent, on_delete=models.CASCADE, related_name='message_threads'
    )
    monitor = models.ForeignKey(  # 2026-03-04: Monitor party
        User, on_delete=models.CASCADE, related_name='message_threads',
        limit_choices_to={'is_staff': True},
    )
    subject = models.CharField(max_length=200, blank=True, default='')
    is_closed = models.BooleanField(default=False)  # 2026-03-04: Resolved thread
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Thread: {self.student.full_name} ({self.parent} ↔ {self.monitor})'


class Message(models.Model):
    """
    2026-03-04: A single message within a MessageThread.

    Sender is either the parent (SENDER_PARENT) or monitor (SENDER_MONITOR).
    """

    SENDER_PARENT  = 'parent'
    SENDER_MONITOR = 'monitor'
    SENDER_CHOICES = [
        (SENDER_PARENT,  'Parent'),
        (SENDER_MONITOR, 'Monitor'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(  # 2026-03-04: Which thread
        MessageThread, on_delete=models.CASCADE, related_name='messages'
    )
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)  # 2026-03-04: Who sent
    body = models.TextField()  # 2026-03-04: Message text
    is_read = models.BooleanField(default=False)  # 2026-03-04: Read by recipient
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender_type}: {self.body[:50]}'


# ============================================================
# BS-COM-002: Announcements
# ============================================================

class Announcement(models.Model):
    """
    2026-03-04: A school-wide or grade-specific announcement.

    Monitors create announcements; parents and students read them.
    """

    AUDIENCE_ALL    = 'all'      # 2026-03-04: All users
    AUDIENCE_GRADE  = 'grade'    # 2026-03-04: Specific grade(s)
    AUDIENCE_PARENT = 'parents'  # 2026-03-04: Parents only

    AUDIENCE_CHOICES = [
        (AUDIENCE_ALL,    'All'),
        (AUDIENCE_GRADE,  'Specific Grade'),
        (AUDIENCE_PARENT, 'Parents Only'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)           # 2026-03-04: Heading
    body = models.TextField()                          # 2026-03-04: Full content
    audience = models.CharField(                       # 2026-03-04: Target audience
        max_length=10, choices=AUDIENCE_CHOICES, default=AUDIENCE_ALL
    )
    grades = models.JSONField(default=list, blank=True)  # 2026-03-04: e.g. [5, 6, 7] for GRADE audience
    priority = models.CharField(                       # 2026-03-04: Visual priority
        max_length=10,
        choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],
        default='normal',
    )
    created_by = models.ForeignKey(                    # 2026-03-04: Monitor author
        User, on_delete=models.SET_NULL, null=True, related_name='announcements'
    )
    is_active = models.BooleanField(default=True)      # 2026-03-04: Published flag
    publish_at = models.DateTimeField(null=True, blank=True)  # 2026-03-04: Scheduled publish
    expires_at = models.DateTimeField(null=True, blank=True)  # 2026-03-04: Auto-expire
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.priority.upper()}] {self.title}'


# ============================================================
# BS-COM-003: Weekly AI Progress Report
# ============================================================

class WeeklyProgressReport(models.Model):
    """
    2026-03-04: AI-generated weekly progress summary per student.

    Generated server-side every Sunday night. Sent to parent via
    WhatsApp/email if enabled. Stored for reference.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(  # 2026-03-04: Which student
        Student, on_delete=models.CASCADE, related_name='weekly_reports'
    )
    week_start = models.DateField()  # 2026-03-04: Monday of the week
    week_end = models.DateField()    # 2026-03-04: Sunday of the week
    summary_text = models.TextField()  # 2026-03-04: AI-generated narrative
    highlights = models.JSONField(default=list)  # 2026-03-04: List of achievement strings
    areas_of_improvement = models.JSONField(default=list)  # 2026-03-04: Improvement areas
    attendance_days = models.IntegerField(default=0)  # 2026-03-04: Days present this week
    lessons_completed = models.IntegerField(default=0)  # 2026-03-04: Lessons finished
    avg_star_rating = models.FloatField(null=True, blank=True)  # 2026-03-04: Average stars
    delivered_whatsapp = models.BooleanField(default=False)  # 2026-03-04: Sent via WA
    delivered_email = models.BooleanField(default=False)     # 2026-03-04: Sent via email
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-week_start']
        unique_together = ('student', 'week_start')  # 2026-03-04: One per student per week

    def __str__(self):
        return f'{self.student.full_name} week of {self.week_start}'


# ============================================================
# BS-PAR-006: Term Progress Report (PDF-ready)
# ============================================================

class TermReport(models.Model):
    """
    2026-03-04: End-of-term comprehensive progress report.

    Stores a JSON payload containing all grade, attendance, and
    activity data. A separate utility renders this to a downloadable PDF.
    The PDF is generated on-demand (no file storage required).
    """

    TERM_1 = 'T1'
    TERM_2 = 'T2'
    TERM_3 = 'T3'

    TERM_CHOICES = [
        (TERM_1, 'Term 1'), (TERM_2, 'Term 2'), (TERM_3, 'Term 3'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(  # 2026-03-04: Student
        Student, on_delete=models.CASCADE, related_name='term_reports'
    )
    academic_year = models.CharField(max_length=9)  # 2026-03-04: e.g. '2025-2026'
    term = models.CharField(max_length=2, choices=TERM_CHOICES)
    report_data = models.JSONField()  # 2026-03-04: Full structured report payload
    generated_by = models.ForeignKey(  # 2026-03-04: Monitor who triggered generation
        User, on_delete=models.SET_NULL, null=True, related_name='term_reports_generated'
    )
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']
        unique_together = ('student', 'academic_year', 'term')

    def __str__(self):
        return f'{self.student.full_name} | {self.academic_year} | {self.term}'
