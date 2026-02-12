"""
LLM Service Django App Configuration

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Django application configuration for the LLM service.
    Registers the service with Django and handles initialization.
"""

# Django imports
from django.apps import AppConfig


class LLMServiceConfig(AppConfig):
    """
    Django AppConfig for LLM Service.
    
    Purpose:
        Configures the LLM service as a Django application.
        Handles service initialization and setup.
    
    Attributes:
        name: Full Python path to the application
        verbose_name: Human-readable name for admin interface
        default_auto_field: Default primary key field type
    """
    
    # Default primary key field type for models
    # Uses BigAutoField for large-scale applications
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Full Python path to this application
    # Django uses this to locate the app
    name = 'services.llm_service'
    
    # Human-readable name
    # Displayed in Django admin and other interfaces
    verbose_name = 'LLM Provider Service'
    
    def ready(self):
        """
        Called when Django starts up.
        
        Purpose:
            Initialize the LLM service.
            Register signal handlers.
            Perform startup checks.
        
        Note:
            This method is called once per Django process.
            Be careful with side effects.
        """
        # Import signals (if any are added in future)
        # from . import signals
        
        # Log service initialization
        import logging
        logger = logging.getLogger(__name__)
        logger.info("LLM Service initialized successfully")
