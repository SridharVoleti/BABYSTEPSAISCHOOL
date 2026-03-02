"""
2026-02-27: App config for Spaced Repetition Service (BS-SPC).
"""
from django.apps import AppConfig


class SpacedRepetitionServiceConfig(AppConfig):
    """2026-02-27: Django app config for spaced repetition service."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.spaced_repetition_service'
    verbose_name = 'Spaced Repetition Service'
