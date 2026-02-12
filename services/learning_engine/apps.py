# 2025-12-18: Learning Engine Django App Configuration
# Author: BabySteps Development Team
# Purpose: Django app configuration for learning engine service
# Last Modified: 2025-12-18

"""
Learning Engine App Configuration

Configures the learning_engine Django application for the AI School platform.
"""

# 2025-12-18: Import Django AppConfig base class
from django.apps import AppConfig


class LearningEngineConfig(AppConfig):
    """
    2025-12-18: Django app configuration for Learning Engine service.
    
    This service handles:
    - Micro-lesson content delivery
    - Student progress tracking
    - Practice validation and feedback
    - Adaptive difficulty adjustment
    - Mastery and streak calculations
    """
    
    # 2025-12-18: Set default auto field type for models
    default_auto_field = 'django.db.models.BigAutoField'
    
    # 2025-12-18: Full Python path to the application
    name = 'services.learning_engine'
    
    # 2025-12-18: Human-readable name for admin
    verbose_name = 'Learning Engine'
    
    def ready(self):
        """
        2025-12-18: Called when Django starts.
        Import signal handlers here if needed.
        """
        pass
