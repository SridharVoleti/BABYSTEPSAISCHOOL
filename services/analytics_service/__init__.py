"""
Analytics Service Package Initialization

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Analytics service for tracking student learning behavior, progress,
    and engagement metrics. This service provides the foundation for
    personalized learning and adaptive content delivery.

Architecture:
    This service follows microservices architecture and SOLID principles.
    - Single Responsibility: Only handles analytics and tracking
    - Open/Closed: Extensible for new metrics without modifying core
    - Liskov Substitution: All trackers implement base tracker interface
    - Interface Segregation: Specific interfaces for different analytics types
    - Dependency Inversion: Depends on abstractions, not implementations

Services Provided:
    - Student activity tracking
    - Progress monitoring
    - Engagement metrics
    - Time-on-task analysis
    - Learning pattern detection
"""

# Package version
__version__ = '1.0.0'

# Package metadata
__author__ = 'BabySteps Development Team'
__date__ = '2025-12-11'

# Import key components for easy access
# These will be defined as we implement each module
default_app_config = 'services.analytics_service.apps.AnalyticsServiceConfig'
