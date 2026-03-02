"""
2026-02-20: Django admin registration for Vocabulary Acquisition System (BS-LNG).

Purpose:
    Register VocabularyWord, WordContent, StudentWordProgress,
    VocabularySession, and SessionWord in the Django admin interface
    for management and inspection.
"""

from django.contrib import admin  # 2026-02-20: Django admin

from .models import (  # 2026-02-20: All vocabulary models
    VocabularyWord, WordContent, StudentWordProgress,
    VocabularySession, SessionWord,
)


@admin.register(VocabularyWord)
class VocabularyWordAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for VocabularyWord."""

    list_display = [  # 2026-02-20: Columns in list view
        'word', 'language', 'grade', 'frequency_rank', 'word_type', 'romanization'
    ]
    list_filter = ['language', 'grade', 'word_type']  # 2026-02-20: Sidebar filters
    search_fields = ['word', 'romanization', 'image_keyword']  # 2026-02-20: Search fields
    ordering = ['language', 'grade', 'frequency_rank']  # 2026-02-20: Default sort


@admin.register(WordContent)
class WordContentAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for WordContent (LLM cache)."""

    list_display = [  # 2026-02-20: Columns in list view
        'word', 'mother_tongue', 'llm_error', 'created_at'
    ]
    list_filter = ['mother_tongue', 'llm_error']  # 2026-02-20: Sidebar filters
    readonly_fields = ['created_at', 'updated_at']  # 2026-02-20: Auto timestamps


@admin.register(StudentWordProgress)
class StudentWordProgressAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for StudentWordProgress."""

    list_display = [  # 2026-02-20: Columns in list view
        'student', 'word', 'status', 'exposure_count',
        'best_pronunciation_score', 'mcq_correct_count',
    ]
    list_filter = ['status']  # 2026-02-20: Filter by mastery level
    search_fields = ['student__full_name', 'word__word']  # 2026-02-20: Search


@admin.register(VocabularySession)
class VocabularySessionAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for VocabularySession."""

    list_display = [  # 2026-02-20: Columns in list view
        'student', 'language', 'session_date', 'status',
        'fluency_star_rating', 'grade',
    ]
    list_filter = ['status', 'language', 'grade']  # 2026-02-20: Sidebar filters
    date_hierarchy = 'session_date'  # 2026-02-20: Date drill-down


@admin.register(SessionWord)
class SessionWordAdmin(admin.ModelAdmin):
    """2026-02-20: Admin for SessionWord (session-word through table)."""

    list_display = [  # 2026-02-20: Columns in list view
        'session', 'word', 'word_order', 'pronunciation_score',
        'mcq_answered', 'mcq_correct',
    ]
    list_filter = ['mcq_answered', 'mcq_correct']  # 2026-02-20: Filter options
