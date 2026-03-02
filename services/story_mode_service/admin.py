"""
2026-02-27: Django admin registration for Story Mode Service (BS-GAM-003).
"""

from django.contrib import admin  # 2026-02-27: Admin site registration

from .models import NarrativeScene, StudentStoryProgress  # 2026-02-27: Story models


@admin.register(NarrativeScene)
class NarrativeSceneAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for the NarrativeScene master catalog."""

    list_display = [  # 2026-02-27: Columns shown in list view
        'scene_id',
        'subject',
        'scene_type',
        'concept_slot',
    ]
    list_filter = ['subject', 'scene_type']  # 2026-02-27: Sidebar filters
    search_fields = [  # 2026-02-27: Full-text search fields
        'scene_id',
        'subject',
        'narrative_text',
    ]
    ordering = ['subject', 'concept_slot']  # 2026-02-27: Natural reading order
    readonly_fields = ['id', 'created_at']  # 2026-02-27: Immutable system fields


@admin.register(StudentStoryProgress)
class StudentStoryProgressAdmin(admin.ModelAdmin):
    """2026-02-27: Admin for per-student story progress records."""

    list_display = [  # 2026-02-27: Columns shown in list view
        'student',
        'total_quests_completed',
        'last_unlocked_at',
    ]
    search_fields = ['student__full_name']  # 2026-02-27: Search by student name
    readonly_fields = [  # 2026-02-27: Immutable system fields
        'id',
        'created_at',
        'updated_at',
    ]
