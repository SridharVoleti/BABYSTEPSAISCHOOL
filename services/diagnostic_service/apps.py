"""
2026-02-12: Diagnostic assessment service Django app configuration.

Purpose:
    Configure the diagnostic_service Django app for BabySteps platform.
    Handles one-time diagnostic assessments using IRT 3PL adaptive testing
    to determine student IQ Level (Foundation/Standard/Advanced).
"""

from django.apps import AppConfig  # 2026-02-12: Import AppConfig


class DiagnosticServiceConfig(AppConfig):
    """2026-02-12: Configuration for the diagnostic assessment service app."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-12: Use BigAutoField
    name = 'services.diagnostic_service'  # 2026-02-12: Full dotted path
    verbose_name = 'Diagnostic Assessment Service'  # 2026-02-12: Human-readable name
