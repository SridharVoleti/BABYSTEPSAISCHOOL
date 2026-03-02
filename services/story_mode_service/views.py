"""
2026-02-27: API views for Story Mode Service (BS-GAM-003).

Endpoints:
  GET /api/v1/story/progress/         — student's story progress
  GET /api/v1/story/scene/<scene_id>/ — scene detail
"""
from rest_framework import status  # 2026-02-27: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-27: Auth guard
from rest_framework.response import Response  # 2026-02-27: DRF JSON response
from rest_framework.views import APIView  # 2026-02-27: Class-based API view

from .services import StoryModeService  # 2026-02-27: Business logic layer


def _get_student(request):
    """
    2026-02-27: Extract student from authenticated request.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    if not hasattr(request.user, 'student_profile'):
        return None, Response(
            {'error': 'Only students can access story mode endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None


class StoryProgressView(APIView):
    """
    2026-02-27: GET /api/v1/story/progress/

    Returns the student's story progress: quest count, current land,
    and last 3 unlocked scenes.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-27: JWT authentication required

    def get(self, request):
        """2026-02-27: Return story progress for authenticated student."""
        student, error = _get_student(request)
        if error:
            return error
        progress = StoryModeService.get_progress(student)
        return Response(progress, status=status.HTTP_200_OK)


class StorySceneView(APIView):
    """
    2026-02-27: GET /api/v1/story/scene/<scene_id>/

    Returns detail for a specific narrative scene.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-27: JWT authentication required

    def get(self, request, scene_id):
        """2026-02-27: Return scene detail by scene_id slug."""
        student, error = _get_student(request)
        if error:
            return error
        scene = StoryModeService.get_scene(scene_id)
        if not scene:
            return Response(
                {'error': f"Scene '{scene_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(scene, status=status.HTTP_200_OK)
