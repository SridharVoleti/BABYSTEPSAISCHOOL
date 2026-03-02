"""
2026-02-20: Django app configuration for Gamification Engine (BS-GAM).
"""

from django.apps import AppConfig  # 2026-02-20: Base app config class


class GamificationServiceConfig(AppConfig):
    """2026-02-20: App configuration for gamification_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-20: Default PK type
    name = 'services.gamification_service'  # 2026-02-20: Full dotted path
    verbose_name = 'Gamification Engine'  # 2026-02-20: Human-readable name
