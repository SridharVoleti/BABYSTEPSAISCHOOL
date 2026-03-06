"""
2026-03-06: Django admin registration for Mentor Dashboard Service (BS-MNT).
"""

from django.contrib import admin  # 2026-03-06: Admin site

from .models import ComprehensionReview, MentorAssignment, WeeklySummary  # 2026-03-06: Our models


@admin.register(MentorAssignment)
class MentorAssignmentAdmin(admin.ModelAdmin):
    """2026-03-06: Admin for mentor–student assignment records."""

    list_display = ('mentor', 'student', 'is_active', 'assigned_at')  # 2026-03-06: Columns
    list_filter = ('is_active',)  # 2026-03-06: Filter sidebar
    search_fields = ('mentor__username', 'student__full_name')  # 2026-03-06: Search
    raw_id_fields = ('mentor', 'student')  # 2026-03-06: FK widgets
    ordering = ('-assigned_at',)  # 2026-03-06: Newest first


@admin.register(ComprehensionReview)
class ComprehensionReviewAdmin(admin.ModelAdmin):
    """2026-03-06: Admin for mentor comprehension review records."""

    list_display = ('reviewed_by', 'response', 'mentor_score', 'reviewed_at')  # 2026-03-06: Columns
    list_filter = ('mentor_score',)  # 2026-03-06: Filter by score
    search_fields = ('reviewed_by__username',)  # 2026-03-06: Search
    raw_id_fields = ('reviewed_by', 'response')  # 2026-03-06: FK widgets
    ordering = ('-reviewed_at',)  # 2026-03-06: Newest first


@admin.register(WeeklySummary)
class WeeklySummaryAdmin(admin.ModelAdmin):
    """2026-03-06: Admin for AI-generated weekly summaries."""

    list_display = ('student', 'week_start', 'lessons_completed', 'avg_star_rating', 'generated_at')
    list_filter = ('week_start',)  # 2026-03-06: Filter by week
    search_fields = ('student__full_name',)  # 2026-03-06: Search
    raw_id_fields = ('student', 'generated_by')  # 2026-03-06: FK widgets
    ordering = ('-week_start',)  # 2026-03-06: Newest first
    readonly_fields = ('generated_at',)  # 2026-03-06: Auto timestamp
