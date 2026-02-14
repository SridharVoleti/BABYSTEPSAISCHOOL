# 2025-12-18: Learning Engine Models - Student Progress and Mastery Tracking
# Author: BabySteps Development Team
# Purpose: Django models for micro-lesson learning system
# Last Modified: 2025-12-18

"""
Learning Engine Models

This module defines the database models for:
- StudentProfile: Learning preferences and adaptive settings
- MicroLessonProgress: Track progress through individual micro-lessons
- PracticeAttempt: Record each practice question attempt
- MasteryScore: Track mastery per concept/lesson
- LearningStreak: Track daily learning consistency
- DifficultyCalibration: Store adaptive difficulty settings per student
"""

# 2025-12-18: Import Django ORM models
from django.db import models

# 2025-12-18: Import validators for field constraints
from django.core.validators import MinValueValidator, MaxValueValidator

# 2025-12-18: Import user model reference
from django.contrib.auth import get_user_model

# 2025-12-18: Import timezone utilities
from django.utils import timezone

# 2025-12-18: Import JSON field for storing structured data
from django.db.models import JSONField

# 2025-12-18: Get reference to User model
User = get_user_model()


class StudentLearningProfile(models.Model):
    """
    2025-12-18: Extended student profile for learning preferences and adaptive settings.
    
    Tracks:
    - Learning speed and patterns
    - Preferred explanation mode (visual/text)
    - Error pattern clusters
    - Weak concept areas
    """
    
    # 2025-12-18: Link to Django user
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='learning_profile',
        help_text="Associated user account"
    )
    
    # 2025-12-18: Learning speed classification
    LEARNING_SPEED_CHOICES = [
        ('slow', 'Slow Learner'),
        ('average', 'Average Learner'),
        ('fast', 'Fast Learner'),
    ]
    learning_speed = models.CharField(
        max_length=20,
        choices=LEARNING_SPEED_CHOICES,
        default='average',
        help_text="Calculated learning speed based on performance"
    )
    
    # 2025-12-18: Preferred explanation mode
    EXPLANATION_MODE_CHOICES = [
        ('visual', 'Visual First'),
        ('text', 'Text First'),
        ('mixed', 'Mixed Mode'),
    ]
    preferred_explanation_mode = models.CharField(
        max_length=20,
        choices=EXPLANATION_MODE_CHOICES,
        default='visual',
        help_text="Student's preferred way of receiving explanations"
    )
    
    # 2025-12-18: Error patterns stored as JSON
    error_patterns = JSONField(
        default=dict,
        blank=True,
        help_text="JSON tracking common error types and frequencies"
    )
    
    # 2025-12-18: Weak concept clusters
    weak_concepts = JSONField(
        default=list,
        blank=True,
        help_text="List of concept IDs where student struggles"
    )
    
    # 2025-12-18: Strong concept clusters
    strong_concepts = JSONField(
        default=list,
        blank=True,
        help_text="List of concept IDs where student excels"
    )
    
    # 2025-12-18: Total mastery points earned
    total_mastery_points = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cumulative mastery points across all lessons"
    )
    
    # 2025-12-18: Current streak count
    current_streak_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Current consecutive days of learning"
    )
    
    # 2025-12-18: Longest streak achieved
    longest_streak_days = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Longest streak ever achieved"
    )
    
    # 2025-12-18: Last activity date for streak calculation
    last_activity_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last learning activity"
    )
    
    # 2025-12-18: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Student Learning Profile"
        verbose_name_plural = "Student Learning Profiles"
    
    def __str__(self):
        # 2025-12-18: String representation
        return f"Learning Profile: {self.user.username}"
    
    def update_streak(self):
        """
        2025-12-18: Update streak based on current activity.
        Called when student completes any learning activity.
        """
        # 2025-12-18: Get today's date
        today = timezone.now().date()
        
        # 2025-12-18: Check if this is first activity
        if self.last_activity_date is None:
            self.current_streak_days = 1
            self.last_activity_date = today
            self.save()
            return
        
        # 2025-12-18: Calculate days since last activity
        days_diff = (today - self.last_activity_date).days
        
        # 2025-12-18: Same day - no streak change
        if days_diff == 0:
            return
        
        # 2025-12-18: Consecutive day - increment streak
        if days_diff == 1:
            self.current_streak_days += 1
            # 2025-12-18: Update longest streak if current exceeds it
            if self.current_streak_days > self.longest_streak_days:
                self.longest_streak_days = self.current_streak_days
        else:
            # 2025-12-18: Streak broken - reset to 1
            self.current_streak_days = 1
        
        # 2025-12-18: Update last activity date
        self.last_activity_date = today
        self.save()


