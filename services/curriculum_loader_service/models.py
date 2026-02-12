# 2025-10-31: Curriculum Loader Service Models
# Author: BabySteps Development Team
# Purpose: Define data models for curriculum management
# Last Modified: 2025-10-31

"""
Curriculum Loader Service Models

This module defines the database models for managing curriculum metadata,
lesson tracking, and content organization.
"""

from django.db import models  # 2025-10-31: Import Django ORM models
from django.core.validators import MinValueValidator, MaxValueValidator  # 2025-10-31: Import validators
from django.contrib.auth import get_user_model  # 2025-10-31: Get user model reference

User = get_user_model()  # 2025-10-31: Reference to custom user model


class CurriculumMetadata(models.Model):
    """
    2025-10-31: Model to store metadata about curriculum structure
    Tracks available classes, subjects, and content organization
    """
    
    # 2025-10-31: Primary identification fields
    class_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Class number (1-12)"
    )
    subject = models.CharField(
        max_length=50,
        help_text="Subject name (e.g., EVS, Math, Science)"
    )
    
    # 2025-10-31: Content organization fields
    total_months = models.IntegerField(
        default=10,
        help_text="Total number of months in curriculum"
    )
    total_weeks = models.IntegerField(
        default=40,
        help_text="Total number of weeks in curriculum"
    )
    total_lessons = models.IntegerField(
        default=0,
        help_text="Total number of lesson files"
    )
    total_question_banks = models.IntegerField(
        default=0,
        help_text="Total number of question bank files"
    )
    
    # 2025-10-31: Curriculum path and version tracking
    curriculum_path = models.CharField(
        max_length=500,
        help_text="Relative path to curriculum folder"
    )
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Curriculum version"
    )
    academic_year = models.CharField(
        max_length=20,
        default="2025-2026",
        help_text="Academic year"
    )
    
    # 2025-10-31: Status and tracking fields
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this curriculum is currently active"
    )
    is_frozen = models.BooleanField(
        default=False,
        help_text="Whether this curriculum is frozen (no edits allowed)"
    )
    last_validated = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time curriculum was validated"
    )
    
    # 2025-10-31: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_curriculums'
    )
    
    class Meta:
        # 2025-10-31: Ensure unique combination of class and subject
        unique_together = ['class_number', 'subject']
        verbose_name = "Curriculum Metadata"
        verbose_name_plural = "Curriculum Metadata"
        ordering = ['class_number', 'subject']
    
    def __str__(self):
        # 2025-10-31: String representation
        return f"Class {self.class_number} - {self.subject} ({self.academic_year})"


class LessonFile(models.Model):
    """
    2025-10-31: Model to track individual lesson JSON files
    Stores metadata and file path for each lesson
    """
    
    # 2025-10-31: Link to curriculum metadata
    curriculum = models.ForeignKey(
        CurriculumMetadata,
        on_delete=models.CASCADE,
        related_name='lesson_files'
    )
    
    # 2025-10-31: Lesson identification fields
    lesson_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique lesson ID (e.g., SCI_C1_M1_W1_D1)"
    )
    lesson_title = models.CharField(
        max_length=200,
        help_text="Lesson title"
    )
    
    # 2025-10-31: Temporal organization fields
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month number (1-12)"
    )
    week = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(52)],
        help_text="Week number (1-52)"
    )
    day = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(7)],
        help_text="Day number (1-7)"
    )
    
    # 2025-10-31: File and content fields
    file_path = models.CharField(
        max_length=500,
        help_text="Relative path to lesson JSON file"
    )
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    
    # 2025-10-31: Lesson metadata fields
    duration_minutes = models.IntegerField(
        default=30,
        help_text="Expected lesson duration in minutes"
    )
    level = models.CharField(
        max_length=50,
        choices=[
            ('Foundational', 'Foundational'),
            ('Challenge', 'Challenge'),
            ('Olympiad', 'Olympiad')
        ],
        default='Foundational',
        help_text="Lesson difficulty level"
    )
    version = models.CharField(
        max_length=20,
        default="1.0",
        help_text="Lesson version"
    )
    
    # 2025-10-31: Language support fields
    languages = models.JSONField(
        default=list,
        help_text="List of supported languages"
    )
    
    # 2025-10-31: Content structure fields
    has_tts = models.BooleanField(
        default=False,
        help_text="Whether lesson has TTS content"
    )
    has_activities = models.BooleanField(
        default=False,
        help_text="Whether lesson has activities"
    )
    has_ai_coach = models.BooleanField(
        default=False,
        help_text="Whether lesson has AI expression coach"
    )
    has_question_bank = models.BooleanField(
        default=False,
        help_text="Whether lesson has associated question bank"
    )
    
    # 2025-10-31: Validation and status fields
    is_validated = models.BooleanField(
        default=False,
        help_text="Whether lesson JSON has been validated"
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation errors if any"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this lesson is currently active"
    )
    
    # 2025-10-31: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time lesson was accessed"
    )
    access_count = models.IntegerField(
        default=0,
        help_text="Number of times lesson has been accessed"
    )
    
    class Meta:
        # 2025-10-31: Ensure unique lesson IDs
        unique_together = ['curriculum', 'month', 'week', 'day']
        verbose_name = "Lesson File"
        verbose_name_plural = "Lesson Files"
        ordering = ['curriculum', 'month', 'week', 'day']
        indexes = [
            models.Index(fields=['lesson_id']),
            models.Index(fields=['curriculum', 'month', 'week', 'day']),
        ]
    
    def __str__(self):
        # 2025-10-31: String representation
        return f"{self.lesson_id}: {self.lesson_title}"


