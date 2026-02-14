"""
2026-02-12: Diagnostic assessment service models.

Purpose:
    Define database models for the diagnostic module (BS-DIA).
    Covers diagnostic sessions, individual responses, and final results.
    Uses IRT 3PL adaptive testing to place students at Foundation/Standard/Advanced.
"""

import uuid  # 2026-02-12: UUID for primary keys

from django.db import models  # 2026-02-12: Django ORM

from services.auth_service.models import Student  # 2026-02-12: Cross-app FK


class DiagnosticSession(models.Model):
    """
    2026-02-12: Tracks one diagnostic assessment sitting.

    Each student takes one diagnostic assessment after first login.
    The session tracks theta estimation progress and final result.
    """

    STATUS_CHOICES = [  # 2026-02-12: Session status options
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    LEVEL_CHOICES = [  # 2026-02-12: IQ level placement results
        ('foundation', 'Foundation'),
        ('standard', 'Standard'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-12: Link to student
        Student, on_delete=models.CASCADE, related_name='diagnostic_sessions'
    )
    status = models.CharField(  # 2026-02-12: Session lifecycle
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    theta_estimate = models.FloatField(  # 2026-02-12: Current ability estimate
        default=0.0,
        help_text='Current IRT theta estimate, clamped to [-3, 3]'
    )
    items_administered = models.IntegerField(  # 2026-02-12: Questions answered so far
        default=0
    )
    total_items = models.IntegerField(  # 2026-02-12: Target number of items
        default=25
    )
    result_level = models.CharField(  # 2026-02-12: Final placement (null until complete)
        max_length=20, choices=LEVEL_CHOICES, blank=True, default=''
    )
    domain_scores = models.JSONField(  # 2026-02-12: Per-subject theta scores
        default=dict, blank=True,
        help_text='Dict of domain -> theta, e.g. {"math": 0.5, "language": -0.2}'
    )
    current_item_id = models.CharField(  # 2026-02-12: Next item to present
        max_length=50, blank=True, default=''
    )
    administered_item_ids = models.JSONField(  # 2026-02-12: Already-used item IDs
        default=list, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-12: Last update timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-created_at']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"DiagSession {self.student.full_name} ({self.status})"


class DiagnosticResponse(models.Model):
    """
    2026-02-12: Records a single item response within a diagnostic session.

    Tracks correctness, timing, and the theta estimate after each response.
    """

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-02-12: Link to session
        DiagnosticSession, on_delete=models.CASCADE, related_name='responses'
    )
    item_id = models.CharField(max_length=50)  # 2026-02-12: Question bank item ID
    is_correct = models.BooleanField()  # 2026-02-12: Whether answer was correct
    response_time_ms = models.IntegerField(  # 2026-02-12: Time to answer in ms
        default=0
    )
    theta_after = models.FloatField(  # 2026-02-12: Theta estimate after this response
        default=0.0
    )
    position = models.IntegerField()  # 2026-02-12: Item position (1-based)
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['position']  # 2026-02-12: By order administered

    def __str__(self):
        """2026-02-12: String representation."""
        correct_str = 'correct' if self.is_correct else 'incorrect'  # 2026-02-12: Label
        return f"Response #{self.position} ({correct_str})"


class DiagnosticResult(models.Model):
    """
    2026-02-12: Final diagnostic placement result - one per student.

    Created when a diagnostic session completes. OneToOneField ensures
    only one result per student (the definitive placement).
    """

    LEVEL_CHOICES = [  # 2026-02-12: Same as session
        ('foundation', 'Foundation'),
        ('standard', 'Standard'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(  # 2026-02-12: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.OneToOneField(  # 2026-02-12: One result per student
        Student, on_delete=models.CASCADE, related_name='diagnostic_result'
    )
    session = models.OneToOneField(  # 2026-02-12: Link to completed session
        DiagnosticSession, on_delete=models.CASCADE, related_name='result'
    )
    overall_level = models.CharField(  # 2026-02-12: Foundation/Standard/Advanced
        max_length=20, choices=LEVEL_CHOICES
    )
    theta_final = models.FloatField()  # 2026-02-12: Final theta estimate
    domain_levels = models.JSONField(  # 2026-02-12: Per-subject levels
        default=dict, blank=True,
        help_text='Dict of domain -> level, e.g. {"math": "advanced"}'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-12: Creation timestamp

    class Meta:
        """2026-02-12: Model metadata."""

        ordering = ['-created_at']  # 2026-02-12: Newest first

    def __str__(self):
        """2026-02-12: String representation."""
        return f"Result: {self.student.full_name} -> {self.overall_level}"
