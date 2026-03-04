"""2026-03-04: Monitor Tools Service app configuration."""

from django.apps import AppConfig  # 2026-03-04: App config base


class MonitorToolsServiceConfig(AppConfig):
    """2026-03-04: AppConfig for monitor_tools_service (BS-MON-005/006/007)."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.monitor_tools_service'
    verbose_name = 'Monitor Tools Service'
