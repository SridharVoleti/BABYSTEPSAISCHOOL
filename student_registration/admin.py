"""
Student Registration Admin Configuration
Author: Cascade AI
Date: 2025-12-13
Description: Django admin interface for managing student registrations
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import StudentRegistration


@admin.register(StudentRegistration)
class StudentRegistrationAdmin(admin.ModelAdmin):
    """
    Admin interface for StudentRegistration model
    Provides filtering, search, and bulk actions for managing registrations
    """
    
    # List display columns
    list_display = [
        'registration_id_short',
        'student_name',
        'student_email',
        'grade',
        'status_badge',
        'created_at',
        'approved_by',
    ]
    
    # Filters in sidebar
    list_filter = [
        'status',
        'grade',
        'preferred_language',
        'created_at',
    ]
    
    # Search fields
    search_fields = [
        'student_name',
        'student_email',
        'parent_name',
        'parent_email',
        'phone',
        'registration_id',
    ]
    
    # Read-only fields
    readonly_fields = [
        'registration_id',
        'created_at',
        'updated_at',
        'approved_by',
        'approved_at',
    ]
    
    # Fieldsets for detail view
    fieldsets = (
        ('Registration Information', {
            'fields': ('registration_id', 'status', 'created_at', 'updated_at')
        }),
        ('Student Details', {
            'fields': (
                'student_name',
                'student_email',
                'date_of_birth',
                'grade',
                'school_name',
                'preferred_language',
            )
        }),
        ('Parent/Guardian Details', {
            'fields': (
                'parent_name',
                'parent_email',
                'phone',
            )
        }),
        ('Address Information', {
            'fields': (
                'address',
                'city',
                'state',
                'pincode',
            )
        }),
        ('Approval Workflow', {
            'fields': (
                'approved_by',
                'approved_at',
                'rejection_reason',
            )
        }),
    )
    
    # Default ordering
    ordering = ['-created_at']
    
    # Items per page
    list_per_page = 25
    
    def registration_id_short(self, obj):
        """Display shortened registration ID"""
        return str(obj.registration_id)[:8] + '...'
    registration_id_short.short_description = 'Reg ID'
    
    def status_badge(self, obj):
        """Display status with color-coded badge"""
        colors = {
            'pending': '#FFC107',  # Yellow
            'approved': '#4CAF50',  # Green
            'rejected': '#F44336',  # Red
        }
        color = colors.get(obj.status, '#999999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_badge.short_description = 'Status'
    
    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion - registrations should be rejected, not deleted
        Only superusers can delete
        """
        return request.user.is_superuser
