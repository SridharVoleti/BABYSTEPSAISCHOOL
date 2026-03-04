"""
2026-03-04: Pod Service Django app configuration.

Purpose:
    Registers the pod_service app with Django for Pod Management
    and AI Student Monitoring (BS-POD + BS-MON).
"""

from django.apps import AppConfig  # 2026-03-04: App config base


class PodServiceConfig(AppConfig):
    """2026-03-04: Pod Service application configuration."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-04: BigInt PK
    name = 'services.pod_service'  # 2026-03-04: Full app label
    verbose_name = 'Pod Management & Monitoring'  # 2026-03-04: Admin label