class QuestionBankFile(models.Model):
    """
    2025-10-31: Model to track question bank JSON files
    Stores metadata and file path for each question bank
    """
    
    # 2025-10-31: Link to lesson file
    lesson = models.OneToOneField(
        LessonFile,
        on_delete=models.CASCADE,
        related_name='question_bank'
    )
    
    # 2025-10-31: Question bank identification
    qb_id = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique question bank ID (e.g., SCI_C1_M1_W1_D1_QB)"
    )
    
    # 2025-10-31: File fields
    file_path = models.CharField(
        max_length=500,
        help_text="Relative path to question bank JSON file"
    )
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    
    # 2025-10-31: Question bank metadata
    total_questions = models.IntegerField(
        default=0,
        help_text="Total number of questions in bank"
    )
    question_types = models.JSONField(
        default=list,
        help_text="List of question types (MCQ, True/False, etc.)"
    )
    difficulty_levels = models.JSONField(
        default=list,
        help_text="List of difficulty levels present"
    )
    
    # 2025-10-31: Validation fields
    is_validated = models.BooleanField(
        default=False,
        help_text="Whether question bank JSON has been validated"
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="List of validation errors if any"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this question bank is currently active"
    )
    
    # 2025-10-31: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last time question bank was accessed"
    )
    access_count = models.IntegerField(
        default=0,
        help_text="Number of times question bank has been accessed"
    )
    
    class Meta:
        verbose_name = "Question Bank File"
        verbose_name_plural = "Question Bank Files"
        ordering = ['lesson']
    
    def __str__(self):
        # 2025-10-31: String representation
        return f"{self.qb_id} (Lesson: {self.lesson.lesson_id})"


class CurriculumCache(models.Model):
    """
    2025-10-31: Model to cache parsed lesson JSON content
    Improves performance by avoiding repeated file reads
    """
    
    # 2025-10-31: Link to lesson file
    lesson = models.OneToOneField(
        LessonFile,
        on_delete=models.CASCADE,
        related_name='cache'
    )
    
    # 2025-10-31: Cached content
    json_content = models.JSONField(
        help_text="Parsed JSON content of lesson"
    )
    
    # 2025-10-31: Cache metadata
    cache_key = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique cache key"
    )
    content_hash = models.CharField(
        max_length=64,
        help_text="SHA256 hash of file content for validation"
    )
    
    # 2025-10-31: Cache validity fields
    is_valid = models.BooleanField(
        default=True,
        help_text="Whether cache is still valid"
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cache expiration time"
    )
    
    # 2025-10-31: Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hit_count = models.IntegerField(
        default=0,
        help_text="Number of cache hits"
    )
    
    class Meta:
        verbose_name = "Curriculum Cache"
        verbose_name_plural = "Curriculum Caches"
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['cache_key']),
            models.Index(fields=['is_valid', 'expires_at']),
        ]
    
    def __str__(self):
        # 2025-10-31: String representation
        return f"Cache: {self.lesson.lesson_id} (Hits: {self.hit_count})"
