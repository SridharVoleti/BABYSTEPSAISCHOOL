"""
2026-02-12: Diagnostic assessment service admin configuration.

Purpose:
    Register diagnostic models with Django admin for management.
"""

from django.contrib import admin  # 2026-02-12: Django admin

from .models import (  # 2026-02-12: Models
    DiagnosticSession, DiagnosticResponse, DiagnosticResult,
    IQReassessmentWindow, IQReassessmentEvent,  # 2026-02-27: Reassessment models
)


@admin.register(DiagnosticSession)
class DiagnosticSessionAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for DiagnosticSession model."""

    list_display = ['student', 'status', 'theta_estimate', 'items_administered', 'result_level', 'created_at']
    list_filter = ['status', 'result_level']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(DiagnosticResponse)
class DiagnosticResponseAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for DiagnosticResponse model."""

    list_display = ['session', 'item_id', 'is_correct', 'response_time_ms', 'theta_after', 'position']
    list_filter = ['is_correct']
    readonly_fields = ['id', 'created_at']


@admin.register(DiagnosticResult)
class DiagnosticResultAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for DiagnosticResult model."""

    list_display = ['student', 'overall_level', 'theta_final', 'created_at']
    list_filter = ['overall_level']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at']


@admin.register(IQReassessmentWindow)
class IQReassessmentWindowAdmin(admin.ModelAdmin):
    """2026-02-27: Admin config for IQReassessmentWindow model."""

    list_display = [
        'student', 'window_number', 'avg_stars', 'avg_reteaching',
        'avg_comprehension', 'outcome', 'level_before', 'level_after', 'created_at',
    ]
    list_filter = ['outcome', 'level_before', 'level_after']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at']


@admin.register(IQReassessmentEvent)
class IQReassessmentEventAdmin(admin.ModelAdmin):
    """2026-02-27: Admin config for IQReassessmentEvent model."""

    list_display = [
        'student', 'old_level', 'new_level', 'direction',
        'triggering_window', 'parent_notified', 'created_at',
    ]
    list_filter = ['direction', 'old_level', 'new_level', 'parent_notified']
    search_fields = ['student__full_name']
    readonly_fields = ['id', 'created_at']