class Lesson(models.Model):
    """
    2026-02-10: Main lesson container that must contain exactly 5 micro-lessons.
    
    Based on requirements analysis:
    - Each lesson MUST be divided into exactly 5 micro-lessons
    - Each micro-lesson contains: Concept, Example, Learner Action, AI Validation, Reinforcement
    - System rejects lessons not matching the 5 micro-lesson structure
    """
    
    # 2026-02-10: Unique lesson identifier
    lesson_id = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique lesson ID (e.g., ENG1_MRIDANG_01)"
    )
    
    # 2026-02-10: Lesson title
    title = models.CharField(
        max_length=200,
        help_text="Lesson title"
    )
    
    # 2026-02-10: Subject and class
    subject = models.CharField(
        max_length=50,
        help_text="Subject (Math, Science, English, etc.)"
    )
    class_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Class/Grade number (1-12)"
    )
    
    # 2026-02-10: Chapter information
    chapter_id = models.CharField(
        max_length=50,
        help_text="Chapter identifier"
    )
    chapter_name = models.CharField(
        max_length=200,
        help_text="Chapter name"
    )
    
    # 2026-02-10: Overall learning objectives
    learning_objectives = JSONField(
        default=list,
        help_text="List of learning objectives for this lesson"
    )
    
    # 2026-02-10: Total duration (sum of all micro-lessons)
    total_duration_minutes = models.IntegerField(
        default=35,
        help_text="Total duration for all 5 micro-lessons (typically 35-50 minutes)"
    )
    
    # 2026-02-10: Lesson status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ready', 'Ready for Teaching'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text="Lesson status"
    )
    
    # 2026-02-10: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lesson"
        verbose_name_plural = "Lessons"
    
    def __str__(self):
        return f"Lesson: {self.title} ({self.lesson_id})"
    
    def clean(self):
        """
        2026-02-10: Validate that this lesson has exactly 5 micro-lessons.
        This enforces the core requirement from the specifications.
        """
        from django.core.exceptions import ValidationError
        
        micro_lesson_count = self.micro_lessons.count()
        if micro_lesson_count != 5:
            raise ValidationError(
                f"Lesson must have exactly 5 micro-lessons, but has {micro_lesson_count}. "
                "Each lesson must be divided into exactly 5 micro-lessons as per requirements."
            )


