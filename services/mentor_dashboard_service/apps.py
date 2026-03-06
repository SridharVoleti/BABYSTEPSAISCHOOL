"""
2026-03-06: App configuration for Mentor Dashboard Service (BS-MNT).
"""

from django.apps import AppConfig  # 2026-03-06: Django app registry


class MentorDashboardServiceConfig(AppConfig):
    """2026-03-06: Django app config for mentor_dashboard_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-06: Default PK type
    name = 'services.mentor_dashboard_service'  # 2026-03-06: Dotted app path
    verbose_name = 'Mentor Dashboard Service'  # 2026-03-06: Human-readable name
