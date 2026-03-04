"""
2026-03-04: Communication Service API views (BS-COM-001/002/003, BS-PAR-006).

Endpoints:
    --- Messaging (BS-COM-001) ---
    POST GET /api/v1/comms/threads/              parent/monitor: list/create threads
    GET      /api/v1/comms/threads/{id}/         thread detail + messages
    POST     /api/v1/comms/threads/{id}/send/    send a message
    POST     /api/v1/comms/threads/{id}/read/    mark messages read

    --- Announcements (BS-COM-002) ---
    GET  /api/v1/comms/announcements/            any auth: list active
    POST /api/v1/comms/announcements/            monitor: create

    --- Weekly Reports (BS-COM-003) ---
    GET  /api/v1/comms/weekly-reports/{student_id}/   parent/monitor: list
    POST /api/v1/comms/weekly-reports/generate/       monitor: trigger generation

    --- Term Reports (BS-PAR-006) ---
    GET  /api/v1/comms/term-reports/{student_id}/     parent/monitor: list
    POST /api/v1/comms/term-reports/generate/         monitor: generate
    GET  /api/v1/comms/term-reports/{student_id}/{year}/{term}/ get specific report
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django.contrib.auth.models import User

from services.auth_service.models import Parent, Student

from .models import MessageThread, TermReport
from .serializers import (
    MessageSerializer, MessageThreadSerializer,
    StartThreadSerializer, SendMessageSerializer,
    AnnouncementSerializer, CreateAnnouncementSerializer,
    WeeklyReportSerializer, GenerateWeeklyReportSerializer,
    TermReportSerializer, GenerateTermReportSerializer,
)
from .services import MessagingService, AnnouncementService, WeeklyReportService, TermReportService


def _is_monitor(request) -> bool:
    """2026-03-04: True if Django staff user."""
    return request.user.is_authenticated and request.user.is_staff


def _get_parent(request):
    """2026-03-04: (parent, None) or (None, error)."""
    if not hasattr(request.user, 'parent_profile'):
        return None, Response({'error': 'Parent auth required.'}, status=status.HTTP_403_FORBIDDEN)
    return request.user.parent_profile, None


def _auth_student_access(request, student):
    """
    2026-03-04: Verify monitor access OR parent owns the student.

    Returns None if OK, or error Response.
    """
    if _is_monitor(request):
        return None
    parent, error = _get_parent(request)
    if error:
        return error
    if student.parent_id != parent.pk:
        return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
    return None


# ============================================================
# Messaging Views (BS-COM-001)
# ============================================================

class ThreadListCreateView(APIView):
    """2026-03-04: GET/POST /api/v1/comms/threads/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """2026-03-04: List threads for the current user."""
        if _is_monitor(request):
            threads = MessagingService.list_threads(monitor=request.user)
        elif hasattr(request.user, 'parent_profile'):
            threads = MessagingService.list_threads(parent=request.user.parent_profile)
        else:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        return Response({'threads': MessageThreadSerializer(threads, many=True).data})

    def post(self, request):
        """2026-03-04: Parent starts a new thread with a monitor."""
        parent, error = _get_parent(request)
        if error:
            return error

        ser = StartThreadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            student = Student.objects.get(pk=d['student_id'], parent=parent)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found or not yours.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            monitor = User.objects.get(pk=d['monitor_id'], is_staff=True)
        except User.DoesNotExist:
            return Response({'error': 'Monitor not found.'}, status=status.HTTP_404_NOT_FOUND)

        thread = MessagingService.get_or_create_thread(
            student=student, parent=parent, monitor=monitor, subject=d.get('subject', '')
        )
        return Response(MessageThreadSerializer(thread).data, status=status.HTTP_201_CREATED)


