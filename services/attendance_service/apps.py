"""2026-03-04: Attendance Service app configuration."""

from django.apps import AppConfig  # 2026-03-04: App config base


class AttendanceServiceConfig(AppConfig):
    """2026-03-04: AppConfig for attendance_service (BS-ATT)."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-03-04: Default PK
    name = 'services.attendance_service'  # 2026-03-04: Full dotted path
    verbose_name = 'Attendance Service'  # 2026-03-04: Human-readable name
