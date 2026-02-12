"""Analytics Service Models - Consolidated

All models for analytics service including Phase 1 and Phase 2 features.

Date: December 12, 2025
Author: BabySteps Development Team
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


# Phase 1 Core Models
class StudentActivity(models.Model):
    """Tracks individual student learning activities."""
    
    ACTIVITY_TYPE_CHOICES = [
        ('lesson_view', 'Lesson View'),
        ('lesson_complete', 'Lesson Complete'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('quiz_complete', 'Quiz Complete'),
        ('practice', 'Practice Exercise'),
        ('video_watch', 'Video Watch'),
        ('reading', 'Reading Activity'),
        ('mentor_chat', 'Mentor Chat'),
        ('assessment', 'Assessment'),
        ('game', 'Educational Game'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPE_CHOICES, db_index=True)
    content_id = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    started_at = models.DateTimeField(db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    is_completed = models.BooleanField(default=False)
    engagement_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_student_activity'
        ordering = ['-started_at']
        verbose_name = 'Student Activity'
        verbose_name_plural = 'Student Activities'
        indexes = [
            models.Index(fields=['student', '-started_at'], name='activity_student_time_idx'),
            models.Index(fields=['content_type', 'content_id'], name='activity_content_idx'),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.activity_type}"


class StudentProgress(models.Model):
    """Tracks overall student progress per subject."""
    
    SUBJECT_CHOICES = [
        ('math', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('social_studies', 'Social Studies'),
        ('evs', 'Environmental Studies'),
        ('hindi', 'Hindi'),
        ('computer', 'Computer Science'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress_records')
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    grade_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    lessons_completed = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    lessons_total = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    skills_mastered = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    skills_total = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))])
    time_spent_minutes = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    last_activity_date = models.DateField(null=True, blank=True, db_index=True)
    streak_days = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_student_progress'
        ordering = ['student', 'subject']
        verbose_name = 'Student Progress'
        verbose_name_plural = 'Student Progress Records'
        unique_together = [['student', 'subject', 'grade_level']]
        indexes = [
            models.Index(fields=['student', 'subject'], name='progress_student_subject_idx'),
        ]
    
    def __str__(self):
        return f"{self.student.username} - {self.subject}"
    
    def completion_percentage(self):
        if self.lessons_total == 0:
            return 0
        return round((self.lessons_completed / self.lessons_total) * 100, 1)
    
    def mastery_percentage(self):
        if self.skills_total == 0:
            return 0
        return round((self.skills_mastered / self.skills_total) * 100, 1)


# Phase 1 advanced models - to be implemented
# from .mastery_models import Skill, Concept, StudentMastery, MasteryEvidence
# from .learning_style_detector import (
#     LearningStyleProfile, ContentInteractionPattern,
#     VisualLearningIndicator, AuditoryLearningIndicator,
#     KinestheticLearningIndicator, ReadingWritingIndicator
# )
# from .adaptive_difficulty import ContentDifficulty, DifficultyProfile, DifficultyAdjustment
# from .ai_assessment import AssessmentQuestion, StudentResponse, AssessmentSession, QuestionTemplate


# Phase 2: Teacher Dashboard Models
class Classroom(models.Model):
    """Classroom managed by a teacher."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classrooms')
    name = models.CharField(max_length=100)
    grade_level = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    academic_year = models.CharField(max_length=20, default='2025-2026')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_classroom'
        unique_together = [['teacher', 'name']]
        ordering = ['-created_at']
    
    @property
    def student_count(self):
        return self.enrollments.filter(is_active=True).count()


class ClassroomEnrollment(models.Model):
    """Student enrollment in classroom."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='enrollments')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='classroom_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'analytics_classroom_enrollment'
        unique_together = [['classroom', 'student']]


class StudentGroup(models.Model):
    """Group of students within a classroom."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='student_groups')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    group_type = models.CharField(max_length=20, default='custom')
    students = models.ManyToManyField(User, related_name='study_groups')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_student_group'


class Assignment(models.Model):
    """Assignment created by teacher."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    subject = models.CharField(max_length=100)
    assignment_type = models.CharField(max_length=20, default='homework')
    due_date = models.DateTimeField()
    total_points = models.IntegerField(default=100, validators=[MinValueValidator(1)])
    rubric = models.JSONField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_assignments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_assignment'


class AssignmentSubmission(models.Model):
    """Student submission for assignment."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignment_submissions')
    status = models.CharField(max_length=20, default='pending')
    submitted_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, validators=[MinValueValidator(0)])
    feedback = models.TextField(blank=True, null=True)
    graded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='graded_submissions')
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_assignment_submission'
        unique_together = [['assignment', 'student']]


class TeacherNote(models.Model):
    """Private notes about students."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notes')
    note_text = models.TextField()
    note_type = models.CharField(max_length=20, default='observation')
    is_private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_teacher_note'


class ResourceRecommendation(models.Model):
    """Resource recommendations for students."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_recommendations')
    recommended_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='made_recommendations')
    resource_type = models.CharField(max_length=30)
    resource_id = models.CharField(max_length=200)
    reason = models.TextField()
    priority = models.CharField(max_length=10, default='medium')
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_resource_recommendation'
