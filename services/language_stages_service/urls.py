"""
2026-03-02: URL configuration for Language Stages Service (BS-LNG-005).

Mounted at: /api/v1/language-stages/
"""

from django.urls import path  # 2026-03-02: URL pattern

from .views import (  # 2026-03-02: Views
    ScenarioListView,
    SessionStartView,
    SessionTurnView,
    SessionCompleteView,
    ProgressView,
)

urlpatterns = [
    # 2026-03-02: GET /api/v1/language-stages/scenarios/?language=Hindi
    path('scenarios/', ScenarioListView.as_view(), name='language-stages-scenarios'),

    # 2026-03-02: POST /api/v1/language-stages/session/start/
    path('session/start/', SessionStartView.as_view(), name='language-stages-session-start'),

    # 2026-03-02: POST /api/v1/language-stages/session/<session_id>/turn/
    path(
        'session/<uuid:session_id>/turn/',
        SessionTurnView.as_view(),
        name='language-stages-session-turn',
    ),

    # 2026-03-02: POST /api/v1/language-stages/session/<session_id>/complete/
    path(
        'session/<uuid:session_id>/complete/',
        SessionCompleteView.as_view(),
        name='language-stages-session-complete',
    ),

    # 2026-03-02: GET /api/v1/language-stages/progress/?language=Hindi
    path('progress/', ProgressView.as_view(), name='language-stages-progress'),
]
