"""
Analytics Service Django App Configuration

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Configure the analytics service Django application.
    Defines app settings, initialization, and ready() hook for startup tasks.
"""

# Django imports for app configuration
from django.apps import AppConfig


class AnalyticsServiceConfig(AppConfig):
    """
    Configuration class for analytics service application.
    
    Attributes:
        default_auto_field (str): Default primary key field type for models
        name (str): Full Python path to the application
        verbose_name (str): Human-readable name for admin interface
    
    Purpose:
        - Configure app metadata
        - Initialize analytics service on Django startup
        - Register signal handlers
        - Set up periodic tasks (if using Celery)
    """
    
    # Use BigAutoField for primary keys to support large datasets
    # This allows up to 9 quintillion records per table
    default_auto_field = 'django.db.models.BigAutoField'
    
    # Full Python path to this application
    # Django uses this to locate models, views, etc.
    name = 'services.analytics_service'
    
    # Human-readable application name
    # Displayed in Django admin interface
    verbose_name = 'Analytics Service'
    
    def ready(self):
        """
        Called when Django starts and app is ready.
        
        Purpose:
            - Import signal handlers
            - Initialize background tasks
            - Set up analytics collectors
            - Validate configuration
        
        Note:
            This method may be called multiple times in development
            (due to auto-reloader), so ensure operations are idempotent.
        """
        # Import signals to register handlers
        # Signals will be implemented in signals.py
        try:
            import services.analytics_service.signals
        except ImportError:
            # Signals module doesn't exist yet, will be created
            pass
