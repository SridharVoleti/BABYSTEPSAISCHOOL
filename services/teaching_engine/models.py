"""
2026-02-17: AI Teaching Engine models.

Purpose:
    Define database models for the AI Teaching Engine (BS-AIE).
    Covers teaching lessons (weekly containers), student progress,
    per-day micro-lesson tracking, weekly assessments, and tutoring sessions.
"""

import uuid  # 2026-02-17: UUID for primary keys

from django.db import models  # 2026-02-17: Django ORM
from django.core.validators import MinValueValidator, MaxValueValidator  # 2026-02-17: Validators

from services.auth_service.models import Student  # 2026-02-17: Cross-app FK


class TeachingLesson(models.Model):
    """
    2026-02-17: Week-level lesson container.

    Maps to one content JSON file. Contains 4 micro-lessons (Days 1-4)
    and a Day 5 weekly assessment. All subjects follow the same structure.
    """

    STATUS_CHOICES = [  # 2026-02-17: Lesson status options
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    lesson_id = models.CharField(  # 2026-02-17: Unique lesson identifier
        max_length=100, unique=True,
        help_text='e.g. ENG1_MRIDANG_W01'
    )
    title = models.CharField(max_length=200)  # 2026-02-17: Lesson title
    subject = models.CharField(max_length=50)  # 2026-02-17: Subject name
    class_number = models.IntegerField(  # 2026-02-17: Grade/class (1-12)
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    chapter_id = models.CharField(max_length=50, blank=True)  # 2026-02-17: Chapter ID
    chapter_title = models.CharField(max_length=200, blank=True)  # 2026-02-17: Chapter name
    week_number = models.IntegerField(  # 2026-02-17: Week number in sequence
        validators=[MinValueValidator(1)]
    )
    character_name = models.CharField(  # 2026-02-17: AI persona name
        max_length=100, blank=True, default=''
    )
    learning_objectives = models.JSONField(  # 2026-02-17: List of objectives
        default=list, blank=True
    )
    content_json_path = models.CharField(  # 2026-02-17: Path to JSON file
        max_length=500,
        help_text='Relative path from project root to content JSON'
    )
    content_hash = models.CharField(  # 2026-02-17: SHA256 for cache invalidation
        max_length=64, blank=True, default=''
    )
    status = models.CharField(  # 2026-02-17: Publication status
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        ordering = ['class_number', 'subject', 'week_number']  # 2026-02-17: Natural order
        indexes = [  # 2026-02-17: Lookup index
            models.Index(fields=['class_number', 'subject']),
        ]

    def __str__(self):
        """2026-02-17: String representation."""
        return f"{self.lesson_id}: {self.title}"


class StudentLessonProgress(models.Model):
    """
    2026-02-17: Tracks a student's journey through a teaching lesson (week).

    Records which day the student is on, IQ level used for personalization,
    day completion statuses, and final assessment results.
    """

    STATUS_CHOICES = [  # 2026-02-17: Progress status options
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    IQ_LEVEL_CHOICES = [  # 2026-02-17: IQ level tiers
        ('foundation', 'Foundation'),
        ('standard', 'Standard'),
        ('advanced', 'Advanced'),
    ]

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-17: Link to student
        Student, on_delete=models.CASCADE, related_name='teaching_progress'
    )
    lesson = models.ForeignKey(  # 2026-02-17: Link to lesson
        TeachingLesson, on_delete=models.CASCADE, related_name='student_progress'
    )
    iq_level = models.CharField(  # 2026-02-17: Personalization tier
        max_length=20, choices=IQ_LEVEL_CHOICES, default='standard'
    )
    current_day = models.IntegerField(  # 2026-02-17: Current day (1-5)
        default=1, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    day_statuses = models.JSONField(  # 2026-02-17: Per-day statuses
        default=dict, blank=True,
        help_text='e.g. {"1":"completed","2":"in_progress","3":"not_started"}'
    )
    total_score = models.IntegerField(default=0)  # 2026-02-17: Cumulative practice score
    assessment_score = models.IntegerField(  # 2026-02-17: Day 5 assessment score
        null=True, blank=True
    )
    assessment_star_rating = models.IntegerField(  # 2026-02-17: Stars (0-3)
        default=0, validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    status = models.CharField(  # 2026-02-17: Overall progress status
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    started_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: First interaction
    completed_at = models.DateTimeField(  # 2026-02-17: Completion timestamp
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['student', 'lesson']  # 2026-02-17: One progress per student-lesson
        ordering = ['-updated_at']  # 2026-02-17: Most recent first

    def __str__(self):
        """2026-02-17: String representation."""
        return f"{self.student.full_name} - {self.lesson.lesson_id} (Day {self.current_day})"


class DayProgress(models.Model):
    """
    2026-02-17: Tracks progress for a single day's micro-lesson.

    Days 1-4 each have their own progress record tracking revision,
    teaching, practice, and completion status.
    """

    STATUS_CHOICES = [  # 2026-02-17: Day progress status options
        ('not_started', 'Not Started'),
        ('revision', 'In Revision'),
        ('teaching', 'In Teaching'),
        ('practice', 'In Practice'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    lesson_progress = models.ForeignKey(  # 2026-02-17: Parent progress
        StudentLessonProgress, on_delete=models.CASCADE, related_name='day_records'
    )
    day_number = models.IntegerField(  # 2026-02-17: Day (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    status = models.CharField(  # 2026-02-17: Day lifecycle
        max_length=20, choices=STATUS_CHOICES, default='not_started'
    )
    revision_completed = models.BooleanField(default=False)  # 2026-02-17: Revision done
    practice_score = models.IntegerField(default=0)  # 2026-02-17: Practice quiz score
    questions_attempted = models.IntegerField(default=0)  # 2026-02-17: Questions tried
    questions_correct = models.IntegerField(default=0)  # 2026-02-17: Questions right
    time_spent_seconds = models.IntegerField(default=0)  # 2026-02-17: Time on this day
    hints_used = models.IntegerField(default=0)  # 2026-02-17: Hints requested
    started_at = models.DateTimeField(null=True, blank=True)  # 2026-02-17: Day started
    completed_at = models.DateTimeField(null=True, blank=True)  # 2026-02-17: Day completed
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['lesson_progress', 'day_number']  # 2026-02-17: One per day
        ordering = ['day_number']  # 2026-02-17: Chronological

    def __str__(self):
        """2026-02-17: String representation."""
        return f"Day {self.day_number} ({self.status})"


class WeeklyAssessmentAttempt(models.Model):
    """
    2026-02-17: Records a Day 5 weekly assessment attempt.

    Students take a quiz covering all 4 micro-lessons.
    Star rating (0-3) awarded based on score thresholds.
    """

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    lesson_progress = models.ForeignKey(  # 2026-02-17: Parent progress
        StudentLessonProgress, on_delete=models.CASCADE,
        related_name='assessment_attempts'
    )
    attempt_number = models.IntegerField(default=1)  # 2026-02-17: Attempt count
    answers = models.JSONField(  # 2026-02-17: Student answers
        default=dict, blank=True,
        help_text='e.g. {"WA_Q1": 0, "WA_Q2": 2}'
    )
    score = models.IntegerField(default=0)  # 2026-02-17: Points earned
    total_points = models.IntegerField(default=0)  # 2026-02-17: Max points
    star_rating = models.IntegerField(  # 2026-02-17: Stars awarded (0-3)
        default=0, validators=[MinValueValidator(0), MaxValueValidator(3)]
    )
    time_spent_seconds = models.IntegerField(default=0)  # 2026-02-17: Time taken
    submitted_at = models.DateTimeField(  # 2026-02-17: Submission time
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['lesson_progress', 'attempt_number']  # 2026-02-17: Unique attempt
        ordering = ['-attempt_number']  # 2026-02-17: Latest first

    def __str__(self):
        """2026-02-17: String representation."""
        return f"Assessment attempt #{self.attempt_number} ({self.star_rating} stars)"


class TutoringSession(models.Model):
    """
    2026-02-17: Records AI tutoring conversations during lessons (BS-AIE-002).

    Stores the full conversation log between student and AI mentor,
    including lesson context. Messages are stored as a JSON array.
    """

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-17: Link to student
        Student, on_delete=models.CASCADE, related_name='tutoring_sessions'
    )
    lesson_progress = models.ForeignKey(  # 2026-02-17: Lesson context (optional)
        StudentLessonProgress, on_delete=models.CASCADE,
        related_name='tutoring_sessions', null=True, blank=True
    )
    day_number = models.IntegerField(  # 2026-02-17: Day when chat happened
        null=True, blank=True
    )
    messages = models.JSONField(  # 2026-02-17: Conversation log
        default=list, blank=True,
        help_text='[{"role":"student","text":"...","ts":"..."},{"role":"mentor",...}]'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        ordering = ['-created_at']  # 2026-02-17: Newest first

    def __str__(self):
        """2026-02-17: String representation."""
        msg_count = len(self.messages) if self.messages else 0  # 2026-02-17: Count
        return f"Tutoring ({msg_count} messages)"
