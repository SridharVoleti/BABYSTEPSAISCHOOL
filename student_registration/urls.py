"""
Student Registration URLs
Author: Cascade AI
Date: 2025-12-13
Description: URL routing for student registration API endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudentRegistrationViewSet

# Create router and register viewset
router = DefaultRouter()
router.register(r'registrations', StudentRegistrationViewSet, basename='studentregistration')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]
