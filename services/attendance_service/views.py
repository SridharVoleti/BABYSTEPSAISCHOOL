"""
2026-03-04: Attendance Service API views (BS-ATT).

Purpose:
    REST endpoints for attendance marking, retrieval, and reporting.
    Students auto-checkin on login; monitors mark manually.

Endpoints:
    POST /api/v1/attendance/checkin/           — student auto-checkin
    POST /api/v1/attendance/checkout/          — student checkout
    POST /api/v1/attendance/mark/              — monitor marks individual
    POST /api/v1/attendance/bulk-mark/         — monitor marks whole class
    GET  /api/v1/attendance/daily/             — monitor: today's class roster
    GET  /api/v1/attendance/student/{id}/      — parent/monitor: student history
    GET  /api/v1/attendance/summary/{id}/      — parent/monitor: monthly summary
"""

from datetime import date  # 2026-03-04: Date objects

from django.utils import timezone  # 2026-03-04: Timezone-aware dates
from rest_framework import status  # 2026-03-04: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-03-04: Auth
from rest_framework.response import Response  # 2026-03-04: DRF response
from rest_framework.views import APIView  # 2026-03-04: Class-based views

from services.auth_service.models import Student  # 2026-03-04: Student model

from .models import AttendanceRecord  # 2026-03-04: Model
from .serializers import (  # 2026-03-04: Serializers
    AttendanceRecordSerializer,
    MarkAttendanceSerializer,
    BulkMarkAttendanceSerializer,
    AttendanceSummaryQuerySerializer,
    ClassAttendanceQuerySerializer,
)
from .services import AttendanceService  # 2026-03-04: Business logic


