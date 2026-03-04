"""
2026-03-02: Django app configuration for Language Stages Service (BS-LNG-005).
"""

from django.apps import AppConfig  # 2026-03-02: App config base


class LanguageStagesServiceConfig(AppConfig):
    """2026-03-02: App config for language_stages_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-02: PK type
    name = 'services.language_stages_service'  # 2026-03-02: Dotted module path
    verbose_name = 'Language Stages (BS-LNG-005)'  # 2026-03-02: Admin label
