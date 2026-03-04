"""
2026-03-04: Pod Service Django admin registration.

Purpose:
    Register Pod, PodEnrollment, StudentSession, AttentionEvent, and
    MonitorAlert in Django admin for management and monitoring.
"""

from django.contrib import admin  # 2026-03-04: Admin base
from django.utils.html import format_html  # 2026-03-04: Safe HTML rendering

from .models import (  # 2026-03-04: Pod models
    Pod, PodEnrollment, StudentSession, AttentionEvent, MonitorAlert,
)


class PodEnrollmentInline(admin.TabularInline):
    """2026-03-04: Inline enrollment editor within Pod admin."""

    model = PodEnrollment  # 2026-03-04: Model
    extra = 0  # 2026-03-04: No blank rows by default
    readonly_fields = ('enrolled_at',)  # 2026-03-04: Auto fields read-only
    fields = ('student', 'is_active', 'enrolled_at')  # 2026-03-04: Visible fields


@admin.register(Pod)
class PodAdmin(admin.ModelAdmin):
    """2026-03-04: Pod admin — create and manage pods."""

    list_display = (  # 2026-03-04: Columns
        'name', 'grade', 'subject_focus', 'active_enrollment_count',
        'max_size', 'is_active', 'created_at',
    )
    list_filter = ('grade', 'is_active', 'subject_focus')  # 2026-03-04: Filters
    search_fields = ('name',)  # 2026-03-04: Search by name
    readonly_fields = ('created_at', 'updated_at')  # 2026-03-04: Auto fields
    inlines = [PodEnrollmentInline]  # 2026-03-04: Inline enrollments

    def active_enrollment_count(self, obj):
        """2026-03-04: Display active enrollment count in list view."""
        return obj.active_enrollment_count  # 2026-03-04: Property

    active_enrollment_count.short_description = 'Students'  # 2026-03-04: Column header


@admin.register(PodEnrollment)
class PodEnrollmentAdmin(admin.ModelAdmin):
    """2026-03-04: PodEnrollment admin — manage individual enrollments."""

    list_display = ('student', 'pod', 'enrolled_at', 'is_active')  # 2026-03-04: Columns
    list_filter = ('is_active', 'pod__grade')  # 2026-03-04: Filters
    search_fields = ('student__full_name', 'pod__name')  # 2026-03-04: Search
    readonly_fields = ('enrolled_at',)  # 2026-03-04: Auto fields


@admin.register(StudentSession)
class StudentSessionAdmin(admin.ModelAdmin):
    """2026-03-04: StudentSession admin — view live session data."""

    list_display = (  # 2026-03-04: Columns
        'student', 'session_start', 'last_heartbeat',
        'attention_score', 'is_active',
    )
    list_filter = ('is_active',)  # 2026-03-04: Active filter
    search_fields = ('student__full_name',)  # 2026-03-04: Search
    readonly_fields = ('session_start', 'last_heartbeat')  # 2026-03-04: Auto fields


@admin.register(AttentionEvent)
class AttentionEventAdmin(admin.ModelAdmin):
    """2026-03-04: AttentionEvent admin — review attention events."""

    list_display = (  # 2026-03-04: Columns
        'student', 'event_type', 'detected_at',
        'escalated', 'escalation_count', 'ai_response_preview',
    )
    list_filter = ('event_type', 'escalated')  # 2026-03-04: Filters
    search_fields = ('student__full_name',)  # 2026-03-04: Search
    readonly_fields = ('detected_at',)  # 2026-03-04: Auto fields

    def ai_response_preview(self, obj):
        """2026-03-04: Show first 80 characters of AI response."""
        return obj.ai_response[:80] if obj.ai_response else '—'  # 2026-03-04: Preview

    ai_response_preview.short_description = 'AI Response'  # 2026-03-04: Column header


@admin.register(MonitorAlert)
class MonitorAlertAdmin(admin.ModelAdmin):
    """2026-03-04: MonitorAlert admin — view and resolve alerts."""

    list_display = (  # 2026-03-04: Columns
        'student', 'alert_type', 'message_preview',
        'is_resolved', 'created_at',
    )
    list_filter = ('alert_type', 'is_resolved')  # 2026-03-04: Filters
    search_fields = ('student__full_name', 'message')  # 2026-03-04: Search
    readonly_fields = ('created_at',)  # 2026-03-04: Auto fields
    actions = ['resolve_selected']  # 2026-03-04: Bulk action

    def message_preview(self, obj):
        """2026-03-04: Show first 80 characters of alert message."""
        return obj.message[:80]  # 2026-03-04: Truncated preview

    message_preview.short_description = 'Message'  # 2026-03-04: Column header

    def resolve_selected(self, request, queryset):
        """2026-03-04: Bulk-resolve selected alerts."""
        updated = queryset.update(is_resolved=True)  # 2026-03-04: Bulk update
        self.message_user(request, f'{updated} alert(s) resolved.')  # 2026-03-04: Feedback

    resolve_selected.short_description = 'Mark selected alerts as resolved'  # 2026-03-04: Label
