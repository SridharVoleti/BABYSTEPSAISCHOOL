"""
2026-03-02: Database models for Language Stages Service (BS-LNG-005).

Purpose:
    Enable Michel Thomas Stage 3 AI-driven conversational role-play.
    Stores scenarios (20 seeded), per-session records, per-turn transcripts,
    and per-student per-language progress.
"""

import uuid  # 2026-03-02: UUID primary keys

from django.db import models  # 2026-03-02: Django ORM
from django.core.validators import MinValueValidator, MaxValueValidator  # 2026-03-02: Validators

from services.auth_service.models import Student  # 2026-03-02: FK to student
from services.read_along_service.models import Language  # 2026-03-02: FK to language


class ConversationScenario(models.Model):
    """
    2026-03-02: A language conversation scenario (role-play context).

    20 universal scenarios seeded via migration 0002. Scenarios are
    language-agnostic; the {target_language} placeholder is filled at runtime.
    """

    DIFFICULTY_CHOICES = [  # 2026-03-02: Difficulty tiers
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(  # 2026-03-02: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    scenario_number = models.IntegerField(  # 2026-03-02: Ordering key (1-20)
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Sequence number 1-20; determines unlock order',
    )
    title = models.CharField(max_length=120)  # 2026-03-02: e.g. "At the Market"
    ai_persona = models.CharField(  # 2026-03-02: e.g. "shopkeeper"
        max_length=80,
        help_text='Role the AI plays in this scenario',
    )
    context_description = models.TextField(  # 2026-03-02: Scene-setting for LLM
        help_text='Paragraph describing the scenario context sent to LLM',
    )
    opening_prompt_template = models.TextField(  # 2026-03-02: AI first line
        help_text='Template for AI opening turn. Use {target_language} placeholder.',
    )
    difficulty = models.CharField(  # 2026-03-02: Difficulty level
        max_length=20, choices=DIFFICULTY_CHOICES, default='beginner'
    )
    min_turns = models.IntegerField(  # 2026-03-02: Minimum student turns to finish
        default=4, validators=[MinValueValidator(1)]
    )
    max_turns = models.IntegerField(  # 2026-03-02: Maximum turns before auto-close
        default=10, validators=[MinValueValidator(1)]
    )
    unlock_after_scenario = models.IntegerField(  # 2026-03-02: Prerequisite scenario number
        null=True, blank=True,
        help_text='This scenario unlocks after scenario N is completed at >= 2 stars. Null = always unlocked.',
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Created

    class Meta:
        """2026-03-02: Model metadata."""

        ordering = ['scenario_number']  # 2026-03-02: Natural display order

    def __str__(self):
        """2026-03-02: String representation."""
        return f"Scenario {self.scenario_number}: {self.title} ({self.difficulty})"


class ConversationSession(models.Model):
    """
    2026-03-02: One conversation session between a student and the AI.

    Created when student starts a scenario. Stores complexity, turn count,
    and final fluency star rating.
    """

    STATUS_CHOICES = [  # 2026-03-02: Session lifecycle
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    COMPLEXITY_CHOICES = [  # 2026-03-02: Complexity tier
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(  # 2026-03-02: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-02: Link to student
        Student, on_delete=models.CASCADE, related_name='conversation_sessions'
    )
    language = models.ForeignKey(  # 2026-03-02: Target language
        Language, on_delete=models.PROTECT, related_name='conversation_sessions'
    )
    scenario = models.ForeignKey(  # 2026-03-02: Scenario being played
        ConversationScenario, on_delete=models.PROTECT, related_name='sessions'
    )
    status = models.CharField(  # 2026-03-02: Session lifecycle
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    complexity_level = models.CharField(  # 2026-03-02: Complexity tier used
        max_length=20, choices=COMPLEXITY_CHOICES, default='beginner'
    )
    turn_count = models.IntegerField(default=0)  # 2026-03-02: Student turns completed
    fluency_star_rating = models.IntegerField(  # 2026-03-02: Final rating (0-5)
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    started_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Started
    completed_at = models.DateTimeField(null=True, blank=True)  # 2026-03-02: Finished

    class Meta:
        """2026-03-02: Model metadata."""

        ordering = ['-started_at']  # 2026-03-02: Newest first

    def __str__(self):
        """2026-03-02: String representation."""
        return (
            f"{self.student.full_name} — {self.scenario.title} "
            f"({self.language}) [{self.status}]"
        )


class ConversationTurn(models.Model):
    """
    2026-03-02: A single dialogue turn within a ConversationSession.

    Stores both student turns (with quality scores) and AI turns.
    """

    ROLE_CHOICES = [  # 2026-03-02: Who produced this turn
        ('student', 'Student'),
        ('ai', 'AI'),
    ]

    id = models.UUIDField(  # 2026-03-02: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-03-02: Parent session
        ConversationSession, on_delete=models.CASCADE, related_name='turns'
    )
    turn_number = models.IntegerField(  # 2026-03-02: Sequential turn index (1, 2, …)
        validators=[MinValueValidator(1)]
    )
    role = models.CharField(  # 2026-03-02: Who spoke
        max_length=10, choices=ROLE_CHOICES
    )
    text = models.TextField()  # 2026-03-02: What was said
    turn_quality_score = models.FloatField(  # 2026-03-02: LLM eval 0-1 (null for AI turns)
        null=True, blank=True,
        help_text='LLM-evaluated quality score (0.0-1.0) for student turns only',
    )
    recast_applied = models.BooleanField(  # 2026-03-02: AI implicitly corrected an error
        default=False
    )
    response_time_seconds = models.IntegerField(  # 2026-03-02: Student typing/speaking time
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Created

    class Meta:
        """2026-03-02: Model metadata."""

        unique_together = ['session', 'turn_number']  # 2026-03-02: One per slot
        ordering = ['turn_number']  # 2026-03-02: Sequential

    def __str__(self):
        """2026-03-02: String representation."""
        return f"Turn {self.turn_number} ({self.role}): {self.text[:40]}"


class StudentConversationProgress(models.Model):
    """
    2026-03-02: Aggregate conversational learning stats per student per language.

    One row per (student, language) pair. Tracks total scenarios completed,
    best stars per scenario, streaks, and total turns.
    """

    id = models.UUIDField(  # 2026-03-02: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-02: Link to student
        Student, on_delete=models.CASCADE, related_name='conversation_progress'
    )
    language = models.ForeignKey(  # 2026-03-02: Target language
        Language, on_delete=models.PROTECT, related_name='student_conversation_progress'
    )
    scenarios_completed = models.IntegerField(default=0)  # 2026-03-02: Total completed
    best_star_by_scenario = models.JSONField(  # 2026-03-02: {"1": 4, "2": 3, …}
        default=dict, blank=True,
        help_text='Maps scenario_number → best fluency_star_rating',
    )
    total_turns = models.IntegerField(default=0)  # 2026-03-02: Cumulative student turns
    current_streak_days = models.IntegerField(default=0)  # 2026-03-02: Daily streak
    last_session_date = models.DateField(null=True, blank=True)  # 2026-03-02: Last activity
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-03-02: Last updated

    class Meta:
        """2026-03-02: Model metadata."""

        unique_together = [['student', 'language']]  # 2026-03-02: One per pair
        ordering = ['-updated_at']  # 2026-03-02: Most recently active first

    def __str__(self):
        """2026-03-02: String representation."""
        return (
            f"{self.student.full_name} — {self.language} "
            f"({self.scenarios_completed} scenarios completed)"
        )
