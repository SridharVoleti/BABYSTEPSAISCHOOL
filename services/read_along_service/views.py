"""
2026-02-19: Read-Along & Mimic Engine API views (BS-RAM).

Purpose:
    Three endpoints: get content, submit session, get history.
    All require IsAuthenticated + student role.
"""

from rest_framework import status  # 2026-02-19: HTTP status codes
from rest_framework.exceptions import ValidationError, NotFound  # 2026-02-19: DRF exceptions
from rest_framework.permissions import IsAuthenticated  # 2026-02-19: Auth check
from rest_framework.response import Response  # 2026-02-19: API responses
from rest_framework.views import APIView  # 2026-02-19: Class-based views

from .services import ReadAlongService  # 2026-02-19: Business logic


def _get_student(request):
    """
    2026-02-19: Extract student from authenticated request.

    Args:
        request: HTTP request with authenticated user.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-02-19: Must be student
        return None, Response(
            {'error': 'Only students can access read-along endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None  # 2026-02-19: Return student


class ContentView(APIView):
    """
    2026-02-19: Get read-along content for a lesson day.

    GET /api/v1/read-along/lessons/<lesson_id>/day/<day_number>/content/
    Query params: language (required)
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request, lesson_id, day_number):
        """2026-02-19: Return sentences, TTS config, and previous best."""
        student, error = _get_student(request)  # 2026-02-19: Get student
        if error:
            return error

        language = request.query_params.get('language')  # 2026-02-19: Required param
        if not language:
            return Response(
                {'error': "'language' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = ReadAlongService.get_content(  # 2026-02-19: Business logic
                student=student,
                lesson_id=str(lesson_id),
                day_number=day_number,
                language=language,
            )
        except (ValidationError, NotFound) as exc:
            code = (
                status.HTTP_400_BAD_REQUEST
                if isinstance(exc, ValidationError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response(exc.detail, status=code)

        return Response(result, status=status.HTTP_200_OK)


class SubmitSessionView(APIView):
    """
    2026-02-19: Submit a completed read-along session.

    POST /api/v1/read-along/sessions/submit/
    Body: { lesson_id, day_number, language, sentence_scores, time_spent_seconds }
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def post(self, request):
        """2026-02-19: Record session, return score and stars."""
        student, error = _get_student(request)  # 2026-02-19: Get student
        if error:
            return error

        data = request.data  # 2026-02-19: Request body

        # 2026-02-19: Validate required fields
        required = ['lesson_id', 'day_number', 'language', 'sentence_scores']
        missing = [f for f in required if f not in data]
        if missing:
            return Response(
                {'error': f"Missing required fields: {', '.join(missing)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            day_number = int(data['day_number'])  # 2026-02-19: Parse int
        except (ValueError, TypeError):
            return Response(
                {'error': "'day_number' must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        time_spent = int(data.get('time_spent_seconds', 0))  # 2026-02-19: Optional

        try:
            result = ReadAlongService.submit_session(  # 2026-02-19: Business logic
                student=student,
                lesson_id=str(data['lesson_id']),
                day_number=day_number,
                language=data['language'],
                sentence_scores=data['sentence_scores'],
                time_spent_seconds=time_spent,
            )
        except (ValidationError, NotFound) as exc:
            code = (
                status.HTTP_400_BAD_REQUEST
                if isinstance(exc, ValidationError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response(exc.detail, status=code)

        return Response(result, status=status.HTTP_200_OK)


class HistoryView(APIView):
    """
    2026-02-19: Get read-along history for a student/lesson/day/language.

    GET /api/v1/read-along/sessions/history/
    Query params: lesson_id, day_number, language (all required)
    """

    permission_classes = [IsAuthenticated]  # 2026-02-19: Auth required

    def get(self, request):
        """2026-02-19: Return last 5 sessions for the requested combo."""
        student, error = _get_student(request)  # 2026-02-19: Get student
        if error:
            return error

        lesson_id = request.query_params.get('lesson_id')
        day_number_str = request.query_params.get('day_number')
        language = request.query_params.get('language')

        # 2026-02-19: Validate required params
        if not lesson_id or not day_number_str or not language:
            return Response(
                {'error': "'lesson_id', 'day_number', and 'language' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            day_number = int(day_number_str)  # 2026-02-19: Parse int
        except ValueError:
            return Response(
                {'error': "'day_number' must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = ReadAlongService.get_history(  # 2026-02-19: Business logic
                student=student,
                lesson_id=lesson_id,
                day_number=day_number,
                language=language,
            )
        except NotFound as exc:
            return Response(exc.detail, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)
