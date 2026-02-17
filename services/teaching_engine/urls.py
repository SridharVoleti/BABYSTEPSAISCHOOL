"""
2026-02-17: AI Teaching Engine URL configuration.

Purpose:
    Define URL patterns for the teaching engine API endpoints.
"""

from django.urls import path  # 2026-02-17: Django URL path

from .views import (  # 2026-02-17: Views
    LessonListView, LessonDetailView,
    StartDayView, CompleteDayView,
    AssessmentView, SubmitAssessmentView,
    TutoringChatView,
)

app_name = 'teaching_engine'  # 2026-02-17: Namespace

urlpatterns = [  # 2026-02-17: URL patterns
    # 2026-02-17: Lesson listing and detail
    path('lessons/', LessonListView.as_view(), name='lesson-list'),
    path('lessons/<str:lesson_id>/', LessonDetailView.as_view(), name='lesson-detail'),

    # 2026-02-17: Day micro-lesson endpoints
    path('lessons/<str:lesson_id>/start-day/', StartDayView.as_view(), name='start-day'),
    path('lessons/<str:lesson_id>/complete-day/', CompleteDayView.as_view(), name='complete-day'),

    # 2026-02-17: Weekly assessment endpoints
    path('lessons/<str:lesson_id>/assessment/', AssessmentView.as_view(), name='assessment'),
    path('lessons/<str:lesson_id>/submit-assessment/', SubmitAssessmentView.as_view(), name='submit-assessment'),

    # 2026-02-17: Tutoring chat
    path('chat/', TutoringChatView.as_view(), name='tutoring-chat'),
]
