"""
2026-02-20: Vocabulary Acquisition System (BS-LNG) app configuration.

Purpose:
    Django AppConfig for the vocabulary_service. Registered in INSTALLED_APPS
    as 'services.vocabulary_service'.
"""

from django.apps import AppConfig  # 2026-02-20: Django app config base


class VocabularyServiceConfig(AppConfig):
    """2026-02-20: Django app config for vocabulary_service."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-20: Default PK type
    name = 'services.vocabulary_service'  # 2026-02-20: Dotted path to app
    verbose_name = 'Vocabulary Acquisition (BS-LNG)'  # 2026-02-20: Admin label
