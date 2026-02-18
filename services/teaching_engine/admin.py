"""
2026-02-17: AI Teaching Engine admin configuration.

Purpose:
    Register teaching engine models with Django admin for management.
"""

from django.contrib import admin  # 2026-02-17: Django admin

from .models import (  # 2026-02-17: Models
    TeachingLesson, StudentLessonProgress, DayProgress,
    WeeklyAssessmentAttempt, TutoringSession,
    PracticeSession, PracticeResponse, ConceptMastery,  # 2026-02-17: Mastery practice models
)


@admin.register(TeachingLesson)
class TeachingLessonAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for TeachingLesson model."""

    list_display = ['lesson_id', 'title', 'subject', 'class_number', 'week_number', 'status']
    list_filter = ['subject', 'class_number', 'status']
    search_fields = ['lesson_id', 'title', 'chapter_title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(StudentLessonProgress)
class StudentLessonProgressAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for StudentLessonProgress model."""

    list_display = ['student', 'lesson', 'iq_level', 'current_day', 'status', 'assessment_star_rating']
    list_filter = ['iq_level', 'status']
    search_fields = ['student__full_name', 'lesson__lesson_id']
    readonly_fields = ['id', 'started_at', 'created_at', 'updated_at']


@admin.register(DayProgress)
class DayProgressAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for DayProgress model."""

    list_display = ['lesson_progress', 'day_number', 'status', 'practice_score', 'questions_correct', 'mastery_star_rating', 'mastery_passed']
    list_filter = ['status', 'day_number', 'mastery_passed']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WeeklyAssessmentAttempt)
class WeeklyAssessmentAttemptAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for WeeklyAssessmentAttempt model."""

    list_display = ['lesson_progress', 'attempt_number', 'score', 'total_points', 'star_rating']
    list_filter = ['star_rating']
    readonly_fields = ['id', 'created_at']


@admin.register(TutoringSession)
class TutoringSessionAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for TutoringSession model."""

    list_display = ['student', 'lesson_progress', 'day_number', 'created_at']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(PracticeSession)
class PracticeSessionAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for PracticeSession model."""

    list_display = ['student', 'day_number', 'iq_level', 'status', 'star_rating', 'questions_answered', 'questions_correct', 'attempt_number']
    list_filter = ['status', 'iq_level', 'star_rating', 'day_number']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(PracticeResponse)
class PracticeResponseAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for PracticeResponse model."""

    list_display = ['session', 'position', 'question_id', 'difficulty', 'question_type', 'is_correct', 'time_taken_seconds']
    list_filter = ['difficulty', 'question_type', 'is_correct']
    readonly_fields = ['id', 'created_at']


@admin.register(ConceptMastery)
class ConceptMasteryAdmin(admin.ModelAdmin):
    """2026-02-17: Admin config for ConceptMastery model."""

    list_display = ['student', 'lesson', 'day_number', 'best_star_rating', 'attempts_count', 'is_mastered']
    list_filter = ['is_mastered', 'best_star_rating', 'day_number']
    search_fields = ['student__full_name', 'lesson__lesson_id']
    readonly_fields = ['id', 'created_at', 'updated_at']
