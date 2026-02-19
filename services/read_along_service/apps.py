"""
2026-02-19: Read-Along & Mimic Engine Django app configuration (BS-RAM).
"""

from django.apps import AppConfig  # 2026-02-19: AppConfig base class


class ReadAlongServiceConfig(AppConfig):
    """2026-02-19: App config for the Read-Along & Mimic Engine service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-19: Default PK type
    name = 'services.read_along_service'  # 2026-02-19: Dotted module path
    verbose_name = 'Read-Along & Mimic Engine'  # 2026-02-19: Admin display name
