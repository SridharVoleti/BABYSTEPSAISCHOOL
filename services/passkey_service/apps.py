"""
2026-03-04: Passkey / WebAuthn app configuration (BS-AUTH-002).

Purpose:
    Django app config for passkey_service — stores WebAuthn
    public-key credentials for passwordless login.
"""

from django.apps import AppConfig  # 2026-03-04: Django app registry


class PasskeyServiceConfig(AppConfig):
    """2026-03-04: App config for passkey_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-04: PK type
    name = 'services.passkey_service'  # 2026-03-04: Dotted module path
    label = 'passkey_service'  # 2026-03-04: Short label (used in migrations)
    verbose_name = 'Passkey / WebAuthn Service'  # 2026-03-04: Human-readable
