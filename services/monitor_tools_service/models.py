"""
2026-03-04: Monitor Tools Service models (BS-MON-005/006/007).

Three sub-modules:
  - BS-MON-005: GradeBookEntry — per-student, per-subject, per-term grade recording
  - BS-MON-006: HomeworkAssignment + HomeworkSubmission — teacher assigns; parent acknowledges
  - BS-MON-007: TimetableSlot — per-grade weekly timetable managed by monitors
"""

import uuid  # 2026-03-04: UUID primary keys

from django.contrib.auth.models import User  # 2026-03-04: Monitor = staff User
from django.db import models  # 2026-03-04: Django ORM

from services.auth_service.models import Student  # 2026-03-04: Student FK


# ============================================================
# BS-MON-005: Grade Book
# ============================================================

class GradeBookEntry(models.Model):
    """
    2026-03-04: One grade entry per student per subject per term.

    Monitors record a numeric score (0-100) plus an optional letter grade.
    Both formative (periodic) and summative (exam) assessments are tracked.
    """

    TERM_1 = 'T1'  # 2026-03-04: April-July
    TERM_2 = 'T2'  # 2026-03-04: August-November
    TERM_3 = 'T3'  # 2026-03-04: December-March

    TERM_CHOICES = [
        (TERM_1, 'Term 1'),
        (TERM_2, 'Term 2'),
        (TERM_3, 'Term 3'),
    ]

    TYPE_FORMATIVE = 'formative'   # 2026-03-04: Classwork/quiz
    TYPE_SUMMATIVE = 'summative'   # 2026-03-04: Exam/assessment
    TYPE_PROJECT   = 'project'     # 2026-03-04: Project/assignment

    TYPE_CHOICES = [
        (TYPE_FORMATIVE, 'Formative'),
        (TYPE_SUMMATIVE, 'Summative'),
        (TYPE_PROJECT,   'Project'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(  # 2026-03-04: Target student
        Student, on_delete=models.CASCADE, related_name='grade_entries', db_index=True
    )
    subject = models.CharField(max_length=50, db_index=True)  # 2026-03-04: e.g. 'Science'
    term = models.CharField(max_length=2, choices=TERM_CHOICES)  # 2026-03-04: Academic term
    assessment_type = models.CharField(  # 2026-03-04: Formative / summative
        max_length=12, choices=TYPE_CHOICES, default=TYPE_FORMATIVE
    )
    title = models.CharField(max_length=100)  # 2026-03-04: e.g. 'Chapter 3 Quiz'
    score = models.FloatField()  # 2026-03-04: Raw score (0-100)
    max_score = models.FloatField(default=100.0)  # 2026-03-04: Maximum possible score
    letter_grade = models.CharField(  # 2026-03-04: A+/A/B/C/D/F (computed or manual)
        max_length=3, blank=True, default=''
    )
    remarks = models.TextField(blank=True, default='')  # 2026-03-04: Teacher comments
    recorded_by = models.ForeignKey(  # 2026-03-04: Monitor who entered the grade
        User, on_delete=models.SET_NULL, null=True, related_name='grade_entries_recorded'
    )
    date_recorded = models.DateField()  # 2026-03-04: Assessment date
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """2026-03-04: Model metadata."""
        ordering = ['-date_recorded', 'subject']
        indexes = [models.Index(fields=['student', 'subject', 'term'])]

    def __str__(self):
        return f'{self.student.full_name} | {self.subject} | {self.term} | {self.score}'

    @property
    def percentage(self) -> float:
        """2026-03-04: Score as percentage of max_score."""
        if self.max_score == 0:
            return 0.0
        return round(self.score / self.max_score * 100, 1)

    def save(self, *args, **kwargs):
        """2026-03-04: Auto-compute letter grade if blank."""
        if not self.letter_grade:
            pct = self.percentage
            if pct >= 90:
                self.letter_grade = 'A+'
            elif pct >= 80:
                self.letter_grade = 'A'
            elif pct >= 70:
                self.letter_grade = 'B'
            elif pct >= 60:
                self.letter_grade = 'C'
            elif pct >= 50:
                self.letter_grade = 'D'
            else:
                self.letter_grade = 'F'
        super().save(*args, **kwargs)


# ============================================================
# BS-MON-006: Homework
# ============================================================

class HomeworkAssignment(models.Model):
    """
    2026-03-04: A homework task assigned to a grade by a monitor.

    Parents view their child's homework; students see it in the app.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.IntegerField(db_index=True)  # 2026-03-04: Target class (1-12)
    subject = models.CharField(max_length=50)   # 2026-03-04: e.g. 'Maths'
    title = models.CharField(max_length=200)    # 2026-03-04: Short title
    description = models.TextField()            # 2026-03-04: Full task description
    due_date = models.DateField()               # 2026-03-04: Submission deadline
    assigned_by = models.ForeignKey(            # 2026-03-04: Monitor who created it
        User, on_delete=models.SET_NULL, null=True, related_name='homework_assigned'
    )
    is_active = models.BooleanField(default=True)  # 2026-03-04: Can be hidden
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """2026-03-04: Model metadata."""
        ordering = ['due_date', 'subject']

    def __str__(self):
        return f'Grade {self.grade} | {self.subject} | {self.title} (due {self.due_date})'


class HomeworkSubmission(models.Model):
    """
    2026-03-04: Parent/student acknowledgement that homework was completed.

    Simple yes/no completion flag + optional note. No file upload (v1).
    """

    STATUS_PENDING = 'pending'       # 2026-03-04: Not yet acted on
    STATUS_DONE    = 'done'          # 2026-03-04: Parent marked done
    STATUS_MISSED  = 'missed'        # 2026-03-04: System marks missed after due_date

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_DONE,    'Done'),
        (STATUS_MISSED,  'Missed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    homework = models.ForeignKey(  # 2026-03-04: Assignment FK
        HomeworkAssignment, on_delete=models.CASCADE, related_name='submissions'
    )
    student = models.ForeignKey(   # 2026-03-04: Student who submitted
        Student, on_delete=models.CASCADE, related_name='homework_submissions'
    )
    status = models.CharField(     # 2026-03-04: Completion status
        max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    note = models.TextField(blank=True, default='')  # 2026-03-04: Parent's note
    submitted_at = models.DateTimeField(null=True, blank=True)  # 2026-03-04: When marked done
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """2026-03-04: Model metadata."""
        unique_together = ('homework', 'student')  # 2026-03-04: One per student per assignment
        ordering = ['-created_at']


# ============================================================
# BS-MON-007: Timetable
# ============================================================

class TimetableSlot(models.Model):
    """
    2026-03-04: One class slot in the weekly timetable for a grade.

    Repeats weekly. Monitors create/update slots for their class.
    """

    DAY_MONDAY    = 1
    DAY_TUESDAY   = 2
    DAY_WEDNESDAY = 3
    DAY_THURSDAY  = 4
    DAY_FRIDAY    = 5
    DAY_SATURDAY  = 6

    DAY_CHOICES = [
        (DAY_MONDAY,    'Monday'),
        (DAY_TUESDAY,   'Tuesday'),
        (DAY_WEDNESDAY, 'Wednesday'),
        (DAY_THURSDAY,  'Thursday'),
        (DAY_FRIDAY,    'Friday'),
        (DAY_SATURDAY,  'Saturday'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grade = models.IntegerField(db_index=True)        # 2026-03-04: Class (1-12)
    day_of_week = models.IntegerField(choices=DAY_CHOICES)  # 2026-03-04: Mon=1 … Sat=6
    start_time = models.TimeField()                   # 2026-03-04: HH:MM
    end_time = models.TimeField()                     # 2026-03-04: HH:MM
    subject = models.CharField(max_length=50)         # 2026-03-04: e.g. 'Mathematics'
    teacher_name = models.CharField(max_length=100, blank=True, default='')  # 2026-03-04: Optional
    room = models.CharField(max_length=50, blank=True, default='')           # 2026-03-04: Optional
    is_active = models.BooleanField(default=True)     # 2026-03-04: Soft-delete
    created_by = models.ForeignKey(                   # 2026-03-04: Monitor who created
        User, on_delete=models.SET_NULL, null=True, related_name='timetable_slots_created'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """2026-03-04: Model metadata."""
        ordering = ['grade', 'day_of_week', 'start_time']
        indexes = [models.Index(fields=['grade', 'day_of_week'])]

    def __str__(self):
        day_name = dict(self.DAY_CHOICES).get(self.day_of_week, str(self.day_of_week))
        return f'Grade {self.grade} | {day_name} {self.start_time}-{self.end_time} | {self.subject}'