class MicroLesson(models.Model):
    """
    2025-12-18: Represents a single micro-lesson unit (5-10 minutes).
    
    2026-02-10: Enhanced to enforce strict 5-part structure:
    Each micro-lesson MUST contain:
    1. Concept Explanation (≤120 words)
    2. Worked Example (step-by-step)
    3. Learner Action (active task)
    4. AI Validation (answer checking)
    5. Reinforcement Summary (≤50 words)
    """
    
    # 2026-02-10: Link to parent lesson (optional for migration)
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name='micro_lessons',
        null=True,
        blank=True,
        help_text="Parent lesson that contains this micro-lesson"
    )
    
    # 2026-02-10: Sequence within lesson (1-5)
    sequence_in_lesson = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
        help_text="Sequence of this micro-lesson within the lesson (1-5)"
    )
    
    # 2026-02-10: Unique micro-lesson identifier
    micro_lesson_id = models.CharField(
        max_length=100,
        unique=True,
        default='',
        help_text="Unique micro-lesson ID (e.g., MATH_C5_CH3_ML2)"
    )
    
    # 2026-02-10: Micro-lesson title
    title = models.CharField(
        max_length=200,
        help_text="Micro-lesson title"
    )
    
    # 2026-02-10: PART 1: Concept Explanation (≤120 words)
    concept_explanation = models.TextField(
        max_length=800,  # ~120 words max
        blank=True,
        default="",
        help_text="Clear concept explanation in ≤120 words, age-appropriate, jargon-free"
    )
    
    # 2026-02-10: PART 2: Worked Example (step-by-step)
    worked_example = JSONField(
        default=dict,
        blank=True,
        help_text="Worked example with problem statement and step-by-step solution"
    )
    
    # 2026-02-10: PART 3: Learner Action (active task)
    learner_action = JSONField(
        default=dict,
        blank=True,
        help_text="Active learning task aligned to the concept"
    )
    
    # 2026-02-10: PART 4: AI Validation Logic
    validation_logic = JSONField(
        default=dict,
        blank=True,
        help_text="AI validation rules and feedback logic"
    )
    
    # 2026-02-10: PART 5: Reinforcement Summary (≤50 words)
    reinforcement_summary = models.TextField(
        max_length=350,  # ~50 words max
        blank=True,
        default="",
        help_text="Concise reinforcement summary restating core idea (≤50 words)"
    )
    
    # 2026-02-10: Duration in minutes (5-10)
    duration_minutes = models.IntegerField(
        default=7,
        validators=[MinValueValidator(5), MaxValueValidator(10)],
        help_text="Expected duration in minutes (5-10)"
    )
    
    # 2026-02-10: Supporting assets (optional)
    visual_assets = JSONField(
        default=list,
        blank=True,
        help_text="Supporting visual assets for this micro-lesson"
    )
    
    # 2026-02-10: Difficulty level
    DIFFICULTY_CHOICES = [
        ('support', 'Support Level'),
        ('core', 'Core Level'),
        ('challenge', 'Challenge Level'),
    ]
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='core',
        help_text="Difficulty level for adaptive learning"
    )
    
    # 2025-12-18: QA status
    QA_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('passed', 'QA Passed'),
        ('failed', 'QA Failed'),
        ('revision', 'Under Revision'),
    ]
    qa_status = models.CharField(
        max_length=20,
        choices=QA_STATUS_CHOICES,
        default='pending',
        help_text="Academic QA status"
    )
    qa_passed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when QA was passed"
    )
    qa_notes = models.TextField(
        blank=True,
        help_text="QA reviewer notes"
    )
    
    # 2025-12-18: Version tracking
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Lesson version for auditability"
    )
    
    # 2025-12-18: Localization
    language = models.CharField(
        max_length=20,
        default="en",
        help_text="Primary language code"
    )
    localization_variants = JSONField(
        default=dict,
        blank=True,
        help_text="Localized content variants (Telugu, Hindi, etc.)"
    )
    
    # 2025-12-18: Publishing status
    is_published = models.BooleanField(
        default=False,
        help_text="Whether lesson is published and visible to students"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Publication timestamp"
    )
    
    # 2025-12-18: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_microlessons',
        help_text="Agent or user who created this lesson"
    )
    
    class Meta:
        verbose_name = "Micro-Lesson"
        verbose_name_plural = "Micro-Lessons"
        ordering = ['lesson', 'sequence_in_lesson']
        indexes = [
            models.Index(fields=['micro_lesson_id']),
            models.Index(fields=['lesson', 'sequence_in_lesson']),
            models.Index(fields=['qa_status', 'is_published']),
        ]
        unique_together = [
            ['lesson', 'sequence_in_lesson'],
        ]
    
    def __str__(self):
        # 2025-12-18: String representation
        return f"{self.lesson_id}: {self.title}"
    
    def validate_structure(self):
        """
        2026-02-10: Validate micro-lesson meets 5-part structure requirements.
        Returns tuple (is_valid, errors_list).
        """
        errors = []
        
        # 2026-02-10: Check concept explanation length (≤120 words)
        concept_word_count = len(self.concept_explanation.split())
        if concept_word_count > 120:
            errors.append(f"Concept explanation must be ≤120 words, found {concept_word_count}")
        
        # 2026-02-10: Check worked example structure
        if not self.worked_example or 'problem' not in self.worked_example or 'solution_steps' not in self.worked_example:
            errors.append("Worked example must contain 'problem' and 'solution_steps'")
        
        # 2026-02-10: Check learner action structure
        if not self.learner_action or 'task' not in self.learner_action:
            errors.append("Learner action must contain a 'task'")
        
        # 2026-02-10: Check validation logic structure
        if not self.validation_logic or 'rules' not in self.validation_logic:
            errors.append("Validation logic must contain 'rules'")
        
        # 2026-02-10: Check reinforcement summary length (≤50 words)
        reinforcement_word_count = len(self.reinforcement_summary.split())
        if reinforcement_word_count > 50:
            errors.append(f"Reinforcement summary must be ≤50 words, found {reinforcement_word_count}")
        
        # 2026-02-10: Check sequence is within 1-5
        if not (1 <= self.sequence_in_lesson <= 5):
            errors.append(f"Sequence must be 1-5, found {self.sequence_in_lesson}")
        
        return len(errors) == 0, errors
    
    def clean(self):
        """
        2026-02-10: Django model validation.
        """
        from django.core.exceptions import ValidationError
        
        is_valid, errors = self.validate_structure()
        if not is_valid:
            raise ValidationError({
                'structure': errors
            })


