"""
2026-02-12: Authentication service Django app configuration.

Purpose:
    Configure the auth_service Django app for the BabySteps platform.
    Handles parent/student authentication via WhatsApp OTP and JWT.
"""

from django.apps import AppConfig  # 2026-02-12: Import AppConfig


class AuthServiceConfig(AppConfig):
    """2026-02-12: Configuration for the authentication service app."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-12: Use BigAutoField
    name = 'services.auth_service'  # 2026-02-12: Full dotted path
    verbose_name = 'Authentication Service'  # 2026-02-12: Human-readable name
