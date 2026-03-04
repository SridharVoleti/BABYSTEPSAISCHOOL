"""2026-03-04: Communication Service app configuration."""

from django.apps import AppConfig


class CommunicationServiceConfig(AppConfig):
    """2026-03-04: AppConfig for communication_service (BS-COM + BS-PAR-006)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.communication_service'
    verbose_name = 'Communication Service'