class MicroLessonProgress(models.Model):
    """
    2025-12-18: Track student progress through a micro-lesson.
    
    Records:
    - Current step in lesson flow
    - Practice question attempts
    - Mastery score achieved
    - Time spent
    - Completion status
    """
    
    # 2025-12-18: Link to student
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='lesson_progress',
        help_text="Student taking the lesson"
    )
    
    # 2025-12-18: Link to micro-lesson
    micro_lesson = models.ForeignKey(
        MicroLesson,
        on_delete=models.CASCADE,
        related_name='student_progress',
        help_text="The micro-lesson being tracked"
    )
    
    # 2025-12-18: Progress status
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('mastered', 'Mastered'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        help_text="Current progress status"
    )
    
    # 2025-12-18: Current step in lesson flow
    STEP_CHOICES = [
        ('objective', 'Viewing Objective'),
        ('visual_intro', 'Visual Introduction'),
        ('worked_example_1', 'Worked Example 1'),
        ('worked_example_2', 'Worked Example 2'),
        ('practice', 'Practice Questions'),
        ('mastery_check', 'Mastery Checkpoint'),
        ('completed', 'Completed'),
    ]
    current_step = models.CharField(
        max_length=30,
        choices=STEP_CHOICES,
        default='objective',
        help_text="Current step in lesson flow"
    )
    
    # 2025-12-18: Practice progress
    questions_attempted = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Number of practice questions attempted"
    )
    questions_correct = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        help_text="Number of practice questions answered correctly"
    )
    
    # 2025-12-18: Mastery score (0-100)
    mastery_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Mastery score percentage (0-100)"
    )
    
    # 2025-12-18: Time tracking
    time_spent_seconds = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Total time spent on this lesson in seconds"
    )
    
    # 2025-12-18: Attempt tracking
    attempt_number = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Which attempt this is (for retries)"
    )
    
    # 2025-12-18: Difficulty level experienced
    DIFFICULTY_CHOICES = [
        ('support', 'Support Level'),
        ('core', 'Core Level'),
        ('challenge', 'Challenge Level'),
    ]
    difficulty_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='core',
        help_text="Difficulty level student experienced"
    )
    
    # 2025-12-18: Hints used
    hints_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of hints requested"
    )
    
    # 2025-12-18: Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When student started this lesson"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When student completed this lesson"
    )
    
    # 2025-12-18: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Micro-Lesson Progress"
        verbose_name_plural = "Micro-Lesson Progress Records"
        # 2025-12-18: Unique per student per lesson per attempt
        unique_together = ['student', 'micro_lesson', 'attempt_number']
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['student', 'status']),
            models.Index(fields=['micro_lesson', 'status']),
        ]
    
    def __str__(self):
        # 2025-12-18: String representation
        return f"{self.student.username} - {self.micro_lesson.lesson_id} ({self.status})"
    
    def calculate_mastery(self):
        """
        2025-12-18: Calculate mastery score based on performance.
        Factors: accuracy, time, hints used.
        """
        # 2025-12-18: Base score from accuracy
        if self.questions_attempted == 0:
            # 2025-12-18: No attempts means no mastery score
            self.mastery_score = 0
            return self.mastery_score
        
        accuracy_score = (self.questions_correct / self.questions_attempted) * 70
        
        # 2025-12-18: Time bonus (up to 20 points for fast completion)
        expected_time = self.micro_lesson.duration_minutes * 60  # Convert to seconds
        if self.time_spent_seconds <= expected_time:
            time_score = 20
        elif self.time_spent_seconds <= expected_time * 1.5:
            time_score = 10
        else:
            time_score = 0
        
        # 2025-12-18: Hint penalty (lose up to 10 points)
        hint_penalty = min(self.hints_used * 2, 10)
        
        # 2025-12-18: Calculate final mastery score
        self.mastery_score = max(0, min(100, int(accuracy_score + time_score - hint_penalty)))
        return self.mastery_score


