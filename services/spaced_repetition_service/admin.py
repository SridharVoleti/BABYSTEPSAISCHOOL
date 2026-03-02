"""
2026-02-27: Django admin configuration for Spaced Repetition Service (BS-SPC).
"""
from django.contrib import admin  # 2026-02-27: Django admin

from .models import (  # 2026-02-27: Service models
    SpacedRepetitionRecord,
    ReviewSession,
    ReviewResponse,
    PacingRecord,
)


@admin.register(SpacedRepetitionRecord)
class SpacedRepetitionRecordAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for spaced repetition records."""

    list_display = [
        'student', 'mastery', 'box', 'next_review_date', 'phase', 'review_count',
    ]
    list_filter = ['box', 'phase']
    search_fields = ['student__full_name']
    ordering = ['next_review_date']


@admin.register(ReviewSession)
class ReviewSessionAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for review sessions."""

    list_display = ['student', 'status', 'concepts_reviewed', 'started_at']
    list_filter = ['status']
    search_fields = ['student__full_name']


@admin.register(ReviewResponse)
class ReviewResponseAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for individual review responses."""

    list_display = ['session', 'mastery', 'stars_awarded', 'outcome', 'created_at']
    list_filter = ['outcome']


@admin.register(PacingRecord)
class PacingRecordAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for student pacing records."""

    list_display = [
        'student', 'phase', 'daily_target', 'iq_adjustment_factor', 'intensive_end_date',
    ]
    list_filter = ['phase']
    search_fields = ['student__full_name']
