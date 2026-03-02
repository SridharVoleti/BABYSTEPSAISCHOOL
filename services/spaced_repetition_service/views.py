"""
2026-02-27: API views for Spaced Repetition Service (BS-SPC).

Endpoints:
  GET  /api/v1/spaced-repetition/pacing/          — pacing status
  GET  /api/v1/spaced-repetition/reviews/today/   — today's review queue
  POST /api/v1/spaced-repetition/reviews/complete/ — complete one review
"""
from rest_framework import status  # 2026-02-27: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-27: Auth guard
from rest_framework.response import Response  # 2026-02-27: DRF response
from rest_framework.views import APIView  # 2026-02-27: Class-based API view

from .serializers import ReviewCompleteSerializer  # 2026-02-27: Input validation
from .services import SpacedRepetitionService, PacingService  # 2026-02-27: Business logic


def _get_student(request):
    """
    2026-02-27: Extract student from authenticated request.

    Returns:
        tuple: (student, error_response) — exactly one will be None.
    """
    if not hasattr(request.user, 'student_profile'):
        return None, Response(
            {'error': 'Only students can access spaced repetition endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None


class PacingView(APIView):
    """
    2026-02-27: GET /api/v1/spaced-repetition/pacing/

    Returns pacing status including pace_status, weekly_velocity,
    projected_completion_date, and daily_target.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """2026-02-27: Return pacing status for the authenticated student."""
        student, error = _get_student(request)
        if error:
            return error
        pacing = PacingService.get_pacing_status(student)
        return Response(pacing, status=status.HTTP_200_OK)


class ReviewQueueView(APIView):
    """
    2026-02-27: GET /api/v1/spaced-repetition/reviews/today/

    Returns list of concept reviews due today (up to 10).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """2026-02-27: Return today's review queue."""
        student, error = _get_student(request)
        if error:
            return error
        queue = SpacedRepetitionService.get_review_queue(student)
        return Response(
            {'reviews': queue, 'count': len(queue)},
            status=status.HTTP_200_OK,
        )


class ReviewCompleteView(APIView):
    """
    2026-02-27: POST /api/v1/spaced-repetition/reviews/complete/

    Complete a review for one concept.
    Body: { "mastery_id": "uuid", "stars": 4, "explanation_seconds": 45 }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """2026-02-27: Record completion of one concept review."""
        student, error = _get_student(request)
        if error:
            return error

        serializer = ReviewCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        result = SpacedRepetitionService.complete_review(
            student=student,
            mastery_id=serializer.validated_data['mastery_id'],
            stars=serializer.validated_data['stars'],
            explanation_seconds=serializer.validated_data['explanation_seconds'],
        )

        if not result.get('success'):
            code = result.get('code', '')
            http_status = (
                status.HTTP_404_NOT_FOUND
                if code == 'MASTERY_NOT_FOUND'
                else status.HTTP_400_BAD_REQUEST
            )
            return Response({'error': result['error']}, status=http_status)

        return Response(result, status=status.HTTP_200_OK)
