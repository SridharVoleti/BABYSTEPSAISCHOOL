"""
2026-02-19: Parent Dashboard API views.

Purpose:
    DRF views for parent-only endpoints: dashboard overview,
    progress detail, parental controls, and conversation log.
"""

from rest_framework import status  # 2026-02-19: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-19: Auth check
from rest_framework.response import Response  # 2026-02-19: API response
from rest_framework.views import APIView  # 2026-02-19: Class-based views

from .serializers import ParentalControlsUpdateSerializer  # 2026-02-19: Input validation
from .services import ParentDashboardService  # 2026-02-19: Business logic


def _get_parent(request):
    """
    2026-02-19: Extract parent from authenticated request.

    Args:
        request: HTTP request with authenticated user.

    Returns:
        tuple: (parent, error_response) — one will be None.
    """
    if not hasattr(request.user, 'parent_profile'):  # 2026-02-19: Must be parent
        return None, Response(
            {'error': 'Only parents can access this endpoint.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.parent_profile, None  # 2026-02-19: Return parent


def _get_owned_student(parent, student_id):
    """
    2026-02-19: Verify that student_id belongs to this parent.

    Args:
        parent: Parent model instance.
        student_id: UUID string from URL.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    student = parent.students.filter(id=student_id, is_active=True).first()
    if not student:  # 2026-02-19: Not owned or not found
        return None, Response(
            {'error': 'Student not found or access denied.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return student, None  # 2026-02-19: Verified ownership


class DashboardView(APIView):
    """
    2026-02-19: Parent dashboard overview — all children progress.

    GET /api/v1/parent/dashboard/
    Returns streak, stars, and activity summary per child.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request):
        """2026-02-19: Return aggregated progress for all active children."""
        parent, error = _get_parent(request)  # 2026-02-19: Verify parent
        if error:
            return error

        data = ParentDashboardService.get_dashboard(parent)  # 2026-02-19: Aggregate
        return Response(data, status=status.HTTP_200_OK)


class ProgressDetailView(APIView):
    """
    2026-02-19: Per-student progress drill-down.

    GET /api/v1/parent/progress/{student_id}/
    Returns subjects → lessons → day star ratings.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request, student_id):
        """2026-02-19: Return subject drill-down for one child."""
        parent, error = _get_parent(request)  # 2026-02-19: Verify parent
        if error:
            return error

        data = ParentDashboardService.get_progress_detail(parent, student_id)
        if data is None:  # 2026-02-19: Not owned
            return Response(
                {'error': 'Student not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)


class ParentalControlsView(APIView):
    """
    2026-02-19: Get/update parental controls for a student.

    GET  /api/v1/parent/controls/{student_id}/
    PUT  /api/v1/parent/controls/{student_id}/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request, student_id):
        """2026-02-19: Return current parental controls (creates defaults if needed)."""
        parent, error = _get_parent(request)  # 2026-02-19: Verify parent
        if error:
            return error

        controls = ParentDashboardService.get_parental_controls(parent, student_id)
        if controls is None:  # 2026-02-19: Not owned
            return Response(
                {'error': 'Student not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._serialize_controls(controls), status=status.HTTP_200_OK)

    def put(self, request, student_id):
        """2026-02-19: Update parental controls (partial update)."""
        parent, error = _get_parent(request)  # 2026-02-19: Verify parent
        if error:
            return error

        serializer = ParentalControlsUpdateSerializer(data=request.data)  # 2026-02-19: Validate
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        controls = ParentDashboardService.update_parental_controls(
            parent, student_id, serializer.validated_data
        )
        if controls is None:  # 2026-02-19: Not owned
            return Response(
                {'error': 'Student not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(self._serialize_controls(controls), status=status.HTTP_200_OK)

    @staticmethod
    def _serialize_controls(controls):
        """
        2026-02-19: Serialize ParentalControls to dict.

        Args:
            controls: ParentalControls instance.

        Returns:
            dict: Serialized controls data.
        """
        return {
            'student_id': str(controls.student_id),
            'daily_time_limit_minutes': controls.daily_time_limit_minutes,
            'schedule_enabled': controls.schedule_enabled,
            'schedule_start_time': (
                controls.schedule_start_time.strftime('%H:%M')
                if controls.schedule_start_time else None
            ),
            'schedule_end_time': (
                controls.schedule_end_time.strftime('%H:%M')
                if controls.schedule_end_time else None
            ),
            'ai_log_enabled': controls.ai_log_enabled,
        }


class ConversationLogView(APIView):
    """
    2026-02-19: Return AI tutoring conversation log for a student.

    GET /api/v1/parent/conversation-log/{student_id}/
    Parents can always view conversation logs.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request, student_id):
        """2026-02-19: Return all tutoring sessions for a child."""
        parent, error = _get_parent(request)  # 2026-02-19: Verify parent
        if error:
            return error

        data = ParentDashboardService.get_conversation_log(parent, student_id)
        if data is None:  # 2026-02-19: Not owned
            return Response(
                {'error': 'Student not found or access denied.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data, status=status.HTTP_200_OK)
