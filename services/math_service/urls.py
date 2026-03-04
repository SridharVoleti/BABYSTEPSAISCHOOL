"""
2026-03-02: URL configuration for Math Service (BS-MTH module).

Routes:
    GET  lessons/                         → LessonListView
    GET  lessons/{lesson_id}/             → LessonDetailView
    POST sessions/                        → StartSessionView
    GET  sessions/{session_id}/           → SessionStatusView
    POST sessions/{session_id}/answer/    → SubmitAnswerView
    POST sessions/{session_id}/hint/      → RequestHintView
    GET  progress/                        → MathProgressView

    BS-AMT-001 AI Math Tutor (teaching phase):
    GET  sessions/{session_id}/teach/          → TeachingSessionView
    POST sessions/{session_id}/teach/chat/     → TeachingChatView
    POST sessions/{session_id}/teach/complete/ → TeachingCompleteView

    AMT-APE-005 Mental Maths Drills:
    POST drills/                              → StartDrillView
    GET  drills/history/                      → DrillHistoryView
    GET  drills/{session_id}/                 → DrillStatusView
    POST drills/{session_id}/answer/          → SubmitDrillAnswerView
    POST drills/{session_id}/complete/        → CompleteDrillView
"""

from django.urls import path  # 2026-03-02: URL router

from .views import (  # 2026-03-02: Import all views
    LessonListView,
    LessonDetailView,
    StartSessionView,
    SessionStatusView,
    SubmitAnswerView,
    RequestHintView,
    MathProgressView,
    TeachingSessionView,
    TeachingChatView,
    TeachingCompleteView,
    StartDrillView,  # 2026-03-03: AMT-APE-005 drill views
    DrillStatusView,
    SubmitDrillAnswerView,
    CompleteDrillView,
    DrillHistoryView,
)

urlpatterns = [  # 2026-03-02: URL patterns
    # 2026-03-02: Lesson endpoints
    path('lessons/', LessonListView.as_view(), name='math-lesson-list'),
    path('lessons/<str:lesson_id>/', LessonDetailView.as_view(), name='math-lesson-detail'),

    # 2026-03-02: Session endpoints
    path('sessions/', StartSessionView.as_view(), name='math-session-start'),
    path('sessions/<uuid:session_id>/', SessionStatusView.as_view(), name='math-session-status'),
    path('sessions/<uuid:session_id>/answer/', SubmitAnswerView.as_view(), name='math-session-answer'),
    path('sessions/<uuid:session_id>/hint/', RequestHintView.as_view(), name='math-session-hint'),

    # 2026-03-02: BS-AMT-001 AI Math Tutor teaching phase endpoints
    path('sessions/<uuid:session_id>/teach/', TeachingSessionView.as_view(), name='math-teach-session'),
    path('sessions/<uuid:session_id>/teach/chat/', TeachingChatView.as_view(), name='math-teach-chat'),
    path('sessions/<uuid:session_id>/teach/complete/', TeachingCompleteView.as_view(), name='math-teach-complete'),

    # 2026-03-03: AMT-APE-005 Mental Maths Drill endpoints
    # Note: 'drills/history/' must come before 'drills/<uuid>/' to avoid UUID parse conflict
    path('drills/', StartDrillView.as_view(), name='math-drill-start'),
    path('drills/history/', DrillHistoryView.as_view(), name='math-drill-history'),
    path('drills/<uuid:session_id>/', DrillStatusView.as_view(), name='math-drill-status'),
    path('drills/<uuid:session_id>/answer/', SubmitDrillAnswerView.as_view(), name='math-drill-answer'),
    path('drills/<uuid:session_id>/complete/', CompleteDrillView.as_view(), name='math-drill-complete'),

    # 2026-03-02: Progress endpoint
    path('progress/', MathProgressView.as_view(), name='math-progress'),
]
