"""
2026-03-04: Communication Service URL configuration (BS-COM-001/002/003, BS-PAR-006).

Mounted at /api/v1/comms/ in backend/urls.py.
"""

from django.urls import path

from .views import (
    ThreadListCreateView, ThreadDetailView, SendMessageView, MarkThreadReadView,
    AnnouncementView,
    WeeklyReportListView, GenerateWeeklyReportView,
    TermReportListView, GenerateTermReportView, TermReportDetailView,
)

urlpatterns = [
    # 2026-03-04: Messaging (BS-COM-001)
    path('threads/', ThreadListCreateView.as_view(), name='comms-threads'),
    path('threads/<uuid:thread_id>/', ThreadDetailView.as_view(), name='comms-thread-detail'),
    path('threads/<uuid:thread_id>/send/', SendMessageView.as_view(), name='comms-thread-send'),
    path('threads/<uuid:thread_id>/read/', MarkThreadReadView.as_view(), name='comms-thread-read'),

    # 2026-03-04: Announcements (BS-COM-002)
    path('announcements/', AnnouncementView.as_view(), name='comms-announcements'),

    # 2026-03-04: Weekly Reports (BS-COM-003)
    path('weekly-reports/<uuid:student_id>/', WeeklyReportListView.as_view(), name='comms-weekly-reports'),
    path('weekly-reports/generate/', GenerateWeeklyReportView.as_view(), name='comms-weekly-generate'),

    # 2026-03-04: Term Reports (BS-PAR-006)
    path('term-reports/<uuid:student_id>/', TermReportListView.as_view(), name='comms-term-reports'),
    path('term-reports/generate/', GenerateTermReportView.as_view(), name='comms-term-generate'),
    path('term-reports/<uuid:student_id>/<str:year>/<str:term>/', TermReportDetailView.as_view(), name='comms-term-detail'),
]
