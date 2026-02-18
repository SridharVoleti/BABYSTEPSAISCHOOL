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
        ('mastery_practice', 'Mastery Practice'),  # 2026-02-17: Post-practice mastery session
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
    mastery_star_rating = models.IntegerField(  # 2026-02-17: Mastery practice star rating (0-5)
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    mastery_passed = models.BooleanField(default=False)  # 2026-02-17: Mastery gate passed (≥3 stars)
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


class PracticeSession(models.Model):
    """
    2026-02-17: Mastery practice session for a day's micro-lesson (BS-STR).

    After completing a day's 3 in-lesson practice questions, students enter
    an adaptive mastery practice session. Difficulty adapts based on
    consecutive correct/incorrect answers. Star rating (1-5) is awarded
    based on percentage correct.
    """

    STATUS_CHOICES = [  # 2026-02-17: Session status options
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    IQ_LEVEL_CHOICES = [  # 2026-02-17: IQ level tiers
        ('foundation', 'Foundation'),
        ('standard', 'Standard'),
        ('advanced', 'Advanced'),
    ]

    DIFFICULTY_CHOICES = [  # 2026-02-17: Difficulty levels
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-17: Link to student
        Student, on_delete=models.CASCADE, related_name='practice_sessions'
    )
    lesson_progress = models.ForeignKey(  # 2026-02-17: Parent lesson progress
        StudentLessonProgress, on_delete=models.CASCADE,
        related_name='practice_sessions'
    )
    day_number = models.IntegerField(  # 2026-02-17: Day (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    iq_level = models.CharField(  # 2026-02-17: Student's IQ level
        max_length=20, choices=IQ_LEVEL_CHOICES, default='standard'
    )
    status = models.CharField(  # 2026-02-17: Session lifecycle
        max_length=20, choices=STATUS_CHOICES, default='in_progress'
    )
    total_questions = models.IntegerField(default=0)  # 2026-02-17: Target question count
    questions_answered = models.IntegerField(default=0)  # 2026-02-17: Answered so far
    questions_correct = models.IntegerField(default=0)  # 2026-02-17: Correct so far
    current_difficulty = models.CharField(  # 2026-02-17: Current adaptive difficulty
        max_length=10, choices=DIFFICULTY_CHOICES, default='medium'
    )
    consecutive_correct = models.IntegerField(default=0)  # 2026-02-17: Streak for adaptation
    consecutive_incorrect = models.IntegerField(default=0)  # 2026-02-17: Streak for adaptation
    same_difficulty_streak = models.IntegerField(default=0)  # 2026-02-17: Same-difficulty counter
    star_rating = models.IntegerField(  # 2026-02-17: Final star rating (0-5)
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    percentage_correct = models.FloatField(default=0.0)  # 2026-02-17: Final percentage
    time_spent_seconds = models.IntegerField(default=0)  # 2026-02-17: Total time
    hints_used = models.IntegerField(default=0)  # 2026-02-17: Total hints used
    attempt_number = models.IntegerField(default=1)  # 2026-02-17: Attempt count
    administered_question_ids = models.JSONField(  # 2026-02-17: Track used question IDs
        default=list, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['lesson_progress', 'day_number', 'attempt_number']  # 2026-02-17: Unique attempt
        ordering = ['-created_at']  # 2026-02-17: Newest first

    def __str__(self):
        """2026-02-17: String representation."""
        return (
            f"Practice Day {self.day_number} Attempt #{self.attempt_number} "
            f"({self.star_rating} stars)"
        )


class PracticeResponse(models.Model):
    """
    2026-02-17: Individual question response within a mastery practice session.

    Records the student's answer, correctness, timing, and difficulty
    for each question in the adaptive practice session.
    """

    DIFFICULTY_CHOICES = [  # 2026-02-17: Difficulty levels
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    QUESTION_TYPE_CHOICES = [  # 2026-02-17: Question type options
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('numeric_fill', 'Numeric Fill'),
        ('drag_order', 'Drag and Order'),
    ]

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-02-17: Parent practice session
        PracticeSession, on_delete=models.CASCADE, related_name='responses'
    )
    question_id = models.CharField(max_length=100)  # 2026-02-17: Question identifier
    concept_id = models.CharField(max_length=100, blank=True)  # 2026-02-17: Concept identifier
    difficulty = models.CharField(  # 2026-02-17: Question difficulty
        max_length=10, choices=DIFFICULTY_CHOICES
    )
    question_type = models.CharField(  # 2026-02-17: Question type
        max_length=20, choices=QUESTION_TYPE_CHOICES, default='mcq'
    )
    student_answer = models.JSONField(  # 2026-02-17: Student's answer (any type)
        default=dict, blank=True
    )
    correct_answer = models.JSONField(  # 2026-02-17: Correct answer (any type)
        default=dict, blank=True
    )
    is_correct = models.BooleanField(default=False)  # 2026-02-17: Was answer correct
    time_taken_seconds = models.IntegerField(default=0)  # 2026-02-17: Time for this question
    hints_used = models.IntegerField(default=0)  # 2026-02-17: Hints for this question
    position = models.IntegerField(default=0)  # 2026-02-17: Position in session (0-indexed)
    feedback_text = models.TextField(blank=True, default='')  # 2026-02-17: Feedback shown
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['session', 'position']  # 2026-02-17: One per position
        ordering = ['position']  # 2026-02-17: Sequential

    def __str__(self):
        """2026-02-17: String representation."""
        status = "correct" if self.is_correct else "incorrect"  # 2026-02-17: Status text
        return f"Q{self.position + 1} ({self.difficulty}) - {status}"


class ConceptMastery(models.Model):
    """
    2026-02-17: Best mastery rating per student per lesson-day (BS-STR).

    Tracks the best star rating across all practice attempts. Used as
    the mastery gate: students need is_mastered=True (≥3 stars) to
    unlock the next day.
    """

    id = models.UUIDField(  # 2026-02-17: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-02-17: Link to student
        Student, on_delete=models.CASCADE, related_name='concept_masteries'
    )
    lesson = models.ForeignKey(  # 2026-02-17: Link to lesson
        TeachingLesson, on_delete=models.CASCADE, related_name='concept_masteries'
    )
    day_number = models.IntegerField(  # 2026-02-17: Day (1-4)
        validators=[MinValueValidator(1), MaxValueValidator(4)]
    )
    best_star_rating = models.IntegerField(  # 2026-02-17: Best star rating (0-5)
        default=0, validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    attempts_count = models.IntegerField(default=0)  # 2026-02-17: Total attempts
    is_mastered = models.BooleanField(default=False)  # 2026-02-17: True when ≥3 stars
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-17: Created
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-17: Last updated

    class Meta:
        """2026-02-17: Model metadata."""

        unique_together = ['student', 'lesson', 'day_number']  # 2026-02-17: One per combo
        ordering = ['day_number']  # 2026-02-17: By day

    def __str__(self):
        """2026-02-17: String representation."""
        mastered = "Mastered" if self.is_mastered else "Not mastered"  # 2026-02-17: Status
        return f"Day {self.day_number} - {self.best_star_rating} stars ({mastered})"