class ThreadDetailView(APIView):
    """2026-03-04: GET /api/v1/comms/threads/{id}/ — thread + messages."""

    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        """2026-03-04: Return thread and all messages."""
        try:
            thread = MessageThread.objects.get(pk=thread_id)
        except MessageThread.DoesNotExist:
            return Response({'error': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 2026-03-04: Access check
        if _is_monitor(request):
            if thread.monitor != request.user:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        elif hasattr(request.user, 'parent_profile'):
            if thread.parent != request.user.parent_profile:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        messages = thread.messages.all()
        return Response({
            'thread': MessageThreadSerializer(thread).data,
            'messages': MessageSerializer(messages, many=True).data,
        })


class SendMessageView(APIView):
    """2026-03-04: POST /api/v1/comms/threads/{id}/send/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        """2026-03-04: Append a message to the thread."""
        try:
            thread = MessageThread.objects.get(pk=thread_id)
        except MessageThread.DoesNotExist:
            return Response({'error': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 2026-03-04: Determine sender_type
        if _is_monitor(request):
            if thread.monitor != request.user:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
            sender_type = 'monitor'
        elif hasattr(request.user, 'parent_profile'):
            if thread.parent != request.user.parent_profile:
                return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
            sender_type = 'parent'
        else:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        body = request.data.get('body', '').strip()
        if not body:
            return Response({'error': 'body is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            msg = MessagingService.send_message(thread, sender_type, body)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)


class MarkThreadReadView(APIView):
    """2026-03-04: POST /api/v1/comms/threads/{id}/read/"""

    permission_classes = [IsAuthenticated]

    def post(self, request, thread_id):
        """2026-03-04: Mark incoming messages as read."""
        try:
            thread = MessageThread.objects.get(pk=thread_id)
        except MessageThread.DoesNotExist:
            return Response({'error': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)

        if _is_monitor(request):
            reader_type = 'monitor'
        elif hasattr(request.user, 'parent_profile'):
            reader_type = 'parent'
        else:
            return Response({'error': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        count = MessagingService.mark_messages_read(thread, reader_type)
        return Response({'marked_read': count})


# ============================================================
# Announcement Views (BS-COM-002)
# ============================================================

class AnnouncementView(APIView):
    """2026-03-04: GET/POST /api/v1/comms/announcements/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """2026-03-04: List active announcements (grade-aware)."""
        grade = None
        for_parents = hasattr(request.user, 'parent_profile')
        if hasattr(request.user, 'student_profile'):
            grade = request.user.student_profile.grade
        else:
            try:
                grade = int(request.query_params.get('grade', ''))
            except (ValueError, TypeError):
                grade = None

        announcements = AnnouncementService.list_active(grade=grade, for_parents=for_parents)
        return Response({'announcements': AnnouncementSerializer(announcements, many=True).data})

    def post(self, request):
        """2026-03-04: Monitor creates an announcement."""
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = CreateAnnouncementSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        ann = AnnouncementService.create(
            title=d['title'],
            body=d['body'],
            audience=d['audience'],
            grades=d.get('grades', []),
            priority=d['priority'],
            created_by=request.user,
        )
        return Response(AnnouncementSerializer(ann).data, status=status.HTTP_201_CREATED)


# ============================================================
# Weekly Report Views (BS-COM-003)
# ============================================================

class WeeklyReportListView(APIView):
    """2026-03-04: GET /api/v1/comms/weekly-reports/{student_id}/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        """2026-03-04: List weekly reports for a student."""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        error = _auth_student_access(request, student)
        if error:
            return error

        reports = WeeklyReportService.list_reports(student)
        return Response({'reports': WeeklyReportSerializer(reports, many=True).data})


class GenerateWeeklyReportView(APIView):
    """2026-03-04: POST /api/v1/comms/weekly-reports/generate/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """2026-03-04: Monitor triggers weekly report generation."""
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = GenerateWeeklyReportSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            student = Student.objects.get(pk=d['student_id'])
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        report = WeeklyReportService.generate_report(
            student=student,
            week_start=d['week_start'],
            attendance_days=d.get('attendance_days', 0),
            lessons_completed=d.get('lessons_completed', 0),
            avg_star_rating=d.get('avg_star_rating'),
        )
        return Response(WeeklyReportSerializer(report).data, status=status.HTTP_201_CREATED)


# ============================================================
# Term Report Views (BS-PAR-006)
# ============================================================

class TermReportListView(APIView):
    """2026-03-04: GET /api/v1/comms/term-reports/{student_id}/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        """2026-03-04: List all term reports for a student."""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        error = _auth_student_access(request, student)
        if error:
            return error

        reports = TermReportService.list_reports(student)
        return Response({'reports': TermReportSerializer(reports, many=True).data})


class GenerateTermReportView(APIView):
    """2026-03-04: POST /api/v1/comms/term-reports/generate/"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """2026-03-04: Monitor generates a term report for a student."""
        if not _is_monitor(request):
            return Response({'error': 'Monitor access required.'}, status=status.HTTP_403_FORBIDDEN)

        ser = GenerateTermReportSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        d = ser.validated_data
        try:
            student = Student.objects.get(pk=d['student_id'])
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        report = TermReportService.generate(
            student=student,
            academic_year=d['academic_year'],
            term=d['term'],
            generated_by=request.user,
        )
        return Response(TermReportSerializer(report).data, status=status.HTTP_201_CREATED)


class TermReportDetailView(APIView):
    """2026-03-04: GET /api/v1/comms/term-reports/{student_id}/{year}/{term}/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id, year, term):
        """2026-03-04: Fetch a specific term report (also serves as PDF data source)."""
        try:
            student = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        error = _auth_student_access(request, student)
        if error:
            return error

        report = TermReportService.get_report(student, year, term)
        if not report:
            return Response({'error': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(TermReportSerializer(report).data)
