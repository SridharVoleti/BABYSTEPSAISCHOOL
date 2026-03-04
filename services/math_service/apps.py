"""
2026-03-02: Math Service Django app configuration (BS-MTH module).
"""

from django.apps import AppConfig  # 2026-03-02: App config base


class MathServiceConfig(AppConfig):
    """2026-03-02: Configuration for the Math Service app."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-02: Default PK type
    name = 'services.math_service'  # 2026-03-02: Dotted path
    label = 'math_service'  # 2026-03-02: Unique label for admin
    verbose_name = 'Math Service'  # 2026-03-02: Human-readable name
