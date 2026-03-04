"""2026-03-04: Monitor Tools Service admin registration."""

from django.contrib import admin  # 2026-03-04: Admin framework

from .models import GradeBookEntry, HomeworkAssignment, HomeworkSubmission, TimetableSlot


@admin.register(GradeBookEntry)
class GradeBookEntryAdmin(admin.ModelAdmin):
    """2026-03-04: Admin for GradeBookEntry."""
    list_display = ['student', 'subject', 'term', 'assessment_type', 'title', 'score', 'letter_grade', 'date_recorded']
    list_filter = ['term', 'assessment_type', 'subject']
    search_fields = ['student__full_name', 'title']
    raw_id_fields = ['student']
    readonly_fields = ['id', 'created_at', 'updated_at', 'letter_grade']


@admin.register(HomeworkAssignment)
class HomeworkAssignmentAdmin(admin.ModelAdmin):
    """2026-03-04: Admin for HomeworkAssignment."""
    list_display = ['grade', 'subject', 'title', 'due_date', 'is_active']
    list_filter = ['grade', 'subject', 'is_active']
    search_fields = ['title']
    readonly_fields = ['id', 'created_at']


@admin.register(HomeworkSubmission)
class HomeworkSubmissionAdmin(admin.ModelAdmin):
    """2026-03-04: Admin for HomeworkSubmission."""
    list_display = ['student', 'homework', 'status', 'submitted_at']
    list_filter = ['status']
    raw_id_fields = ['student', 'homework']
    readonly_fields = ['id', 'created_at']


@admin.register(TimetableSlot)
class TimetableSlotAdmin(admin.ModelAdmin):
    """2026-03-04: Admin for TimetableSlot."""
    list_display = ['grade', 'day_of_week', 'start_time', 'end_time', 'subject', 'teacher_name', 'is_active']
    list_filter = ['grade', 'day_of_week', 'is_active']
    search_fields = ['subject', 'teacher_name']
    readonly_fields = ['id', 'updated_at']
