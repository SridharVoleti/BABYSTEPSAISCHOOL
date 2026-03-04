"""
2026-03-04: Monitor Tools Service URL configuration (BS-MON-005/006/007).

Mounted at /api/v1/monitor-tools/ in backend/urls.py.
"""

from django.urls import path  # 2026-03-04: URL routing

from .views import (
    # 2026-03-04: Grade Book
    AddGradeView, StudentGradesView, ClassGradesView, ReportCardView,
    # 2026-03-04: Homework
    HomeworkListCreateView, StudentHomeworkView, HomeworkMarkDoneView, HomeworkSubmissionsView,
    # 2026-03-04: Timetable
    TimetableView, TimetableSlotDetailView, TodayScheduleView,
)

urlpatterns = [
    # 2026-03-04: Grade Book (BS-MON-005)
    path('grades/add/', AddGradeView.as_view(), name='monitor-grades-add'),
    path('grades/student/<uuid:student_id>/', StudentGradesView.as_view(), name='monitor-grades-student'),
    path('grades/class/', ClassGradesView.as_view(), name='monitor-grades-class'),
    path('grades/report-card/<uuid:student_id>/', ReportCardView.as_view(), name='monitor-report-card'),

    # 2026-03-04: Homework (BS-MON-006)
    path('homework/', HomeworkListCreateView.as_view(), name='monitor-homework'),
    path('homework/student/', StudentHomeworkView.as_view(), name='monitor-homework-student'),
    path('homework/done/', HomeworkMarkDoneView.as_view(), name='monitor-homework-done'),
    path('homework/<uuid:hw_id>/submissions/', HomeworkSubmissionsView.as_view(), name='monitor-homework-submissions'),

    # 2026-03-04: Timetable (BS-MON-007)
    path('timetable/', TimetableView.as_view(), name='monitor-timetable'),
    path('timetable/today/', TodayScheduleView.as_view(), name='monitor-timetable-today'),
    path('timetable/<uuid:slot_id>/', TimetableSlotDetailView.as_view(), name='monitor-timetable-slot'),
]
