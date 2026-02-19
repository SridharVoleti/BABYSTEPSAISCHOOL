"""
2026-02-19: Parent Dashboard URL configuration.

Purpose:
    URL patterns for parent dashboard endpoints (BS-PAR module).
    All routes are parent-only and use JWT authentication.
"""

from django.urls import path  # 2026-02-19: URL routing

from .views import (  # 2026-02-19: Import views
    DashboardView,
    ProgressDetailView,
    ParentalControlsView,
    ConversationLogView,
)

urlpatterns = [
    # 2026-02-19: Overview of all children's learning progress
    path('dashboard/', DashboardView.as_view(), name='parent-dashboard'),

    # 2026-02-19: Per-student subject drill-down
    path(
        'progress/<uuid:student_id>/',
        ProgressDetailView.as_view(),
        name='parent-progress-detail',
    ),

    # 2026-02-19: Get/update parental controls per student
    path(
        'controls/<uuid:student_id>/',
        ParentalControlsView.as_view(),
        name='parent-controls',
    ),

    # 2026-02-19: AI tutoring conversation log per student
    path(
        'conversation-log/<uuid:student_id>/',
        ConversationLogView.as_view(),
        name='parent-conversation-log',
    ),
]
