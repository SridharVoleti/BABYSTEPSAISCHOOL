"""
2026-03-04: Attendance Service URL configuration (BS-ATT).

Mounted at /api/v1/attendance/ in backend/urls.py.
"""

from django.urls import path  # 2026-03-04: URL routing

from .views import (  # 2026-03-04: Views
    CheckinView,
    CheckoutView,
    MarkAttendanceView,
    BulkMarkAttendanceView,
    DailyClassRosterView,
    StudentAttendanceHistoryView,
    AttendanceSummaryView,
)

urlpatterns = [
    # 2026-03-04: Student self-service
    path('checkin/', CheckinView.as_view(), name='attendance-checkin'),
    path('checkout/', CheckoutView.as_view(), name='attendance-checkout'),

    # 2026-03-04: Monitor manual marking
    path('mark/', MarkAttendanceView.as_view(), name='attendance-mark'),
    path('bulk-mark/', BulkMarkAttendanceView.as_view(), name='attendance-bulk-mark'),

    # 2026-03-04: Monitor class roster
    path('daily/', DailyClassRosterView.as_view(), name='attendance-daily'),

    # 2026-03-04: Parent/monitor student views
    path('student/<uuid:student_id>/', StudentAttendanceHistoryView.as_view(), name='attendance-student-history'),
    path('summary/<uuid:student_id>/', AttendanceSummaryView.as_view(), name='attendance-summary'),
]
