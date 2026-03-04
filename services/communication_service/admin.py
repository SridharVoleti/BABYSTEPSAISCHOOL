"""2026-03-04: Communication Service admin registration."""

from django.contrib import admin

from .models import Announcement, Message, MessageThread, TermReport, WeeklyProgressReport


@admin.register(MessageThread)
class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ['student', 'parent', 'monitor', 'subject', 'is_closed', 'updated_at']
    list_filter = ['is_closed']
    raw_id_fields = ['student', 'parent', 'monitor']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['thread', 'sender_type', 'is_read', 'created_at']
    list_filter = ['sender_type', 'is_read']
    readonly_fields = ['id', 'created_at']
    raw_id_fields = ['thread']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'priority', 'is_active', 'created_at']
    list_filter = ['audience', 'priority', 'is_active']
    search_fields = ['title', 'body']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(WeeklyProgressReport)
class WeeklyProgressReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'week_start', 'attendance_days', 'lessons_completed', 'avg_star_rating']
    list_filter = ['week_start']
    raw_id_fields = ['student']
    readonly_fields = ['id', 'generated_at']


@admin.register(TermReport)
class TermReportAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'term', 'generated_at']
    list_filter = ['academic_year', 'term']
    raw_id_fields = ['student']
    readonly_fields = ['id', 'generated_at']
