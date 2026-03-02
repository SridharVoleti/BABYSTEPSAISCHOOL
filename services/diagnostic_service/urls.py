"""
2026-02-12: Diagnostic assessment service URL configuration.

Purpose:
    Route diagnostic API endpoints to views.
    Mounted at /api/v1/diagnostic/ in backend/urls.py.
"""

from django.urls import path  # 2026-02-12: URL routing

from .views import (  # 2026-02-12: Views
    DiagnosticStartView,
    DiagnosticRespondView,
    DiagnosticStatusView,
    DiagnosticResultView,
    IQReassessmentHistoryView,  # 2026-02-27: Reassessment history
)

# 2026-02-12: URL patterns
urlpatterns = [
    path('start/', DiagnosticStartView.as_view(), name='diagnostic-start'),
    path('respond/', DiagnosticRespondView.as_view(), name='diagnostic-respond'),
    path('status/', DiagnosticStatusView.as_view(), name='diagnostic-status'),
    path('result/', DiagnosticResultView.as_view(), name='diagnostic-result'),
    path(  # 2026-02-27: IQ reassessment history endpoint
        'reassessment/history/',
        IQReassessmentHistoryView.as_view(),
        name='iq-reassessment-history',
    ),
]
