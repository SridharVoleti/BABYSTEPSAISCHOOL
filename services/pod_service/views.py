"""
2026-03-04: Pod Management & Monitoring API views (BS-POD + BS-MON).

Purpose:
    DRF views for pod listing/detail, enrollment, heartbeat,
    attention events, help requests, and monitor dashboard.

Auth:
    - Pod listing/detail/enroll/unenroll: staff (monitor) only
    - Heartbeat / attention / help: authenticated student
    - Monitor dashboard: staff only
"""

import logging  # 2026-03-04: Module logger

from rest_framework import status  # 2026-03-04: HTTP status codes
from rest_framework.permissions import IsAuthenticated, IsAdminUser  # 2026-03-04: Permissions
from rest_framework.response import Response  # 2026-03-04: API responses
from rest_framework.views import APIView  # 2026-03-04: Class-based views

from services.auth_service.models import Student  # 2026-03-04: Student model
from .models import Pod, PodEnrollment, MonitorAlert  # 2026-03-04: Models
from .serializers import (  # 2026-03-04: Input validators
    AttentionEventSerializer, HelpRequestSerializer,
    EnrollStudentSerializer, ResolveAlertSerializer,
)
from .services import PodService, AlertService  # 2026-03-04: Business logic

logger = logging.getLogger(__name__)  # 2026-03-04: Module logger


def _get_student(request):
    """
    2026-03-04: Extract the Student model from an authenticated request.

    Args:
        request: Authenticated HTTP request (JWT with student role).

    Returns:
        tuple: (Student, error_response) — one will be None.
    """
    try:
        student = request.user.student_profile  # 2026-03-04: OneToOne from User→Student
        return student, None
    except Exception:  # 2026-03-04: No student profile
        return None, Response(
            {'error': 'Student profile not found.'},
            status=status.HTTP_403_FORBIDDEN,
        )


