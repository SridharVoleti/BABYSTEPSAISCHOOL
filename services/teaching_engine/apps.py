"""
2026-02-17: AI Teaching Engine Django app configuration.

Purpose:
    Configure the teaching_engine Django app for BabySteps platform.
    Handles personalized lesson delivery with IQ-level adaptation,
    4-day micro-lessons, revision, and weekly assessments (BS-AIE).
"""

from django.apps import AppConfig  # 2026-02-17: Import AppConfig


class TeachingEngineConfig(AppConfig):
    """2026-02-17: Configuration for the AI Teaching Engine app."""

    default_auto_field = 'django.db.models.BigAutoField'  # 2026-02-17: Use BigAutoField
    name = 'services.teaching_engine'  # 2026-02-17: Full dotted path
    verbose_name = 'AI Teaching Engine'  # 2026-02-17: Human-readable name
