"""
2026-02-19: Comprehension Capture Engine database models (BS-CMP).

Purpose:
    Store per-attempt comprehension evaluations linking student explanations
    to LLM scores, anti-parroting flags, and the final weighted star rating.
"""

import uuid  # 2026-02-19: UUID primary keys

from django.db import models  # 2026-02-19: Django ORM
from django.core.validators import MinValueValidator, MaxValueValidator  # 2026-02-19: Validators

from services.auth_service.models import Student  # 2026-02-19: Cross-app FK
from services.teaching_engine.models import TeachingLesson  # 2026-02-19: Cross-app FK


class ComprehensionEvaluation(models.Model):
    """
    2026-02-19: One comprehension attempt per student per lesson day.

    Records the student's explanation text, LLM scores across 5 dimensions,
    the anti-parroting flag, the weighted star rating formula result, and
    the attempt sequence number (multiple retries allowed).

    The weighted_score formula is:
        (practice_stars / 5 × 100) × 0.30
        + comprehension_score × 0.40
        + application_score × 0.20     ← defaults to 50 (BS-APP placeholder)
        + retention_score  × 0.10     ← defaults to 50 (BS-RET placeholder)

    weighted_star_rating = min(5, ceil(weighted_score / 20))
    """

    id = models.UUIDField(  # 2026-02-19: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-19: Link to student
        Student, on_delete=models.CASCADE,
        related_name='comprehension_evals'
    )
    lesson = models.ForeignKey(  # 2026-02-19: Link to teaching lesson
        TeachingLesson, on_delete=models.CASCADE,
        related_name='comprehension_evals'
    )
    day_number = models.IntegerField(  # 2026-02-19: Day (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )

    # 2026-02-19: Student explanation fields
    student_text = models.TextField()  # 2026-02-19: What the student said
    is_parroting = models.BooleanField(default=False)  # 2026-02-19: Parroting flag

    # 2026-02-19: LLM dimension scores (0-100 each)
    score_understanding = models.IntegerField(default=0)  # 2026-02-19: Main idea grasp
    score_accuracy = models.IntegerField(default=0)  # 2026-02-19: Factual correctness
    score_own_words = models.IntegerField(default=0)  # 2026-02-19: Own-words usage
    score_depth = models.IntegerField(default=0)  # 2026-02-19: Detail/examples
    score_clarity = models.IntegerField(default=0)  # 2026-02-19: Clarity of expression

    # 2026-02-19: Derived scores
    comprehension_score = models.FloatField(default=0.0)  # 2026-02-19: Mean of 5 dims
    llm_feedback = models.TextField(default='')  # 2026-02-19: Encouraging feedback
    llm_error = models.BooleanField(default=False)  # 2026-02-19: True if LLM failed

    # 2026-02-19: Weighted star formula inputs
    practice_stars = models.IntegerField(default=0)  # 2026-02-19: Mastery practice stars
    application_score = models.FloatField(default=50.0)  # 2026-02-19: Placeholder (BS-APP)
    retention_score = models.FloatField(default=50.0)  # 2026-02-19: Placeholder (BS-RET)

    # 2026-02-19: Weighted formula outputs
    weighted_score = models.FloatField(default=0.0)  # 2026-02-19: 0-100 composite
    weighted_star_rating = models.IntegerField(  # 2026-02-19: Final 0-5 star rating
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )

    attempt_number = models.IntegerField(default=1)  # 2026-02-19: Attempt sequence
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-19: Timestamp

    class Meta:
        """2026-02-19: Model metadata."""

        ordering = ['-created_at']  # 2026-02-19: Newest first
        indexes = [  # 2026-02-19: Lookup indexes
            models.Index(fields=['student', 'lesson', 'day_number']),
        ]

    def __str__(self):
        """2026-02-19: String representation."""
        return (
            f"{self.student.full_name} – Day {self.day_number} "
            f"Attempt #{self.attempt_number} ({self.weighted_star_rating}★)"
        )


class ComprehensionQuestionResponse(models.Model):
    """
    2026-02-21: Per-question articulation response for marks-based comprehension (BS-CMP).

    Records one student attempt at a specific comprehension question within a lesson day.
    The LLM evaluates whether each key point was covered by the student's typed or spoken
    answer. Multiple attempts are allowed; the best (highest marks_awarded) is tracked.

    marks_available matches the 'marks' field of the question JSON (2, 3, or 5).
    marks_awarded = count of True values in key_points_covered.
    """

    INPUT_CHOICES = [  # 2026-02-21: How the student provided their answer
        ('typed', 'Typed'),
        ('spoken', 'Spoken'),
    ]

    id = models.UUIDField(  # 2026-02-21: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-21: Link to student
        Student, on_delete=models.CASCADE,
        related_name='comprehension_question_responses'
    )
    lesson = models.ForeignKey(  # 2026-02-21: Link to teaching lesson
        TeachingLesson, on_delete=models.CASCADE,
        related_name='comprehension_question_responses'
    )
    day_number = models.IntegerField(  # 2026-02-21: Day within the lesson (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    question_id = models.CharField(max_length=50)  # 2026-02-21: e.g. "D1_CQ1"
    question_text = models.TextField()  # 2026-02-21: Snapshot of the question text
    marks_available = models.IntegerField()  # 2026-02-21: 2, 3, or 5

    student_text = models.TextField()  # 2026-02-21: Typed or speech-to-text answer
    input_method = models.CharField(  # 2026-02-21: How the answer was provided
        max_length=10, choices=INPUT_CHOICES, default='typed'
    )

    key_points_covered = models.JSONField(default=list)  # 2026-02-21: e.g. [True, False, True]
    marks_awarded = models.IntegerField(default=0)  # 2026-02-21: sum(key_points_covered)
    llm_feedback = models.TextField(default='')  # 2026-02-21: One encouraging sentence
    llm_error = models.BooleanField(default=False)  # 2026-02-21: True if LLM call failed

    attempt_number = models.IntegerField(default=1)  # 2026-02-21: Attempt sequence
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-21: Timestamp

    class Meta:
        """2026-02-21: Model metadata."""

        ordering = ['-created_at']  # 2026-02-21: Newest first
        indexes = [  # 2026-02-21: Lookup indexes
            models.Index(fields=['student', 'lesson', 'day_number', 'question_id']),
        ]

    def __str__(self):
        """2026-02-21: String representation."""
        return (
            f"{self.student.full_name} – {self.question_id} "
            f"Attempt #{self.attempt_number} ({self.marks_awarded}/{self.marks_available})"
        )
