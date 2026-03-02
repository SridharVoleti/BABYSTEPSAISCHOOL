"""
2026-02-27: Django app configuration for Story Mode Service (BS-GAM-003).
"""

from django.apps import AppConfig  # 2026-02-27: Base app config class


class StoryModeServiceConfig(AppConfig):
    """2026-02-27: App configuration for story_mode_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-27: Default PK type
    name = 'services.story_mode_service'  # 2026-02-27: Full dotted path
    verbose_name = 'Story Mode Service'  # 2026-02-27: Human-readable name
