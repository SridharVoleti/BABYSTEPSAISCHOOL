"""
2026-02-12: Diagnostic assessment service admin configuration.

Purpose:
    Register diagnostic models with Django admin for management.
"""

from django.contrib import admin  # 2026-02-12: Django admin

from .models import (  # 2026-02-12: Models
    DiagnosticSession, DiagnosticResponse, DiagnosticResult,
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
