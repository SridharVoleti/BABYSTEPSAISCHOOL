"""
2026-03-04: Pod Service URL configuration (BS-POD + BS-MON).

Purpose:
    Route pod API endpoints. Mounted at /api/v1/pods/ in backend/urls.py.

Endpoints:
    GET  pods/                      → PodListView (monitor)
    GET  pods/{id}/                 → PodDetailView (monitor)
    POST pods/{id}/enroll/          → PodEnrollView (admin)
    POST pods/{id}/unenroll/        → PodUnenrollView (admin)
    POST pods/heartbeat/            → HeartbeatView (student)
    POST pods/attention-event/      → AttentionEventView (student)
    POST pods/help-request/         → HelpRequestView (student)
    GET  pods/monitor-dashboard/    → MonitorDashboardView (monitor)
    POST pods/resolve-alert/        → ResolveAlertView (monitor)
"""

from django.urls import path  # 2026-03-04: URL routing

from .views import (  # 2026-03-04: Views
    PodListView, PodDetailView, PodEnrollView, PodUnenrollView,
    HeartbeatView, AttentionEventView, HelpRequestView,
    MonitorDashboardView, ResolveAlertView,
)

# 2026-03-04: URL patterns for pod_service
urlpatterns = [
    # 2026-03-04: Monitor-facing pod endpoints
    path('', PodListView.as_view(), name='pod-list'),
    path('<uuid:pod_id>/', PodDetailView.as_view(), name='pod-detail'),
    path('<uuid:pod_id>/enroll/', PodEnrollView.as_view(), name='pod-enroll'),
    path('<uuid:pod_id>/unenroll/', PodUnenrollView.as_view(), name='pod-unenroll'),

    # 2026-03-04: Student-facing activity endpoints
    path('heartbeat/', HeartbeatView.as_view(), name='pod-heartbeat'),
    path('attention-event/', AttentionEventView.as_view(), name='pod-attention-event'),
    path('help-request/', HelpRequestView.as_view(), name='pod-help-request'),

    # 2026-03-04: Monitor dashboard and alert management
    path('monitor-dashboard/', MonitorDashboardView.as_view(), name='pod-monitor-dashboard'),
    path('resolve-alert/', ResolveAlertView.as_view(), name='pod-resolve-alert'),
]