class PodListView(APIView):
    """
    2026-03-04: GET /api/v1/pods/ — list all pods with real-time status.

    Staff (monitor) access only. Returns all active pods with traffic-light
    status and per-student activity summaries.
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Monitor/admin only

    def get(self, request):
        """2026-03-04: Return all pod statuses for monitor dashboard."""
        statuses = PodService.list_all_pod_statuses()  # 2026-03-04: Compute statuses
        return Response({'pods': statuses}, status=status.HTTP_200_OK)


class PodDetailView(APIView):
    """
    2026-03-04: GET /api/v1/pods/{pod_id}/ — pod detail + enrolled students.

    Staff access only.
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Monitor/admin only

    def get(self, request, pod_id):
        """2026-03-04: Return single pod status."""
        pod_status = PodService.get_pod_status(pod_id)  # 2026-03-04: Compute
        if not pod_status:
            return Response(
                {'error': 'Pod not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(pod_status, status=status.HTTP_200_OK)


class PodEnrollView(APIView):
    """
    2026-03-04: POST /api/v1/pods/{pod_id}/enroll/ — add student to pod.

    Admin only. Body: {student_id: UUID}
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Admin only

    def post(self, request, pod_id):
        """2026-03-04: Enroll a student in the pod."""
        serializer = EnrollStudentSerializer(data=request.data)  # 2026-03-04: Validate
        serializer.is_valid(raise_exception=True)

        result = PodService.enroll_student(  # 2026-03-04: Business logic
            pod_id=pod_id,
            student_id=str(serializer.validated_data['student_id']),
        )

        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        if result.get('code') == 'POD_FULL':
            return Response(result, status=status.HTTP_409_CONFLICT)
        if result.get('code') == 'ALREADY_ENROLLED':
            return Response(result, status=status.HTTP_409_CONFLICT)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class PodUnenrollView(APIView):
    """
    2026-03-04: POST /api/v1/pods/{pod_id}/unenroll/ — remove student from pod.

    Admin only. Body: {student_id: UUID}
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Admin only

    def post(self, request, pod_id):
        """2026-03-04: Unenroll a student from the pod."""
        serializer = EnrollStudentSerializer(data=request.data)  # 2026-03-04: Validate
        serializer.is_valid(raise_exception=True)

        result = PodService.unenroll_student(  # 2026-03-04: Business logic
            pod_id=pod_id,
            student_id=str(serializer.validated_data['student_id']),
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class HeartbeatView(APIView):
    """
    2026-03-04: POST /api/v1/pods/heartbeat/ — student pings every 30s.

    Authenticated student sends heartbeat to indicate they are active.
    Updates last_heartbeat on their StudentSession.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Student must be logged in

    def post(self, request):
        """2026-03-04: Record heartbeat for the logged-in student."""
        student, error = _get_student(request)  # 2026-03-04: Get student
        if error:
            return error  # 2026-03-04: Return 403 if not student

        result = PodService.record_heartbeat(student)  # 2026-03-04: Business logic
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class AttentionEventView(APIView):
    """
    2026-03-04: POST /api/v1/pods/attention-event/ — report a camera/attention event.

    Authenticated student reports a detected attention anomaly.
    Body: {event_type, ai_response, escalated}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Student must be logged in

    def post(self, request):
        """2026-03-04: Record an attention event for the logged-in student."""
        student, error = _get_student(request)  # 2026-03-04: Get student
        if error:
            return error  # 2026-03-04: Return 403

        serializer = AttentionEventSerializer(data=request.data)  # 2026-03-04: Validate
        serializer.is_valid(raise_exception=True)

        result = PodService.record_attention_event(  # 2026-03-04: Business logic
            student=student,
            **serializer.validated_data,
        )

        # 2026-03-04: If escalated, also send parent alert
        if serializer.validated_data.get('escalated'):
            AlertService.send_parent_alert(  # 2026-03-04: Parent notification
                student=student,
                alert_type='not_focusing',
            )

        return Response(result, status=status.HTTP_201_CREATED)


class HelpRequestView(APIView):
    """
    2026-03-04: POST /api/v1/pods/help-request/ — student presses Need Help.

    Creates a MonitorAlert of type 'help_request'.
    Body: {message: str (optional)}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-04: Student must be logged in

    def post(self, request):
        """2026-03-04: Record a help request for the logged-in student."""
        student, error = _get_student(request)  # 2026-03-04: Get student
        if error:
            return error  # 2026-03-04: Return 403

        serializer = HelpRequestSerializer(data=request.data)  # 2026-03-04: Validate
        serializer.is_valid(raise_exception=True)

        result = AlertService.create_help_request(  # 2026-03-04: Business logic
            student=student,
            message=serializer.validated_data.get('message') or None,
        )
        return Response(result, status=status.HTTP_201_CREATED)


class MonitorDashboardView(APIView):
    """
    2026-03-04: GET /api/v1/pods/monitor-dashboard/ — real-time pod grid.

    Staff access only. Returns all pod statuses + unresolved alerts
    for the monitor to display in the dashboard UI.
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Monitor/admin only

    def get(self, request):
        """2026-03-04: Return monitor dashboard data."""
        pod_statuses = PodService.list_all_pod_statuses()  # 2026-03-04: All pods

        # 2026-03-04: Unresolved alerts for the alert panel
        alerts = AlertService.get_unresolved_alerts()  # 2026-03-04: Unresolved
        alert_list = [  # 2026-03-04: Serialise alerts
            {
                'id': a.id,  # 2026-03-04: Integer PK (BigAutoField)
                'student_name': a.student.full_name,
                'alert_type': a.alert_type,
                'message': a.message,
                'created_at': a.created_at.isoformat(),
            }
            for a in alerts[:50]  # 2026-03-04: Limit to 50 most recent
        ]

        return Response({  # 2026-03-04: Dashboard payload
            'pods': pod_statuses,
            'alerts': alert_list,
            'unresolved_count': alerts.count(),
        }, status=status.HTTP_200_OK)


class ResolveAlertView(APIView):
    """
    2026-03-04: POST /api/v1/pods/resolve-alert/ — mark an alert as resolved.

    Staff access only. Body: {alert_id: UUID}
    """

    permission_classes = [IsAdminUser]  # 2026-03-04: Monitor/admin only

    def post(self, request):
        """2026-03-04: Resolve the given alert."""
        serializer = ResolveAlertSerializer(data=request.data)  # 2026-03-04: Validate
        serializer.is_valid(raise_exception=True)

        result = AlertService.resolve_alert(  # 2026-03-04: Business logic
            alert_id=serializer.validated_data['alert_id']  # 2026-03-04: Integer PK
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class MonitorLoginView(APIView):
    """
    2026-03-04: POST /api/v1/auth/monitor-login/ — monitor username/password login.

    Staff users log in with Django username + password.
    Returns JWT tokens with role='monitor' in claims.
    """

    permission_classes = []  # 2026-03-04: Public — no auth needed to login

    def post(self, request):
        """2026-03-04: Authenticate a monitor user and return JWT tokens."""
        from django.contrib.auth import authenticate  # 2026-03-04: Django auth
        from rest_framework_simplejwt.tokens import RefreshToken  # 2026-03-04: JWT

        username = request.data.get('username', '').strip()  # 2026-03-04: Username
        password = request.data.get('password', '')  # 2026-03-04: Password

        if not username or not password:  # 2026-03-04: Both required
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=username, password=password)  # 2026-03-04: Auth
        if user is None:  # 2026-03-04: Wrong credentials
            return Response(
                {'error': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_staff:  # 2026-03-04: Must be staff to monitor
            return Response(
                {'error': 'Monitor access requires staff privileges.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # 2026-03-04: Generate JWT tokens with monitor role claim
        refresh = RefreshToken.for_user(user)  # 2026-03-04: Create token pair
        refresh['role'] = 'monitor'  # 2026-03-04: Custom claim
        refresh['username'] = user.username  # 2026-03-04: Include username

        return Response({  # 2026-03-04: Return tokens
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'role': 'monitor',
            'username': user.username,
        }, status=status.HTTP_200_OK)
