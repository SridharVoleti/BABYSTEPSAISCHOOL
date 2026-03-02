"""
2026-02-19: Comprehension Capture Engine Django app configuration (BS-CMP).

Purpose:
    Registers the comprehension_service app with Django.
"""

from django.apps import AppConfig  # 2026-02-19: AppConfig base


class ComprehensionServiceConfig(AppConfig):
    """2026-02-19: App config for the Comprehension Capture Engine."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-19: Default PK
    name = 'services.comprehension_service'  # 2026-02-19: Dotted module path
    verbose_name = 'Comprehension Capture Engine'  # 2026-02-19: Human-readable name
