"""
2026-02-12: Diagnostic assessment service views.

Purpose:
    DRF views for diagnostic endpoints: start session, submit response,
    check status, and retrieve final result.
"""

from rest_framework import status  # 2026-02-12: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-12: Auth required
from rest_framework.response import Response  # 2026-02-12: API responses
from rest_framework.views import APIView  # 2026-02-12: Class-based views

from services.auth_service.models import Student  # 2026-02-12: Student model
from .serializers import DiagnosticRespondSerializer  # 2026-02-12: Serializers
from .services import DiagnosticService  # 2026-02-12: Business logic


def _get_student(request):
    """
    2026-02-12: Extract student from authenticated request.

    Args:
        request: HTTP request with authenticated user.

    Returns:
        tuple: (student, error_response) - one will be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-02-12: Must be student
        return None, Response(
            {'error': 'Only students can access diagnostic assessments.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None  # 2026-02-12: Return student


class DiagnosticStartView(APIView):
    """
    2026-02-12: Start a new diagnostic assessment session.

    POST /api/v1/diagnostic/start/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-12: Student auth required

    def post(self, request):
        """2026-02-12: Start or resume a diagnostic session."""
        student, error = _get_student(request)  # 2026-02-12: Get student
        if error:
            return error

        result = DiagnosticService.start_session(student)  # 2026-02-12: Business logic

        if result['success']:  # 2026-02-12: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class DiagnosticRespondView(APIView):
    """
    2026-02-12: Submit a response and get next item or final result.

    POST /api/v1/diagnostic/respond/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-12: Student auth required

    def post(self, request):
        """2026-02-12: Process a diagnostic response."""
        student, error = _get_student(request)  # 2026-02-12: Get student
        if error:
            return error

        serializer = DiagnosticRespondSerializer(data=request.data)  # 2026-02-12: Validate
        serializer.is_valid(raise_exception=True)

        result = DiagnosticService.process_response(  # 2026-02-12: Business logic
            student=student,
            item_id=serializer.validated_data['item_id'],
            selected_option=serializer.validated_data['selected_option'],
            response_time_ms=serializer.validated_data.get('response_time_ms', 0),
        )

        if result['success']:  # 2026-02-12: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class DiagnosticStatusView(APIView):
    """
    2026-02-12: Get current diagnostic session status.

    GET /api/v1/diagnostic/status/
    Used for page refresh recovery.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-12: Student auth required

    def get(self, request):
        """2026-02-12: Get current session status."""
        student, error = _get_student(request)  # 2026-02-12: Get student
        if error:
            return error

        result = DiagnosticService.get_status(student)  # 2026-02-12: Business logic
        return Response(result, status=status.HTTP_200_OK)


class DiagnosticResultView(APIView):
    """
    2026-02-12: Get completed diagnostic result.

    GET /api/v1/diagnostic/result/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-12: Student auth required

    def get(self, request):
        """2026-02-12: Get diagnostic result."""
        student, error = _get_student(request)  # 2026-02-12: Get student
        if error:
            return error

        result = DiagnosticService.get_result(student)  # 2026-02-12: Business logic

        if result['success']:  # 2026-02-12: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)
