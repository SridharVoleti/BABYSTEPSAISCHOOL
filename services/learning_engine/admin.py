# 2025-12-18: Learning Engine Admin Configuration
# Author: BabySteps Development Team
# Purpose: Django admin interface for learning engine models
# Last Modified: 2025-12-18

"""
Learning Engine Admin Configuration

Provides admin interface for managing:
- Student Learning Profiles
- Micro-Lessons
- Progress Records
- Practice Attempts
- Difficulty Calibrations
"""

# 2025-12-18: Import Django admin
from django.contrib import admin

# 2025-12-18: Import models
from .models import (
    StudentLearningProfile,
    Lesson,
    MicroLesson,
    MicroLessonProgress,
    PracticeAttempt,
    DifficultyCalibration,
)


@admin.register(StudentLearningProfile)
class StudentLearningProfileAdmin(admin.ModelAdmin):
    """2025-12-18: Admin interface for StudentLearningProfile."""
    
    # 2025-12-18: List display columns
    list_display = [
        'user',
        'learning_speed',
        'preferred_explanation_mode',
        'total_mastery_points',
        'current_streak_days',
        'longest_streak_days',
        'last_activity_date',
    ]
    
    # 2025-12-18: Filters
    list_filter = ['learning_speed', 'preferred_explanation_mode']
    
    # 2025-12-18: Search fields
    search_fields = ['user__username', 'user__email']
    
    # 2025-12-18: Read-only fields
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    """2026-02-10: Admin interface for Lesson."""
    
    # 2026-02-10: List display columns
    list_display = [
        'lesson_id',
        'title',
        'subject',
        'class_number',
        'chapter_name',
        'total_duration_minutes',
        'status',
        'created_at',
    ]
    
    # 2026-02-10: Filters
    list_filter = [
        'subject',
        'class_number',
        'status',
    ]
    
    # 2026-02-10: Search fields
    search_fields = ['lesson_id', 'title', 'chapter_name']
    
    # 2026-02-10: Read-only fields
    readonly_fields = ['created_at', 'updated_at']
    
    # 2026-02-10: Fieldsets for organization
    fieldsets = (
        ('Identification', {
            'fields': ('lesson_id', 'title', 'status')
        }),
        ('Classification', {
            'fields': ('subject', 'class_number', 'chapter_id', 'chapter_name')
        }),
        ('Content', {
            'fields': ('learning_objectives', 'total_duration_minutes')
        }),
    )


@admin.register(MicroLesson)
class MicroLessonAdmin(admin.ModelAdmin):
    """2026-02-10: Admin interface for MicroLesson with 5-part structure."""
    
    # 2026-02-10: List display columns
    list_display = [
        'micro_lesson_id',
        'title',
        'lesson',
        'sequence_in_lesson',
        'duration_minutes',
        'difficulty_level',
        'qa_status',
        'is_published',
    ]
    
    # 2026-02-10: Filters
    list_filter = [
        'lesson',
        'sequence_in_lesson',
        'difficulty_level',
        'qa_status',
        'is_published',
        'language',
    ]
    
    # 2026-02-10: Search fields
    search_fields = ['micro_lesson_id', 'title', 'concept_explanation']
    
    # 2026-02-10: Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'qa_passed_at', 'published_at']
    
    # 2026-02-10: Fieldsets for organization
    fieldsets = (
        ('Identification', {
            'fields': ('lesson', 'sequence_in_lesson', 'micro_lesson_id', 'title')
        }),
        ('5-Part Structure', {
            'fields': (
                'concept_explanation',
                'worked_example',
                'learner_action',
                'validation_logic',
                'reinforcement_summary'
            )
        }),
        ('Settings', {
            'fields': ('duration_minutes', 'difficulty_level', 'visual_assets')
        }),
        ('Publishing', {
            'fields': ('qa_status', 'qa_notes', 'is_published', 'language')
        }),
    )


@admin.register(MicroLessonProgress)
class MicroLessonProgressAdmin(admin.ModelAdmin):
    """2025-12-18: Admin interface for MicroLessonProgress."""
    
    # 2025-12-18: List display columns
    list_display = [
        'student',
        'micro_lesson',
        'status',
        'current_step',
        'questions_correct',
        'questions_attempted',
        'mastery_score',
        'attempt_number',
    ]
    
    # 2025-12-18: Filters
    list_filter = ['status', 'current_step', 'difficulty_level']
    
    # 2025-12-18: Search fields
    search_fields = ['student__username', 'micro_lesson__lesson_id']
    
    # 2025-12-18: Read-only fields
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    """2025-12-18: Admin interface for PracticeAttempt."""
    
    # 2025-12-18: List display columns
    list_display = [
        'lesson_progress',
        'question_index',
        'is_correct',
        'time_taken_seconds',
        'hints_used',
        'retry_count',
        'attempted_at',
    ]
    
    # 2025-12-18: Filters
    list_filter = ['is_correct', 'hints_used']
    
    # 2025-12-18: Read-only fields
    readonly_fields = ['attempted_at']


@admin.register(DifficultyCalibration)
class DifficultyCalibrationAdmin(admin.ModelAdmin):
    """2025-12-18: Admin interface for DifficultyCalibration."""
    
    # 2025-12-18: List display columns
    list_display = [
        'student',
        'subject',
        'current_difficulty',
        'rolling_accuracy',
        'avg_time_per_question',
        'avg_retries',
    ]
    
    # 2025-12-18: Filters
    list_filter = ['subject', 'current_difficulty']
    
    # 2025-12-18: Search fields
    search_fields = ['student__username', 'subject']
    
    # 2025-12-18: Read-only fields
    readonly_fields = ['created_at', 'updated_at']
