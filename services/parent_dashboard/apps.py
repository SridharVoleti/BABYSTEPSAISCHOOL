"""
2026-02-19: Parent Dashboard app configuration.

Purpose:
    AppConfig for the parent_dashboard service (BS-PAR module).
"""

from django.apps import AppConfig  # 2026-02-19: Django AppConfig


class ParentDashboardConfig(AppConfig):
    """2026-02-19: Configuration for parent_dashboard app."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-19: Default PK
    name = 'services.parent_dashboard'  # 2026-02-19: Full app path
    verbose_name = 'Parent Dashboard'  # 2026-02-19: Human-readable name
