"""
Teacher Dashboard Models

This module contains models for teacher dashboard features including:
- Classroom management
- Student grouping
- Assignments
- Teacher notes and recommendations

Author: BabySteps Development Team
Date: December 12, 2025
Version: 1.0
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

# Get the user model
User = get_user_model()


class Classroom(models.Model):
    """
    Model representing a classroom/class managed by a teacher.
    
    A classroom groups students for a specific subject and grade level.
    Teachers can create multiple classrooms and manage student enrollment.
    
    Fields:
        id: UUID primary key
        teacher: ForeignKey to User (teacher who created/manages classroom)
        name: Name of the classroom (e.g., "Class 1-A Morning Batch")
        grade_level: Grade level (e.g., "Class 1", "Class 2")
        subject: Subject taught (e.g., "Mathematics", "Science")
        academic_year: Academic year (e.g., "2025-2026")
        description: Optional description
        is_active: Whether classroom is currently active
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    
    Meta:
        unique_together: (teacher, name) - Each teacher's classrooms must have unique names
    """
    
    # UUID primary key for better security and scalability
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Teacher who manages this classroom
    teacher = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='classrooms',
        limit_choices_to={'is_staff': True}
    )
    
    # Classroom identification
    name = models.CharField(
        max_length=100,
        help_text="Name of the classroom (e.g., 'Class 1-A')"
    )
    
    # Academic details
    grade_level = models.CharField(
        max_length=50,
        help_text="Grade level (e.g., 'Class 1')"
    )
    
    subject = models.CharField(
        max_length=100,
        help_text="Subject taught in this classroom"
    )
    
    academic_year = models.CharField(
        max_length=20,
        default='2025-2026',
        help_text="Academic year (e.g., '2025-2026')"
    )
    
    # Additional information
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Description of the classroom"
    )
    
    # Status tracking
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the classroom is currently active"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Database table name
        db_table = 'analytics_classroom'
        
        # Ensure unique classroom names per teacher
        unique_together = [['teacher', 'name']]
        
        # Default ordering
        ordering = ['-created_at']
        
        # Indexes for performance
        indexes = [
            models.Index(fields=['teacher', 'is_active']),
            models.Index(fields=['grade_level', 'subject']),
        ]
    
    def __str__(self):
        """String representation of classroom."""
        return f"{self.name} - {self.subject} ({self.teacher.username})"
    
    @property
    def student_count(self):
        """Return count of enrolled students."""
        return self.enrollments.filter(is_active=True).count()


class ClassroomEnrollment(models.Model):
    """
    Model representing student enrollment in a classroom.
    
    Tracks which students are enrolled in which classrooms.
    Supports enrollment history with is_active flag.
    
    Fields:
        id: UUID primary key
        classroom: ForeignKey to Classroom
        student: ForeignKey to User (student)
        enrolled_at: When student was enrolled
        is_active: Whether enrollment is currently active
    """
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Classroom reference
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    
    # Student reference
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='classroom_enrollments'
    )
    
    # Enrollment tracking
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'analytics_classroom_enrollment'
        unique_together = [['classroom', 'student']]
        ordering = ['-enrolled_at']
        indexes = [
            models.Index(fields=['classroom', 'is_active']),
            models.Index(fields=['student', 'is_active']),
        ]
    
    def __str__(self):
        """String representation of enrollment."""
        return f"{self.student.username} in {self.classroom.name}"


class StudentGroup(models.Model):
    """
    Model representing a group of students within a classroom.
    
    Teachers can create groups for:
    - Ability-based grouping
    - Collaborative projects
    - Differentiated instruction
    - Small group activities
    
    Fields:
        id: UUID primary key
        classroom: ForeignKey to Classroom
        name: Group name
        description: Purpose/description of group
        group_type: Type of grouping (ability, project, random, etc.)
        created_by: Teacher who created the group
        created_at: Creation timestamp
    """
    
    GROUP_TYPES = [
        ('ability', 'Ability-Based'),
        ('project', 'Project Group'),
        ('random', 'Random Grouping'),
        ('custom', 'Custom Group'),
    ]
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Classroom reference
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='student_groups'
    )
    
    # Group details
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPES,
        default='custom'
    )
    
    # Students in this group (ManyToMany)
    students = models.ManyToManyField(
        User,
        related_name='study_groups'
    )
    
    # Creator tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_student_group'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['classroom', 'group_type']),
        ]
    
    def __str__(self):
        """String representation of group."""
        return f"{self.name} ({self.classroom.name})"


class Assignment(models.Model):
    """
    Model representing an assignment created by a teacher.
    
    Assignments can be:
    - Homework
    - Quizzes
    - Projects
    - Practice exercises
    
    Fields:
        id: UUID primary key
        classroom: ForeignKey to Classroom
        title: Assignment title
        description: Detailed description
        subject: Subject area
        assignment_type: Type of assignment
        due_date: When assignment is due
        total_points: Maximum points possible
        rubric: JSONField containing grading rubric
        created_by: Teacher who created assignment
        created_at: Creation timestamp
    """
    
    ASSIGNMENT_TYPES = [
        ('homework', 'Homework'),
        ('quiz', 'Quiz'),
        ('test', 'Test'),
        ('project', 'Project'),
        ('practice', 'Practice'),
    ]
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # Classroom reference
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assignment details
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.CharField(max_length=100)
    
    assignment_type = models.CharField(
        max_length=20,
        choices=ASSIGNMENT_TYPES,
        default='homework'
    )
    
    # Scheduling
    due_date = models.DateTimeField()
    
    # Grading
    total_points = models.IntegerField(
        default=100,
        validators=[MinValueValidator(1)]
    )
    
    # Rubric stored as JSON
    rubric = models.JSONField(
        blank=True,
        null=True,
        help_text="Grading rubric with criteria and points"
    )
    
    # Creator tracking
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_assignments'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_assignment'
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['classroom', 'due_date']),
            models.Index(fields=['created_by', 'assignment_type']),
        ]
    
    def __str__(self):
        """String representation of assignment."""
        return f"{self.title} ({self.classroom.name})"
    
    @property
    def is_overdue(self):
        """Check if assignment is past due date."""
        return timezone.now() > self.due_date


class AssignmentSubmission(models.Model):
    """
    Model representing a student's submission for an assignment.
    
    Tracks submission status, score, and feedback.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('late', 'Late Submission'),
    ]
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # References
    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assignment_submissions'
    )
    
    # Submission details
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    submitted_at = models.DateTimeField(null=True, blank=True)
    
    # Grading
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    
    feedback = models.TextField(blank=True, null=True)
    
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='graded_submissions'
    )
    
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_assignment_submission'
        unique_together = [['assignment', 'student']]
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['assignment', 'status']),
            models.Index(fields=['student', 'status']),
        ]
    
    def __str__(self):
        """String representation of submission."""
        return f"{self.student.username} - {self.assignment.title}"