class PracticeAttempt(models.Model):
    """
    2025-12-18: Record each practice question attempt for detailed analytics.
    
    Tracks:
    - Question answered
    - Student's answer
    - Correctness
    - Time taken
    - Hints used
    """
    
    # 2025-12-18: Link to lesson progress
    lesson_progress = models.ForeignKey(
        MicroLessonProgress,
        on_delete=models.CASCADE,
        related_name='practice_attempts',
        help_text="Associated lesson progress record"
    )
    
    # 2025-12-18: Question index (1-10)
    question_index = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Question number (1-10)"
    )
    
    # 2025-12-18: Question content snapshot
    question_content = JSONField(
        help_text="Snapshot of question at time of attempt"
    )
    
    # 2025-12-18: Student's answer
    student_answer = models.TextField(
        help_text="Student's submitted answer"
    )
    
    # 2025-12-18: Correct answer
    correct_answer = models.TextField(
        help_text="The correct answer"
    )
    
    # 2025-12-18: Result
    is_correct = models.BooleanField(
        help_text="Whether the answer was correct"
    )
    
    # 2025-12-18: Partial credit (for multi-step problems)
    partial_credit = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Partial credit awarded (0.0 to 1.0)"
    )
    
    # 2025-12-18: Time taken
    time_taken_seconds = models.IntegerField(
        validators=[MinValueValidator(0)],
        help_text="Time taken to answer in seconds"
    )
    
    # 2025-12-18: Hints used for this question
    hints_used = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of hints used for this question"
    )
    
    # 2025-12-18: Retry count
    retry_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Number of retries for this question"
    )
    
    # 2025-12-18: Feedback shown
    feedback_shown = JSONField(
        default=dict,
        blank=True,
        help_text="Feedback displayed to student"
    )
    
    # 2025-12-18: Misconception detected
    misconception_detected = models.CharField(
        max_length=200,
        blank=True,
        help_text="Misconception identified from wrong answer"
    )
    
    # 2025-12-18: Timestamp
    attempted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Practice Attempt"
        verbose_name_plural = "Practice Attempts"
        ordering = ['lesson_progress', 'question_index', 'attempted_at']
        indexes = [
            models.Index(fields=['lesson_progress', 'question_index']),
            models.Index(fields=['is_correct']),
        ]
    
    def __str__(self):
        # 2025-12-18: String representation
        result = "✓" if self.is_correct else "✗"
        return f"Q{self.question_index} {result} - {self.lesson_progress}"


