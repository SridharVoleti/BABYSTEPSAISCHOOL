"""
2026-03-04: Attendance Service admin registration (BS-ATT).

Purpose:
    Register AttendanceRecord in Django admin for manual inspection
    and data correction by school administrators.
"""

from django.contrib import admin  # 2026-03-04: Admin framework

from .models import AttendanceRecord  # 2026-03-04: Model to register


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """2026-03-04: Admin configuration for AttendanceRecord."""

    list_display = [  # 2026-03-04: Columns in list view
        'student', 'date', 'status', 'check_in_time',
        'session_duration_minutes', 'recorded_by',
    ]
    list_filter = [  # 2026-03-04: Sidebar filters
        'status', 'recorded_by', 'date',
    ]
    search_fields = [  # 2026-03-04: Search by student name
        'student__full_name',
    ]
    date_hierarchy = 'date'  # 2026-03-04: Drill-down by date
    ordering = ['-date', 'student']  # 2026-03-04: Default sort
    readonly_fields = [  # 2026-03-04: Non-editable computed fields
        'id', 'created_at', 'updated_at', 'session_duration_minutes',
    ]
    raw_id_fields = ['student']  # 2026-03-04: Avoid large dropdown