class TeacherNote(models.Model):
    """
    Model representing private notes teachers can add about students.
    
    Used for tracking observations, interventions, and progress notes.
    """
    
    NOTE_TYPES = [
        ('observation', 'Observation'),
        ('intervention', 'Intervention'),
        ('achievement', 'Achievement'),
        ('concern', 'Concern'),
        ('general', 'General'),
    ]
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # References
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_notes'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_notes'
    )
    
    # Note details
    note_text = models.TextField()
    note_type = models.CharField(
        max_length=20,
        choices=NOTE_TYPES,
        default='general'
    )
    
    is_private = models.BooleanField(
        default=True,
        help_text="Whether note is visible only to teacher"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_teacher_note'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'created_by']),
            models.Index(fields=['note_type']),
        ]
    
    def __str__(self):
        """String representation of note."""
        return f"Note about {self.student.username} by {self.created_by.username}"


class ResourceRecommendation(models.Model):
    """
    Model representing resource recommendations from teachers to students.
    
    Teachers can recommend:
    - Additional practice materials
    - Video tutorials
    - Reading materials
    - External resources
    """
    
    RESOURCE_TYPES = [
        ('practice_worksheet', 'Practice Worksheet'),
        ('video', 'Video Tutorial'),
        ('reading', 'Reading Material'),
        ('interactive', 'Interactive Activity'),
        ('external', 'External Resource'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
    ]
    
    # UUID primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    # References
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resource_recommendations'
    )
    
    recommended_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='made_recommendations'
    )
    
    # Resource details
    resource_type = models.CharField(
        max_length=30,
        choices=RESOURCE_TYPES
    )
    
    resource_id = models.CharField(
        max_length=200,
        help_text="ID or reference to the resource"
    )
    
    reason = models.TextField(
        help_text="Why this resource is recommended"
    )
    
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_LEVELS,
        default='medium'
    )
    
    # Tracking
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_resource_recommendation'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        """String representation of recommendation."""
        return f"{self.resource_type} for {self.student.username}"