def _get_student(request):
    """2026-03-04: Return (student, None) or (None, error_response)."""
    if not hasattr(request.user, 'student_profile'):
        return None, Response(
            {'error': 'Student authentication required.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None


def _get_parent(request):
    """2026-03-04: Return (parent, None) or (None, error_response)."""
    if not hasattr(request.user, 'parent_profile'):
        return None, Response(
            {'error': 'Parent authentication required.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.parent_profile, None


def _is_monitor(request) -> bool:
    """2026-03-04: True if the requesting user is a Django staff (monitor)."""
    return request.user.is_authenticated and request.user.is_staff


class CheckinView(APIView):
    """
    2026-03-04: Auto-checkin endpoint called when a student logs in.

    POST /api/v1/attendance/checkin/
    Requires: student JWT
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Mark student present for today."""
        student, error = _get_student(request)
        if error:
            return error
        record = AttendanceService.auto_checkin(student)
        return Response(
            {
                'status': record.status,
                'check_in_time': record.check_in_time.isoformat() if record.check_in_time else None,
                'date': str(record.date),
            },
            status=status.HTTP_200_OK,
        )


class CheckoutView(APIView):
    """
    2026-03-04: Checkout endpoint — updates session duration.

    POST /api/v1/attendance/checkout/
    Requires: student JWT
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Record student checkout time."""
        student, error = _get_student(request)
        if error:
            return error
        record = AttendanceService.auto_checkout(student)
        if not record:
            return Response(
                {'error': 'No check-in record found for today.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {
                'status': record.status,
                'session_duration_minutes': record.session_duration_minutes,
            },
            status=status.HTTP_200_OK,
        )


class MarkAttendanceView(APIView):
    """
    2026-03-04: Monitor marks an individual student's attendance.

    POST /api/v1/attendance/mark/
    Requires: monitor (staff) JWT
    Body: {student_id, date, status, notes?}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Mark attendance for one student."""
        if not _is_monitor(request):
            return Response(
                {'error': 'Monitor access required.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = MarkAttendanceSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            student = Student.objects.get(pk=d['student_id'], is_active=True)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        record = AttendanceService.mark_attendance(
            student=student,
            target_date=d['date'],
            status=d['status'],
            notes=d.get('notes', ''),
        )
        return Response(
            AttendanceRecordSerializer(record).data,
            status=status.HTTP_200_OK,
        )


class BulkMarkAttendanceView(APIView):
    """
    2026-03-04: Monitor marks attendance for an entire class in one call.

    POST /api/v1/attendance/bulk-mark/
    Requires: monitor (staff) JWT
    Body: {grade, date, records: [{student_id, status, notes?}, ...]}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def post(self, request):
        """2026-03-04: Bulk mark attendance for a class."""
        if not _is_monitor(request):
            return Response(
                {'error': 'Monitor access required.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = BulkMarkAttendanceSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        target_date = d['date']
        grade = d['grade']
        records_data = d.get('records', [])

        # 2026-03-04: Build override map keyed by student_id string
        override_map = {
            str(r['student_id']): r
            for r in records_data
            if 'student_id' in r and 'status' in r
        }

        students = Student.objects.filter(grade=grade, is_active=True)
        saved_count = 0
        for student in students:
            override = override_map.get(str(student.pk))
            att_status = override.get('status', AttendanceRecord.STATUS_PRESENT) if override else AttendanceRecord.STATUS_PRESENT
            notes = override.get('notes', '') if override else ''
            AttendanceService.mark_attendance(student, target_date, att_status, notes)
            saved_count += 1

        return Response(
            {
                'marked': saved_count,
                'grade': grade,
                'date': str(target_date),
            },
            status=status.HTTP_200_OK,
        )


class DailyClassRosterView(APIView):
    """
    2026-03-04: Monitor views the full attendance roster for a class on a date.

    GET /api/v1/attendance/daily/?grade=6&date=2026-03-04
    Requires: monitor (staff) JWT
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def get(self, request):
        """2026-03-04: Return class attendance roster."""
        if not _is_monitor(request):
            return Response(
                {'error': 'Monitor access required.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        ser = ClassAttendanceQuerySerializer(data=request.query_params)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        grade = ser.validated_data['grade']
        target_date = ser.validated_data.get('date', timezone.localdate())

        roster = AttendanceService.get_class_attendance(grade, target_date)
        return Response(
            {'grade': grade, 'date': str(target_date), 'roster': roster},
            status=status.HTTP_200_OK,
        )


class StudentAttendanceHistoryView(APIView):
    """
    2026-03-04: View a student's attendance history.

    GET /api/v1/attendance/student/{student_id}/?start_date=&end_date=
    Requires: parent (owns student) or monitor
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def get(self, request, student_id):
        """2026-03-04: Return student attendance history."""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-03-04: Authorisation — monitor sees all; parent must own student
        if not _is_monitor(request):
            parent, error = _get_parent(request)
            if error:
                return error
            if student.parent_id != parent.pk:
                return Response(
                    {'error': 'Access denied.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        today = timezone.localdate()
        try:
            start_date = date.fromisoformat(
                request.query_params.get('start_date', str(today.replace(day=1)))
            )
            end_date = date.fromisoformat(
                request.query_params.get('end_date', str(today))
            )
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = AttendanceService.get_student_attendance(student, start_date, end_date)
        return Response(
            {
                'student_id': str(student_id),
                'student_name': student.full_name,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'records': AttendanceRecordSerializer(records, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class AttendanceSummaryView(APIView):
    """
    2026-03-04: Monthly attendance summary for a student.

    GET /api/v1/attendance/summary/{student_id}/?year=2026&month=3
    Requires: parent (owns student) or monitor
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Must be logged in

    def get(self, request, student_id):
        """2026-03-04: Return monthly attendance summary."""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-03-04: Authorisation
        if not _is_monitor(request):
            parent, error = _get_parent(request)
            if error:
                return error
            if student.parent_id != parent.pk:
                return Response(
                    {'error': 'Access denied.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        today = timezone.localdate()
        ser = AttendanceSummaryQuerySerializer(data=request.query_params)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        year = ser.validated_data.get('year', today.year)
        month = ser.validated_data.get('month', today.month)

        summary = AttendanceService.get_attendance_summary(student, year, month)
        summary['student_id'] = str(student_id)
        summary['student_name'] = student.full_name

        return Response(summary, status=status.HTTP_200_OK)
