"""
2026-02-12: Authentication service URL configuration.

Purpose:
    Route auth API endpoints to viewsets.
    Mounted at /api/v1/auth/ in backend/urls.py.
"""

from django.urls import path, include  # 2026-02-12: URL routing
from rest_framework.routers import DefaultRouter  # 2026-02-12: DRF router

from .views import (  # 2026-02-12: Viewsets
    AuthViewSet, StudentAuthViewSet, StudentProfileViewSet,
    ConsentViewSet, LanguageViewSet,
    MonitorPasswordResetRequestView, MonitorPasswordResetConfirmView,  # 2026-03-04: Monitor reset
)
from services.pod_service.views import MonitorLoginView  # 2026-03-04: Monitor login

# 2026-02-12: Create router and register viewsets
router = DefaultRouter()
router.register(r'', AuthViewSet, basename='auth')
router.register(r'student-auth', StudentAuthViewSet, basename='student-auth')
router.register(r'students', StudentProfileViewSet, basename='students')
router.register(r'consent', ConsentViewSet, basename='consent')
router.register(r'languages', LanguageViewSet, basename='languages')

# 2026-02-12: URL patterns
urlpatterns = [
    path('', include(router.urls)),  # 2026-02-12: Include all router URLs
    path('monitor-login/', MonitorLoginView.as_view(), name='monitor-login'),  # 2026-03-04: Monitor login
    # 2026-03-04: Monitor password reset (email token flow)
    path('monitor-password-reset/', MonitorPasswordResetRequestView.as_view(), name='monitor-password-reset-request'),
    path('monitor-password-reset/confirm/', MonitorPasswordResetConfirmView.as_view(), name='monitor-password-reset-confirm'),
]
