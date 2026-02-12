# 2025-10-31: Curriculum Loader Service - Django Admin Configuration
# Author: BabySteps Development Team
# Purpose: Admin interface for curriculum management
# Last Modified: 2025-10-31

"""
Django Admin Configuration for Curriculum Loader Service

Provides admin interface for managing curriculum metadata and lesson files.
"""

from django.contrib import admin  # 2025-10-31: Import admin
from .models import (  # 2025-10-31: Import models
    CurriculumMetadata,
    LessonFile,
    QuestionBankFile,
    CurriculumCache
)


@admin.register(CurriculumMetadata)
class CurriculumMetadataAdmin(admin.ModelAdmin):
    """2025-10-31: Admin interface for CurriculumMetadata model"""
    
    # 2025-10-31: List display fields
    list_display = [
        'class_number', 'subject', 'total_lessons', 'total_question_banks',
        'total_months', 'is_active', 'is_frozen', 'academic_year'
    ]
    
    # 2025-10-31: List filters
    list_filter = ['class_number', 'subject', 'is_active', 'is_frozen', 'academic_year']
    
    # 2025-10-31: Search fields
    search_fields = ['subject', 'curriculum_path']
    
    # 2025-10-31: Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'last_validated']
    
    # 2025-10-31: Fieldsets for organized display
    fieldsets = (
        ('Basic Information', {
            'fields': ('class_number', 'subject', 'academic_year', 'version')
        }),
        ('Content Statistics', {
            'fields': ('total_months', 'total_weeks', 'total_lessons', 'total_question_banks')
        }),
        ('Path and Status', {
            'fields': ('curriculum_path', 'is_active', 'is_frozen')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'last_validated', 'created_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LessonFile)
class LessonFileAdmin(admin.ModelAdmin):
    """2025-10-31: Admin interface for LessonFile model"""
    
    # 2025-10-31: List display fields
    list_display = [
        'lesson_id', 'lesson_title', 'curriculum', 'month', 'week', 'day',
        'level', 'duration_minutes', 'is_validated', 'is_active'
    ]
    
    # 2025-10-31: List filters
    list_filter = ['curriculum', 'month', 'week', 'level', 'is_validated', 'is_active']
    
    # 2025-10-31: Search fields
    search_fields = ['lesson_id', 'lesson_title', 'file_path']
    
    # 2025-10-31: Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'last_accessed', 'access_count']
    
    # 2025-10-31: Ordering
    ordering = ['curriculum', 'month', 'week', 'day']
    
    # 2025-10-31: Fieldsets
    fieldsets = (
        ('Identification', {
            'fields': ('lesson_id', 'lesson_title', 'curriculum')
        }),
        ('Temporal Organization', {
            'fields': ('month', 'week', 'day')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size')
        }),
        ('Lesson Metadata', {
            'fields': ('duration_minutes', 'level', 'version', 'languages')
        }),
        ('Content Features', {
            'fields': ('has_tts', 'has_activities', 'has_ai_coach', 'has_question_bank')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validation_errors', 'is_active')
        }),
        ('Analytics', {
            'fields': ('created_at', 'updated_at', 'last_accessed', 'access_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuestionBankFile)
class QuestionBankFileAdmin(admin.ModelAdmin):
    """2025-10-31: Admin interface for QuestionBankFile model"""
    
    # 2025-10-31: List display fields
    list_display = [
        'qb_id', 'lesson', 'total_questions', 'is_validated', 'is_active'
    ]
    
    # 2025-10-31: List filters
    list_filter = ['is_validated', 'is_active']
    
    # 2025-10-31: Search fields
    search_fields = ['qb_id', 'file_path']
    
    # 2025-10-31: Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'last_accessed', 'access_count']
    
    # 2025-10-31: Fieldsets
    fieldsets = (
        ('Identification', {
            'fields': ('qb_id', 'lesson')
        }),
        ('File Information', {
            'fields': ('file_path', 'file_size')
        }),
        ('Question Bank Metadata', {
            'fields': ('total_questions', 'question_types', 'difficulty_levels')
        }),
        ('Validation', {
            'fields': ('is_validated', 'validation_errors', 'is_active')
        }),
        ('Analytics', {
            'fields': ('created_at', 'updated_at', 'last_accessed', 'access_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CurriculumCache)
class CurriculumCacheAdmin(admin.ModelAdmin):
    """2025-10-31: Admin interface for CurriculumCache model"""
    
    # 2025-10-31: List display fields
    list_display = [
        'cache_key', 'lesson', 'is_valid', 'hit_count', 'expires_at', 'updated_at'
    ]
    
    # 2025-10-31: List filters
    list_filter = ['is_valid']
    
    # 2025-10-31: Search fields
    search_fields = ['cache_key', 'content_hash']
    
    # 2025-10-31: Read-only fields
    readonly_fields = ['created_at', 'updated_at', 'hit_count']
    
    # 2025-10-31: Ordering
    ordering = ['-updated_at']
    
    # 2025-10-31: Fieldsets
    fieldsets = (
        ('Cache Information', {
            'fields': ('cache_key', 'lesson', 'content_hash')
        }),
        ('Validity', {
            'fields': ('is_valid', 'expires_at')
        }),
        ('Analytics', {
            'fields': ('hit_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Content', {
            'fields': ('json_content',),
            'classes': ('collapse',)
        }),
    )
