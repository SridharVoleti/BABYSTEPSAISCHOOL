"""
2026-03-06: URL configuration for Mentor Dashboard Service (BS-MNT).

All routes are under /api/v1/mentor/ (mounted in backend/urls.py).
"""

from django.urls import path  # 2026-03-06: URL routing

from .views import (  # 2026-03-06: View imports
    DraftMessageView,
    GenerateSummaryView,
    MentorDashboardView,
    MentorMessagesView,
    MentorStudentDetailView,
    ReviewQueueView,
    SubmitReviewView,
    WeeklySummaryView,
)

# 2026-03-06: app_namespace for reverse URL lookups
app_name = 'mentor_dashboard_service'

urlpatterns = [
    # 2026-03-06: GET /api/v1/mentor/dashboard/ — student grid
    path('dashboard/', MentorDashboardView.as_view(), name='dashboard'),

    # 2026-03-06: GET /api/v1/mentor/students/<uuid>/ — per-student detail
    path('students/<uuid:student_id>/', MentorStudentDetailView.as_view(), name='student-detail'),

    # 2026-03-06: GET /api/v1/mentor/review-queue/ — un-reviewed comprehension responses
    path('review-queue/', ReviewQueueView.as_view(), name='review-queue'),

    # 2026-03-06: POST /api/v1/mentor/review-queue/<uuid>/ — submit mentor review
    path('review-queue/<uuid:response_id>/', SubmitReviewView.as_view(), name='submit-review'),

    # 2026-03-06: GET /api/v1/mentor/students/<uuid>/summary/ — current-week summary
    path('students/<uuid:student_id>/summary/', WeeklySummaryView.as_view(), name='weekly-summary'),

    # 2026-03-06: POST /api/v1/mentor/students/<uuid>/summary/generate/ — generate summary
    path(
        'students/<uuid:student_id>/summary/generate/',
        GenerateSummaryView.as_view(),
        name='generate-summary',
    ),

    # 2026-03-06: GET /api/v1/mentor/messages/ — all parent threads
    path('messages/', MentorMessagesView.as_view(), name='messages'),

    # 2026-03-06: POST /api/v1/mentor/students/<uuid>/draft-message/ — AI draft
    path(
        'students/<uuid:student_id>/draft-message/',
        DraftMessageView.as_view(),
        name='draft-message',
    ),
]
