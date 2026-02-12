"""
Analytics Service URL Configuration

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Define URL routing for analytics service API endpoints.
    Maps URLs to viewsets using Django REST Framework routers.

URL Structure:
    /api/analytics/activities/          - Activity tracking
    /api/analytics/activities/summary/  - Activity summary
    /api/analytics/progress/            - Progress tracking
    /api/analytics/progress/summary/    - Progress summary

Router Features:
    - Automatic CRUD endpoint generation
    - Support for custom actions
    - Standardized URL patterns
    - API browsability
"""

# Django imports
from django.urls import path, include

# Django REST Framework imports
from rest_framework.routers import DefaultRouter

# Import viewsets
from .views import StudentActivityViewSet, StudentProgressViewSet

# Create router instance
# DefaultRouter provides standard REST endpoints
# Automatically generates:
#   - list: GET /resource/
#   - create: POST /resource/
#   - retrieve: GET /resource/{id}/
#   - update: PUT /resource/{id}/
#   - partial_update: PATCH /resource/{id}/
#   - destroy: DELETE /resource/{id}/
router = DefaultRouter()

# Register viewsets with router
# First argument is URL prefix
# Second argument is viewset class
# Third argument (optional) is basename for URL names

# Activity endpoints
# Generates URLs:
#   GET    /activities/                  - List activities
#   POST   /activities/                  - Create activity
#   GET    /activities/{id}/             - Retrieve activity
#   PUT    /activities/{id}/             - Update activity
#   PATCH  /activities/{id}/             - Partial update
#   DELETE /activities/{id}/             - Delete activity
#   GET    /activities/summary/          - Summary (custom action)
router.register(
    r'activities',
    StudentActivityViewSet,
    basename='activity'
)

# Progress endpoints
# Generates URLs:
#   GET    /progress/                    - List progress
#   POST   /progress/                    - Create progress
#   GET    /progress/{id}/               - Retrieve progress
#   PUT    /progress/{id}/               - Update progress
#   PATCH  /progress/{id}/               - Partial update
#   DELETE /progress/{id}/               - Delete progress
#   GET    /progress/summary/            - Summary (custom action)
#   POST   /progress/{id}/update-streak/ - Update streak (custom action)
router.register(
    r'progress',
    StudentProgressViewSet,
    basename='progress'
)

# Define URL patterns
# The router.urls include all registered viewset URLs
urlpatterns = [
    # Include all router-generated URLs
    # This mounts the analytics API at the base path
    path('', include(router.urls)),
]

# URL naming convention:
# Router automatically creates named URLs:
#   activity-list: /activities/
#   activity-detail: /activities/{id}/
#   activity-summary: /activities/summary/
#   progress-list: /progress/
#   progress-detail: /progress/{id}/
#   progress-summary: /progress/summary/
#   progress-update-streak: /progress/{id}/update-streak/

# Usage in code:
#   from django.urls import reverse
#   url = reverse('activity-list')
#   url = reverse('activity-detail', kwargs={'pk': activity_id})
#   url = reverse('activity-summary')

# API Documentation:
# With DRF's browsable API, navigating to these URLs in a browser
# provides interactive documentation and testing interface

# Future endpoints to add:
# - /dashboard/ - Combined analytics dashboard
# - /leaderboard/ - Student rankings
# - /trends/ - Time-series analytics
# - /comparisons/ - Peer comparisons
# - /reports/ - Downloadable reports
