"""
2026-02-19: Parent Dashboard admin registration.

Purpose:
    Register ParentalControls model in Django admin.
"""

from django.contrib import admin  # 2026-02-19: Django admin

from .models import ParentalControls  # 2026-02-19: Our model


@admin.register(ParentalControls)
class ParentalControlsAdmin(admin.ModelAdmin):
    """2026-02-19: Admin config for ParentalControls."""

    list_display = [  # 2026-02-19: Columns in list view
        'student', 'daily_time_limit_minutes',
        'schedule_enabled', 'ai_log_enabled', 'updated_at',
    ]
    list_filter = ['schedule_enabled', 'ai_log_enabled']  # 2026-02-19: Sidebar filters
    search_fields = ['student__full_name']  # 2026-02-19: Search by student name
    readonly_fields = ['created_at', 'updated_at']  # 2026-02-19: Auto-managed