class DifficultyCalibration(models.Model):
    """
    2025-12-18: Store adaptive difficulty settings per student per subject.
    
    Tracks:
    - Accuracy history
    - Average time to solve
    - Retry patterns
    - Current difficulty level
    """
    
    # 2025-12-18: Link to student
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='difficulty_calibrations',
        help_text="Student being calibrated"
    )
    
    # 2025-12-18: Subject for calibration
    subject = models.CharField(
        max_length=50,
        help_text="Subject for this calibration"
    )
    
    # 2025-12-18: Current difficulty level
    DIFFICULTY_CHOICES = [
        ('support', 'Support Level'),
        ('core', 'Core Level'),
        ('challenge', 'Challenge Level'),
    ]
    current_difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='core',
        help_text="Current difficulty level for this student/subject"
    )
    
    # 2025-12-18: Rolling accuracy (last 20 questions)
    rolling_accuracy = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Rolling accuracy over last 20 questions"
    )
    
    # 2025-12-18: Average time per question (seconds)
    avg_time_per_question = models.FloatField(
        default=60.0,
        validators=[MinValueValidator(0.0)],
        help_text="Average time per question in seconds"
    )
    
    # 2025-12-18: Average retries per question
    avg_retries = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0)],
        help_text="Average retries per question"
    )
    
    # 2025-12-18: History for calculations
    recent_attempts = JSONField(
        default=list,
        help_text="Last 20 attempt results for rolling calculations"
    )
    
    # 2025-12-18: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Difficulty Calibration"
        verbose_name_plural = "Difficulty Calibrations"
        unique_together = ['student', 'subject']
    
    def __str__(self):
        # 2025-12-18: String representation
        return f"{self.student.username} - {self.subject}: {self.current_difficulty}"
    
    def recalibrate(self):
        """
        2025-12-18: Recalibrate difficulty based on recent performance.
        
        Rules (Duolingo-inspired):
        - High accuracy (>80%) + fast time → increase difficulty
        - Low accuracy (<50%) or many retries → decrease difficulty
        - Otherwise maintain current level
        """
        # 2025-12-18: Check if enough data
        if len(self.recent_attempts) < 5:
            return self.current_difficulty
        
        # 2025-12-18: Calculate metrics from recent attempts
        correct_count = sum(1 for a in self.recent_attempts if a.get('is_correct', False))
        self.rolling_accuracy = correct_count / len(self.recent_attempts)
        
        times = [a.get('time_seconds', 60) for a in self.recent_attempts]
        self.avg_time_per_question = sum(times) / len(times)
        
        retries = [a.get('retries', 0) for a in self.recent_attempts]
        self.avg_retries = sum(retries) / len(retries)
        
        # 2025-12-18: Apply calibration rules
        if self.rolling_accuracy > 0.8 and self.avg_time_per_question < 45:
            # 2025-12-18: Student is excelling - increase difficulty
            if self.current_difficulty == 'support':
                self.current_difficulty = 'core'
            elif self.current_difficulty == 'core':
                self.current_difficulty = 'challenge'
        elif self.rolling_accuracy < 0.5 or self.avg_retries > 2:
            # 2025-12-18: Student is struggling - decrease difficulty
            if self.current_difficulty == 'challenge':
                self.current_difficulty = 'core'
            elif self.current_difficulty == 'core':
                self.current_difficulty = 'support'
        
        self.save()
        return self.current_difficulty
    
    def add_attempt(self, is_correct, time_seconds, retries=0):
        """
        2025-12-18: Add a new attempt to the rolling history.
        Keeps only last 20 attempts.
        """
        # 2025-12-18: Create attempt record
        attempt = {
            'is_correct': is_correct,
            'time_seconds': time_seconds,
            'retries': retries,
            'timestamp': timezone.now().isoformat()
        }
        
        # 2025-12-18: Add to list and trim to 20
        self.recent_attempts.append(attempt)
        if len(self.recent_attempts) > 20:
            self.recent_attempts = self.recent_attempts[-20:]
        
        # 2025-12-18: Recalibrate after adding
        self.recalibrate()
