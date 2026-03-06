"""
2026-03-06: Mentor Dashboard Service database models (BS-MNT).

Three models:
  - MentorAssignment: maps a staff user (mentor) to an assigned student
  - ComprehensionReview: mentor override score on a ComprehensionQuestionResponse
  - WeeklySummary: AI-generated weekly progress narrative per student per week
"""

import uuid  # 2026-03-06: UUID primary keys

from django.contrib.auth.models import User  # 2026-03-06: Django built-in user
from django.core.validators import MinValueValidator, MaxValueValidator  # 2026-03-06: Validators
from django.db import models  # 2026-03-06: Django ORM

from services.auth_service.models import Student  # 2026-03-06: Student FK
from services.comprehension_service.models import ComprehensionQuestionResponse  # 2026-03-06: Review target


class MentorAssignment(models.Model):
    """
    2026-03-06: Links a staff (mentor) user to an assigned student.

    A mentor may be assigned multiple students; a student may have multiple mentors.
    The unique_together constraint prevents duplicate (mentor, student) pairs.
    """

    id = models.UUIDField(  # 2026-03-06: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    mentor = models.ForeignKey(  # 2026-03-06: Staff user acting as mentor
        User,
        on_delete=models.CASCADE,
        related_name='mentor_assignments',
        limit_choices_to={'is_staff': True},
    )
    student = models.ForeignKey(  # 2026-03-06: Assigned student
        Student,
        on_delete=models.CASCADE,
        related_name='mentor_assignments',
    )
    assigned_at = models.DateTimeField(auto_now_add=True)  # 2026-03-06: Assignment timestamp
    is_active = models.BooleanField(default=True)  # 2026-03-06: Soft delete flag

    class Meta:
        """2026-03-06: Model metadata."""

        unique_together = ('mentor', 'student')  # 2026-03-06: No duplicate assignments
        ordering = ['-assigned_at']  # 2026-03-06: Newest first

    def __str__(self):
        """2026-03-06: String representation."""
        return f"Mentor {self.mentor.username} → {self.student.full_name}"


class ComprehensionReview(models.Model):
    """
    2026-03-06: Mentor override score for an AI-graded ComprehensionQuestionResponse.

    Mentors can spot-check low-scoring or LLM-error responses and assign
    a quality score (0=fail, 1-5=quality level) along with optional notes.
    unique_together prevents the same mentor from reviewing the same response twice.
    """

    id = models.UUIDField(  # 2026-03-06: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    response = models.ForeignKey(  # 2026-03-06: The comprehension response being reviewed
        ComprehensionQuestionResponse,
        on_delete=models.CASCADE,
        related_name='mentor_reviews',
    )
    reviewed_by = models.ForeignKey(  # 2026-03-06: Mentor who reviewed
        User,
        on_delete=models.CASCADE,
        related_name='comprehension_reviews',
        limit_choices_to={'is_staff': True},
    )
    mentor_score = models.IntegerField(  # 2026-03-06: 0=fail, 1-5=quality
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    mentor_notes = models.TextField(blank=True)  # 2026-03-06: Optional review notes
    reviewed_at = models.DateTimeField(auto_now_add=True)  # 2026-03-06: Review timestamp

    class Meta:
        """2026-03-06: Model metadata."""

        unique_together = ('response', 'reviewed_by')  # 2026-03-06: One review per mentor per response
        ordering = ['-reviewed_at']  # 2026-03-06: Newest first

    def __str__(self):
        """2026-03-06: String representation."""
        return (
            f"Review by {self.reviewed_by.username} on "
            f"{self.response_id} → score {self.mentor_score}"
        )


class WeeklySummary(models.Model):
    """
    2026-03-06: AI-generated weekly progress report for a student.

    Generated on-demand by a mentor or scheduled. Stores the narrative text
    plus structured strengths and areas_for_improvement lists.
    unique_together prevents duplicate summaries for the same week.
    """

    id = models.UUIDField(  # 2026-03-06: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-06: Which student this covers
        Student,
        on_delete=models.CASCADE,
        related_name='mentor_weekly_summaries',
    )
    week_start = models.DateField()  # 2026-03-06: Monday of the reported week
    summary_text = models.TextField()  # 2026-03-06: AI-generated narrative (≤200 words)
    strengths = models.JSONField(default=list)  # 2026-03-06: e.g. ["Strong in fractions"]
    areas_for_improvement = models.JSONField(default=list)  # 2026-03-06: e.g. ["Needs vocabulary work"]
    lessons_completed = models.IntegerField(default=0)  # 2026-03-06: Lessons finished this week
    avg_star_rating = models.FloatField(default=0.0)  # 2026-03-06: Mean star rating for the week
    generated_at = models.DateTimeField(auto_now_add=True)  # 2026-03-06: Creation timestamp
    generated_by = models.ForeignKey(  # 2026-03-06: Mentor who triggered generation
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='generated_summaries',
    )

    class Meta:
        """2026-03-06: Model metadata."""

        unique_together = ('student', 'week_start')  # 2026-03-06: One summary per student per week
        ordering = ['-week_start']  # 2026-03-06: Most recent first

    def __str__(self):
        """2026-03-06: String representation."""
        return f"Summary: {self.student.full_name} w/o {self.week_start}"
