"""
2026-03-02: Django admin registration for Language Stages Service (BS-LNG-005).
"""

from django.contrib import admin  # 2026-03-02: Admin framework

from .models import (  # 2026-03-02: Models to register
    ConversationScenario, ConversationSession, ConversationTurn,
    StudentConversationProgress,
)


@admin.register(ConversationScenario)
class ConversationScenarioAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for conversation scenarios."""

    list_display = [  # 2026-03-02: List columns
        'scenario_number', 'title', 'ai_persona', 'difficulty',
        'min_turns', 'max_turns', 'unlock_after_scenario',
    ]
    list_filter = ['difficulty']  # 2026-03-02: Filter sidebar
    search_fields = ['title', 'ai_persona']  # 2026-03-02: Search
    ordering = ['scenario_number']  # 2026-03-02: Default order


@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for conversation sessions."""

    list_display = [  # 2026-03-02: List columns
        'student', 'scenario', 'language', 'status',
        'turn_count', 'fluency_star_rating', 'started_at',
    ]
    list_filter = ['status', 'complexity_level']  # 2026-03-02: Filters
    search_fields = ['student__full_name']  # 2026-03-02: Search by student name
    ordering = ['-started_at']  # 2026-03-02: Newest first


@admin.register(ConversationTurn)
class ConversationTurnAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for conversation turns."""

    list_display = [  # 2026-03-02: List columns
        'session', 'turn_number', 'role', 'turn_quality_score', 'recast_applied',
    ]
    list_filter = ['role', 'recast_applied']  # 2026-03-02: Filters
    ordering = ['session', 'turn_number']  # 2026-03-02: Sequential


@admin.register(StudentConversationProgress)
class StudentConversationProgressAdmin(admin.ModelAdmin):
    """2026-03-02: Admin for student conversation progress."""

    list_display = [  # 2026-03-02: List columns
        'student', 'language', 'scenarios_completed', 'total_turns',
        'current_streak_days', 'last_session_date',
    ]
    search_fields = ['student__full_name']  # 2026-03-02: Search by name
    ordering = ['-updated_at']  # 2026-03-02: Most recently active
