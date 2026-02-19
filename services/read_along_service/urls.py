"""
2026-02-19: URL configuration for Read-Along & Mimic Engine (BS-RAM).
"""

from django.urls import path  # 2026-02-19: URL routing

from .views import ContentView, SubmitSessionView, HistoryView  # 2026-02-19: Views

urlpatterns = [
    # 2026-02-19: Get read-along content for a lesson day
    path(
        'lessons/<uuid:lesson_id>/day/<int:day_number>/content/',
        ContentView.as_view(),
        name='read-along-content',
    ),
    # 2026-02-19: Submit a completed read-along session
    path(
        'sessions/submit/',
        SubmitSessionView.as_view(),
        name='read-along-submit',
    ),
    # 2026-02-19: Get session history
    path(
        'sessions/history/',
        HistoryView.as_view(),
        name='read-along-history',
    ),
]
