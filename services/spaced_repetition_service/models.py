"""
2026-02-27: Database models for Spaced Repetition Service (BS-SPC).

Purpose:
    Define the Leitner box records, review sessions, individual review
    responses, and intensive-phase pacing records for spaced repetition.
"""

import uuid  # 2026-02-27: UUID primary keys
from datetime import date  # 2026-02-27: Date arithmetic for property

from django.db import models  # 2026-02-27: Django ORM

from services.auth_service.models import Student  # 2026-02-27: Cross-app FK
from services.teaching_engine.models import ConceptMastery  # 2026-02-27: Mastery FK


class SpacedRepetitionRecord(models.Model):
    """
    2026-02-27: Tracks when to review a mastered concept (Leitner box system).

    One record per student-mastery pair. Advances through boxes 1-5 on
    5-star reviews; resets to box 1 on failure (< 3 stars). After three
    consecutive 5-star reviews in box 5, transitions to maintenance phase.
    """

    PHASE_CHOICES = [  # 2026-02-27: Phase of spaced repetition
        ('spaced_repetition', 'Spaced Repetition'),
        ('maintenance', 'Maintenance'),
    ]

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-27: Link to student
        Student,
        on_delete=models.CASCADE,
        related_name='spc_records',
    )
    mastery = models.ForeignKey(  # 2026-02-27: Link to concept mastery record
        ConceptMastery,
        on_delete=models.CASCADE,
        related_name='spc_record',
    )
    box = models.IntegerField(default=1)  # 2026-02-27: Leitner box number (1-5)
    next_review_date = models.DateField()  # 2026-02-27: Scheduled review date
    last_reviewed_at = models.DateTimeField(  # 2026-02-27: Timestamp of last review
        null=True, blank=True
    )
    consecutive_5star_reviews = models.IntegerField(default=0)  # 2026-02-27: Streak tracker
    phase = models.CharField(  # 2026-02-27: Current phase
        max_length=20,
        choices=PHASE_CHOICES,
        default='spaced_repetition',
    )
    review_count = models.IntegerField(default=0)  # 2026-02-27: Total reviews completed
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-27: Last updated

    class Meta:
        """2026-02-27: Model metadata."""

        unique_together = [['student', 'mastery']]  # 2026-02-27: One record per combo
        ordering = ['next_review_date']  # 2026-02-27: Soonest due first

    def __str__(self):
        """2026-02-27: String representation."""
        return (
            f"{self.student.full_name} - Box {self.box} "
            f"(due {self.next_review_date})"
        )


class ReviewSession(models.Model):
    """
    2026-02-27: One review sitting for a student.

    Created when a student starts their daily review queue.
    Completed when the student finishes or exits the session.
    """

    STATUS_CHOICES = [  # 2026-02-27: Session lifecycle
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-27: Link to student
        Student,
        on_delete=models.CASCADE,
        related_name='review_sessions',
    )
    status = models.CharField(  # 2026-02-27: Session status
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
    )
    concepts_reviewed = models.IntegerField(default=0)  # 2026-02-27: Count of reviewed items
    started_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Session start
    completed_at = models.DateTimeField(  # 2026-02-27: Session end
        null=True, blank=True
    )

    class Meta:
        """2026-02-27: Model metadata."""

        ordering = ['-started_at']  # 2026-02-27: Most recent first

    def __str__(self):
        """2026-02-27: String representation."""
        return (
            f"{self.student.full_name} review session "
            f"({self.concepts_reviewed} concepts, {self.status})"
        )


class ReviewResponse(models.Model):
    """
    2026-02-27: One concept reviewed within a ReviewSession.

    Records the star rating, explanation time, and outcome (advanced/reset)
    for each concept reviewed in a sitting.
    """

    OUTCOME_CHOICES = [  # 2026-02-27: Review outcome
        ('advanced', 'Advanced'),
        ('reset', 'Reset'),
    ]

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-02-27: Parent review session
        ReviewSession,
        on_delete=models.CASCADE,
        related_name='responses',
    )
    mastery = models.ForeignKey(  # 2026-02-27: Concept mastery reviewed
        ConceptMastery,
        on_delete=models.CASCADE,
        related_name='review_responses',
    )
    stars_awarded = models.IntegerField()  # 2026-02-27: 0-5 star rating
    explanation_seconds = models.IntegerField(default=0)  # 2026-02-27: Explanation time
    outcome = models.CharField(  # 2026-02-27: Result of this review
        max_length=10,
        choices=OUTCOME_CHOICES,
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Created

    class Meta:
        """2026-02-27: Model metadata."""

        ordering = ['created_at']  # 2026-02-27: Chronological

    def __str__(self):
        """2026-02-27: String representation."""
        return (
            f"Review {self.outcome} - {self.stars_awarded} stars "
            f"({self.explanation_seconds}s)"
        )


class PacingRecord(models.Model):
    """
    2026-02-27: One per student — tracks intensive phase pacing.

    Stores the academic year start, intensive period end, total concepts
    for the grade, and the IQ-adjusted daily target. Used to compute
    whether the student is ahead, on-track, or behind pace.
    """

    PHASE_CHOICES = [  # 2026-02-27: Pacing phase
        ('intensive', 'Intensive'),
        ('spaced_repetition', 'Spaced Repetition'),
    ]

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.OneToOneField(  # 2026-02-27: One record per student
        Student,
        on_delete=models.CASCADE,
        related_name='pacing_record',
    )
    academic_year_start = models.DateField()  # 2026-02-27: June 1 of the academic year
    intensive_end_date = models.DateField()  # 2026-02-27: academic_year_start + 112 days
    total_concepts = models.IntegerField(default=0)  # 2026-02-27: Published lessons × 4
    daily_target = models.IntegerField(default=1)  # 2026-02-27: IQ-adjusted daily goal
    iq_adjustment_factor = models.FloatField(default=1.0)  # 2026-02-27: IQ multiplier
    completed_concepts = models.IntegerField(default=0)  # 2026-02-27: Denormalized mastery count
    phase = models.CharField(  # 2026-02-27: Current learning phase
        max_length=20,
        choices=PHASE_CHOICES,
        default='intensive',
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-27: Last updated

    class Meta:
        """2026-02-27: Model metadata."""

        # 2026-02-27: No ordering needed; always queried by student (unique)

    @property
    def expected_concepts_to_date(self):
        """2026-02-27: Compute how many concepts should have been mastered by today."""
        today = date.today()
        days_elapsed = max(0, (today - self.academic_year_start).days)
        return min(self.total_concepts, days_elapsed * self.daily_target)

    def __str__(self):
        """2026-02-27: String representation."""
        return (
            f"{self.student.full_name} pacing "
            f"(target {self.daily_target}/day, {self.phase})"
        )
