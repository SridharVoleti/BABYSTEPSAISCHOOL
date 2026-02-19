"""
2026-02-19: Read-Along & Mimic Engine models (BS-RAM).

Purpose:
    Language: DB-backed registry of Indian languages. Admins can add
    new languages via Django admin without any code changes.
    ReadAlongSession: Records a student's read-along attempt for a
    lesson day, including per-sentence Levenshtein scores and star rating.
"""

import uuid  # 2026-02-19: UUID primary keys

from django.db import models  # 2026-02-19: Django ORM
from django.core.validators import (  # 2026-02-19: Field validators
    MinValueValidator, MaxValueValidator
)

from services.auth_service.models import Student  # 2026-02-19: Cross-app FK
from services.teaching_engine.models import TeachingLesson  # 2026-02-19: Cross-app FK


class Language(models.Model):
    """
    2026-02-19: Admin-manageable language entry.

    Add new Indian languages from Django admin (/admin/read_along_service/language/)
    without any code changes. The service reads from this table at runtime.
    """

    name = models.CharField(  # 2026-02-19: Canonical name, e.g. 'Telugu'
        max_length=50, unique=True
    )
    bcp47_tag = models.CharField(  # 2026-02-19: BCP-47 tag, e.g. 'te-IN'
        max_length=10
    )
    display_name = models.CharField(  # 2026-02-19: Native-script display name
        max_length=100
    )
    script = models.CharField(  # 2026-02-19: Script family, e.g. 'Telugu'
        max_length=30
    )
    tts_rate = models.FloatField(  # 2026-02-19: TTS playback rate (0.0-1.0)
        default=0.85
    )
    is_active = models.BooleanField(  # 2026-02-19: Deactivate without deleting
        default=True
    )
    sort_order = models.IntegerField(  # 2026-02-19: Display order in picker
        default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-19: Created

    class Meta:
        """2026-02-19: Model metadata."""

        ordering = ['sort_order', 'name']  # 2026-02-19: Natural display order

    def __str__(self):
        """2026-02-19: String representation."""
        return f"{self.name} ({self.bcp47_tag})"


# 2026-02-19: Star rating thresholds (score → stars)
# 0 = <0.40, 1 = <0.55, 2 = <0.70, 3 = <0.82, 4 = <0.92, 5 = ≥0.92
STAR_THRESHOLDS = [0.40, 0.55, 0.70, 0.82, 0.92]


class ReadAlongSession(models.Model):
    """
    2026-02-19: Records a student's read-along attempt for one lesson day.

    Stores per-sentence Levenshtein similarity scores (0.0-1.0), overall
    mean score, star rating (0-5), and attempt metadata. Supports retries
    via attempt_number; is_new_best is computed by the service layer.
    """

    STATUS_CHOICES = [  # 2026-02-19: Session lifecycle states
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(  # 2026-02-19: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-19: Link to student
        Student, on_delete=models.CASCADE, related_name='read_along_sessions'
    )
    lesson = models.ForeignKey(  # 2026-02-19: Link to teaching lesson
        TeachingLesson, on_delete=models.CASCADE, related_name='read_along_sessions'
    )
    day_number = models.IntegerField(  # 2026-02-19: Day within lesson (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    language = models.CharField(  # 2026-02-19: Language name, e.g. 'Telugu'
        max_length=30
    )
    bcp47_tag = models.CharField(  # 2026-02-19: BCP-47 tag used, e.g. 'te-IN'
        max_length=10
    )
    sentence_scores = models.JSONField(  # 2026-02-19: Per-sentence scores [0.0–1.0]
        default=list
    )
    overall_score = models.FloatField(default=0.0)  # 2026-02-19: Mean of sentence_scores
    star_rating = models.IntegerField(  # 2026-02-19: 0-5 stars
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    sentences_attempted = models.IntegerField(default=0)  # 2026-02-19: Sentences tried
    sentences_total = models.IntegerField(default=0)  # 2026-02-19: Total sentences
    attempt_number = models.IntegerField(default=1)  # 2026-02-19: Retry counter
    status = models.CharField(  # 2026-02-19: Session lifecycle
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    time_spent_seconds = models.IntegerField(default=0)  # 2026-02-19: Duration
    completed_at = models.DateTimeField(  # 2026-02-19: Completion timestamp
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-19: Created

    class Meta:
        """2026-02-19: Model metadata."""

        unique_together = [  # 2026-02-19: One record per attempt combo
            'student', 'lesson', 'day_number', 'language', 'attempt_number'
        ]
        ordering = ['-created_at']  # 2026-02-19: Newest first

    def __str__(self):
        """2026-02-19: String representation."""
        return (
            f"{self.student.full_name} | {self.lesson.lesson_id} "
            f"Day {self.day_number} ({self.language}) #{self.attempt_number} "
            f"— {self.star_rating}★"
        )
