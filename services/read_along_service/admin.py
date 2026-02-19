"""
2026-02-19: Django admin registration for Read-Along service (BS-RAM).

Purpose:
    Register Language and ReadAlongSession models with rich admin UIs.
    Language admin allows inline editing of is_active, sort_order, tts_rate.
    To add a new language without code changes, use the Language add form.
"""

from django.contrib import admin  # 2026-02-19: Django admin

from .models import Language, ReadAlongSession  # 2026-02-19: Models to register


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """
    2026-02-19: Admin for the Language model.

    Allows admins to add/deactivate languages without code changes.
    list_editable enables inline toggling of is_active, sort_order, tts_rate.
    """

    list_display = [  # 2026-02-19: Columns shown in list view
        'name', 'display_name', 'bcp47_tag', 'script', 'tts_rate', 'is_active', 'sort_order'
    ]
    list_editable = [  # 2026-02-19: Editable directly in list view
        'is_active', 'sort_order', 'tts_rate'
    ]
    list_filter = ['is_active', 'script']  # 2026-02-19: Sidebar filters
    search_fields = ['name', 'bcp47_tag', 'display_name']  # 2026-02-19: Search box
    ordering = ['sort_order', 'name']  # 2026-02-19: Default ordering


@admin.register(ReadAlongSession)
class ReadAlongSessionAdmin(admin.ModelAdmin):
    """
    2026-02-19: Admin for ReadAlongSession — read-only audit view.
    """

    list_display = [  # 2026-02-19: Session summary columns
        'student', 'lesson', 'day_number', 'language',
        'star_rating', 'overall_score', 'attempt_number', 'status', 'created_at',
    ]
    list_filter = ['language', 'status', 'star_rating']  # 2026-02-19: Filters
    search_fields = ['student__full_name', 'lesson__lesson_id']  # 2026-02-19: Search
    readonly_fields = [  # 2026-02-19: All fields read-only
        'id', 'student', 'lesson', 'day_number', 'language', 'bcp47_tag',
        'sentence_scores', 'overall_score', 'star_rating', 'sentences_attempted',
        'sentences_total', 'attempt_number', 'status', 'time_spent_seconds',
        'completed_at', 'created_at',
    ]
    ordering = ['-created_at']  # 2026-02-19: Newest first
