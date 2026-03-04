"""
2026-03-02: Django admin configuration for Math Service (BS-MTH module).
"""

from django.contrib import admin  # 2026-03-02: Admin framework

from .models import (  # 2026-03-02: Own models
    MathLesson, MathSession, MathProblemAttempt, MathTutoringSession,
    MathDrillSession, MathDrillAttempt,  # 2026-03-03: Drill models (AMT-APE-005)
)


@admin.register(MathLesson)
class MathLessonAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for MathLesson model."""

    list_display = ['lesson_id', 'title', 'class_number', 'week_number', 'topic', 'status']  # 2026-03-02: Columns
    list_filter = ['class_number', 'status']  # 2026-03-02: Sidebar filters
    search_fields = ['lesson_id', 'title', 'topic']  # 2026-03-02: Search
    ordering = ['class_number', 'week_number']  # 2026-03-02: Default order


@admin.register(MathSession)
class MathSessionAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for MathSession model."""

    list_display = ['id', 'student', 'lesson', 'day_number', 'iq_level', 'status', 'star_rating', 'started_at']  # 2026-03-02: Columns
    list_filter = ['status', 'iq_level', 'star_rating']  # 2026-03-02: Sidebar filters
    search_fields = ['student__full_name', 'lesson__lesson_id']  # 2026-03-02: Search
    readonly_fields = ['id', 'started_at', 'completed_at']  # 2026-03-02: Read-only fields


@admin.register(MathProblemAttempt)
class MathProblemAttemptAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for MathProblemAttempt model."""

    list_display = ['id', 'session', 'problem_id', 'problem_type', 'is_correct', 'hints_used', 'created_at']  # 2026-03-02: Columns
    list_filter = ['is_correct', 'problem_type']  # 2026-03-02: Sidebar filters
    search_fields = ['problem_id', 'session__id']  # 2026-03-02: Search
    readonly_fields = ['id', 'created_at']  # 2026-03-02: Read-only


@admin.register(MathTutoringSession)
class MathTutoringSessionAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for MathTutoringSession model (BS-AMT-001)."""

    list_display = ['id', 'math_session', 'teaching_complete', 'message_count', 'created_at']  # 2026-03-02: Columns
    list_filter = ['teaching_complete']  # 2026-03-02: Filter by completion
    search_fields = ['math_session__lesson__lesson_id']  # 2026-03-02: Search by lesson
    readonly_fields = ['id', 'created_at', 'updated_at']  # 2026-03-02: Read-only

    def message_count(self, obj):
        """2026-03-02: Number of messages in the tutoring conversation."""
        return len(obj.messages)  # 2026-03-02: Count messages
    message_count.short_description = 'Messages'  # 2026-03-02: Column header


@admin.register(MathDrillSession)
class MathDrillSessionAdmin(admin.ModelAdmin):
    """2026-03-03: Admin for MathDrillSession model (AMT-APE-005)."""

    list_display = [
        'id', 'student', 'drill_type', 'time_limit_seconds',
        'total_questions', 'score', 'star_rating', 'status', 'started_at',
    ]  # 2026-03-03: Columns
    list_filter = ['drill_type', 'status', 'star_rating']  # 2026-03-03: Sidebar filters
    search_fields = ['student__full_name']  # 2026-03-03: Search by student name
    readonly_fields = ['id', 'started_at', 'completed_at']  # 2026-03-03: Read-only fields


@admin.register(MathDrillAttempt)
class MathDrillAttemptAdmin(admin.ModelAdmin):
    """2026-03-03: Admin for MathDrillAttempt model (AMT-APE-005)."""

    list_display = [
        'id', 'session', 'question_index', 'student_answer',
        'is_correct', 'response_time_ms', 'answered_at',
    ]  # 2026-03-03: Columns
    list_filter = ['is_correct']  # 2026-03-03: Filter by correctness
    search_fields = ['session__id']  # 2026-03-03: Search by session ID
    readonly_fields = ['id', 'answered_at']  # 2026-03-03: Read-only
