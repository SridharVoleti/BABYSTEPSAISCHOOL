"""
2026-03-02: Math Service database models (BS-MTH module).

Purpose:
    Store math lesson metadata, practice sessions per student,
    and individual problem attempt records. Content (problems + solutions)
    lives in JSON files; only tracking data is stored in DB.
"""

import uuid  # 2026-03-02: UUID primary keys

from django.db import models  # 2026-03-02: Django ORM

from services.auth_service.models import Student  # 2026-03-02: Cross-service FK


class MathLesson(models.Model):
    """
    2026-03-02: Metadata record for a math lesson week.

    Points to the JSON file containing problems and worked solutions.
    Actual content is loaded from content_json_path at runtime.
    """

    STATUS_CHOICES = [  # 2026-03-02: Lesson lifecycle
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    lesson_id = models.CharField(  # 2026-03-02: e.g. 'MATH1_W01'
        max_length=50, unique=True,
        help_text='Unique lesson identifier, e.g. MATH1_W01'
    )
    title = models.CharField(max_length=200)  # 2026-03-02: Human-readable title
    class_number = models.IntegerField(  # 2026-03-02: Grade 1-12
        help_text='Class/grade number (1-12)'
    )
    week_number = models.IntegerField(  # 2026-03-02: Week within the class
        help_text='Week number within the class curriculum'
    )
    topic = models.CharField(max_length=200)  # 2026-03-02: Topic description
    content_json_path = models.CharField(  # 2026-03-02: Relative path to JSON
        max_length=300,
        help_text='Relative path from project root to lesson JSON, e.g. json/math/class1/week1.json'
    )
    status = models.CharField(  # 2026-03-02: draft or published
        max_length=20, choices=STATUS_CHOICES, default='draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Creation timestamp
    updated_at = models.DateTimeField(auto_now=True)  # 2026-03-02: Last update timestamp

    class Meta:
        """2026-03-02: Model metadata."""
        ordering = ['class_number', 'week_number']  # 2026-03-02: Natural ordering

    def __str__(self):
        """2026-03-02: String representation."""
        return f"{self.lesson_id}: {self.title}"  # 2026-03-02: Display


class MathSession(models.Model):
    """
    2026-03-02: Tracks one student's math practice session for a specific day.

    A session is tied to a lesson + day combination. The student
    works through problems loaded from the lesson's JSON file.
    Star rating is computed when the session completes.
    """

    IQ_LEVEL_CHOICES = [  # 2026-03-02: IQ placement levels
        ('foundation', 'Foundation'),
        ('standard', 'Standard'),
        ('advanced', 'Advanced'),
    ]

    STATUS_CHOICES = [  # 2026-03-02: Session lifecycle
        ('active', 'Active'),
        ('completed', 'Completed'),
    ]

    id = models.UUIDField(  # 2026-03-02: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-02: FK to student
        Student, on_delete=models.CASCADE, related_name='math_sessions'
    )
    lesson = models.ForeignKey(  # 2026-03-02: FK to lesson
        MathLesson, on_delete=models.CASCADE, related_name='sessions'
    )
    day_number = models.IntegerField(  # 2026-03-02: Day 1-4
        help_text='Day number within the lesson (1-4)'
    )
    iq_level = models.CharField(  # 2026-03-02: Student IQ level
        max_length=20, choices=IQ_LEVEL_CHOICES, default='standard'
    )
    status = models.CharField(  # 2026-03-02: Session status
        max_length=20, choices=STATUS_CHOICES, default='active'
    )
    total_problems = models.IntegerField(default=0)  # 2026-03-02: Total problems in session
    problems_correct = models.IntegerField(default=0)  # 2026-03-02: Correct answers count
    star_rating = models.IntegerField(  # 2026-03-02: 0-5 stars (null until complete)
        null=True, blank=True,
        help_text='Star rating 0-5, set when session completes'
    )
    started_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Session start
    completed_at = models.DateTimeField(  # 2026-03-02: Session end (null while active)
        null=True, blank=True
    )

    class Meta:
        """2026-03-02: Model metadata."""
        ordering = ['-started_at']  # 2026-03-02: Newest first

    def __str__(self):
        """2026-03-02: String representation."""
        return f"Session {self.id} | {self.student} | {self.lesson.lesson_id} Day {self.day_number}"


class MathProblemAttempt(models.Model):
    """
    2026-03-02: Records one student answer attempt for a single math problem.

    Links back to a MathSession. The problem content is identified by
    problem_id (from JSON). Feedback comes from the evaluator.
    """

    id = models.UUIDField(  # 2026-03-02: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-03-02: FK to session
        MathSession, on_delete=models.CASCADE, related_name='attempts'
    )
    problem_id = models.CharField(  # 2026-03-02: JSON problem ID
        max_length=100,
        help_text='Problem identifier from the JSON content file'
    )
    problem_type = models.CharField(  # 2026-03-02: mcq, numeric_fill, word_problem
        max_length=50,
        help_text='Problem type: mcq, numeric_fill, word_problem'
    )
    student_answer = models.TextField()  # 2026-03-02: Raw student answer
    is_correct = models.BooleanField(default=False)  # 2026-03-02: Evaluation result
    hints_used = models.IntegerField(default=0)  # 2026-03-02: Hint requests count
    feedback = models.TextField(blank=True, default='')  # 2026-03-02: Evaluator feedback
    time_taken_seconds = models.IntegerField(  # 2026-03-02: Time spent (optional)
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Attempt timestamp

    class Meta:
        """2026-03-02: Model metadata."""
        ordering = ['created_at']  # 2026-03-02: Chronological order

    def __str__(self):
        """2026-03-02: String representation."""
        result = 'correct' if self.is_correct else 'incorrect'  # 2026-03-02: Result label
        return f"Attempt {self.problem_id} ({result})"


class MathDrillSession(models.Model):
    """
    2026-03-03: Mental Maths Drill session (AMT-APE-005).

    Stores a timed drill session for multiplication tables, squares, or cubes.
    All questions are generated algorithmically at session start and stored here
    so the server is the authoritative source of truth.
    """

    DRILL_TYPE_CHOICES = [  # 2026-03-03: Drill type options
        ('tables', 'Multiplication Tables'),
        ('squares', 'Squares'),
        ('cubes', 'Cubes'),
    ]

    STATUS_CHOICES = [  # 2026-03-03: Session lifecycle
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('expired', 'Expired'),
    ]

    id = models.UUIDField(  # 2026-03-03: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.ForeignKey(  # 2026-03-03: FK to student
        Student, on_delete=models.CASCADE, related_name='drill_sessions'
    )
    drill_type = models.CharField(  # 2026-03-03: tables, squares, cubes
        max_length=20, choices=DRILL_TYPE_CHOICES
    )
    number_range_min = models.IntegerField(default=1)  # 2026-03-03: Range lower bound
    number_range_max = models.IntegerField(default=12)  # 2026-03-03: Range upper bound
    time_limit_seconds = models.IntegerField()  # 2026-03-03: 30, 60, or 120
    total_questions = models.IntegerField(default=10)  # 2026-03-03: Questions in session
    status = models.CharField(  # 2026-03-03: Session status
        max_length=20, choices=STATUS_CHOICES, default='active'
    )
    score = models.IntegerField(default=0)  # 2026-03-03: Correct answers count
    star_rating = models.IntegerField(  # 2026-03-03: 0-5 stars (null until complete)
        null=True, blank=True,
        help_text='Star rating 0-5, set when session completes or expires'
    )
    questions = models.JSONField(  # 2026-03-03: [{id, question, correct_answer}]
        default=list,
        help_text='Generated questions list with correct_answer (server-side only)'
    )
    started_at = models.DateTimeField(auto_now_add=True)  # 2026-03-03: Session start
    completed_at = models.DateTimeField(  # 2026-03-03: Session end (null while active)
        null=True, blank=True
    )

    class Meta:
        """2026-03-03: Model metadata."""
        ordering = ['-started_at']  # 2026-03-03: Newest first

    def __str__(self):
        """2026-03-03: String representation."""
        return f"Drill {self.id} | {self.student} | {self.drill_type} | {self.status}"


class MathDrillAttempt(models.Model):
    """
    2026-03-03: Records one student answer attempt for a single drill question.

    Links back to a MathDrillSession. Each question index can only be
    answered once per session.
    """

    id = models.UUIDField(  # 2026-03-03: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    session = models.ForeignKey(  # 2026-03-03: FK to drill session
        MathDrillSession, on_delete=models.CASCADE, related_name='attempts'
    )
    question_index = models.IntegerField(  # 2026-03-03: 0-based index in session.questions
        help_text='0-based index of the question in the session questions list'
    )
    student_answer = models.CharField(max_length=50)  # 2026-03-03: Raw student answer
    is_correct = models.BooleanField(default=False)  # 2026-03-03: Evaluation result
    response_time_ms = models.IntegerField(  # 2026-03-03: Time in ms (optional)
        null=True, blank=True,
        help_text='Time taken to answer in milliseconds (optional)'
    )
    answered_at = models.DateTimeField(auto_now_add=True)  # 2026-03-03: Attempt timestamp

    class Meta:
        """2026-03-03: Model metadata."""
        ordering = ['answered_at']  # 2026-03-03: Chronological order
        unique_together = [('session', 'question_index')]  # 2026-03-03: One attempt per question

    def __str__(self):
        """2026-03-03: String representation."""
        result = 'correct' if self.is_correct else 'incorrect'  # 2026-03-03: Result label
        return f"DrillAttempt Q{self.question_index} ({result})"


class MathTutoringSession(models.Model):
    """
    2026-03-02: AI Math Tutor teaching session (BS-AMT-001).

    One tutoring session per MathSession. The AI tutor teaches the concept
    using the day's teaching_summary and worked_examples from the JSON before
    the student attempts practice problems. Stores the full conversation
    so the student can scroll back and re-read the tutor's explanation.
    """

    id = models.UUIDField(  # 2026-03-02: UUID PK
        primary_key=True, default=uuid.uuid4, editable=False
    )
    math_session = models.OneToOneField(  # 2026-03-02: One tutoring session per practice session
        MathSession, on_delete=models.CASCADE, related_name='tutoring'
    )
    messages = models.JSONField(  # 2026-03-02: [{role, text, ts}] conversation log
        default=list,
        help_text='Ordered list of {role: tutor|student, text, ts} dicts'
    )
    teaching_complete = models.BooleanField(  # 2026-03-02: True when student clicks Ready
        default=False,
        help_text='Set True when student signals ready to practice'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-03-02: Session start
    updated_at = models.DateTimeField(auto_now=True)  # 2026-03-02: Last message timestamp

    class Meta:
        """2026-03-02: Model metadata."""
        db_table = 'math_tutoring_session'  # 2026-03-02: Explicit table name

    def __str__(self):
        """2026-03-02: String representation."""
        status = 'complete' if self.teaching_complete else 'in-progress'  # 2026-03-02: Status
        return f"Teaching {self.math_session.lesson.lesson_id} Day {self.math_session.day_number} ({status})"
