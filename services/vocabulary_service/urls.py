# 2026-02-20: Vocabulary Acquisition System URL routing (BS-LNG).
# All routes mounted under /api/v1/vocabulary/ in backend/urls.py.

from django.urls import path  # 2026-02-20: URL routing

from .views import (  # 2026-02-20: View classes
    TodaySessionView,
    RecordPronunciationView,
    RecordMCQView,
    CompleteSessionView,
    ProgressView,
)

urlpatterns = [
    # 2026-02-20: GET today's session (or create it)
    path('session/', TodaySessionView.as_view(), name='vocab-today-session'),

    # 2026-02-20: POST pronunciation score for a word
    path(
        'session/<uuid:session_id>/word/<uuid:word_id>/pronunciation/',
        RecordPronunciationView.as_view(),
        name='vocab-record-pronunciation',
    ),

    # 2026-02-20: POST MCQ answer for a word
    path(
        'session/<uuid:session_id>/word/<uuid:word_id>/mcq/',
        RecordMCQView.as_view(),
        name='vocab-record-mcq',
    ),

    # 2026-02-20: POST to finalize session
    path(
        'session/<uuid:session_id>/complete/',
        CompleteSessionView.as_view(),
        name='vocab-complete-session',
    ),

    # 2026-02-20: GET progress stats for a language
    path('progress/', ProgressView.as_view(), name='vocab-progress'),
]
