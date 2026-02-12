"""
2026-02-12: Authentication service admin configuration.

Purpose:
    Register auth models with Django admin for management.
"""

from django.contrib import admin  # 2026-02-12: Django admin

from .models import (  # 2026-02-12: Models
    Parent, Student, OTPRequest, ConsentRecord, AuditLog,
)


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for Parent model."""

    list_display = ['full_name', 'phone', 'is_phone_verified', 'is_profile_complete', 'created_at']
    list_filter = ['is_phone_verified', 'is_profile_complete', 'state']
    search_fields = ['full_name', 'phone', 'email']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for Student model."""

    list_display = ['full_name', 'grade', 'age_group', 'login_method', 'parent', 'is_active']
    list_filter = ['grade', 'age_group', 'login_method', 'is_active']
    search_fields = ['full_name', 'parent__full_name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(OTPRequest)
class OTPRequestAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for OTPRequest model."""

    list_display = ['phone', 'purpose', 'attempts', 'is_verified', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_verified']
    search_fields = ['phone']
    readonly_fields = ['id', 'created_at']


@admin.register(ConsentRecord)
class ConsentRecordAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for ConsentRecord model."""

    list_display = ['parent', 'consent_version', 'action', 'scroll_percentage', 'timestamp']
    list_filter = ['action', 'consent_version']
    readonly_fields = ['id', 'timestamp']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """2026-02-12: Admin config for AuditLog model."""

    list_display = ['action', 'resource_type', 'user', 'ip_address', 'timestamp']
    list_filter = ['action', 'resource_type']
    search_fields = ['action']
    readonly_fields = ['id', 'timestamp']
