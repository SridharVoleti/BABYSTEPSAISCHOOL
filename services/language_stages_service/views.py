"""
2026-03-02: API views for Language Stages Service (BS-LNG-005).

Endpoints:
  GET  /api/v1/language-stages/scenarios/?language=Hindi
        — List 20 scenarios with unlock status for student
  POST /api/v1/language-stages/session/start/
        — Start a scenario session
  POST /api/v1/language-stages/session/<session_id>/turn/
        — Submit a student turn, receive AI response
  POST /api/v1/language-stages/session/<session_id>/complete/
        — End session and get fluency star rating
  GET  /api/v1/language-stages/progress/?language=Hindi
        — Per-language progress summary
"""

from rest_framework import status  # 2026-03-02: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-03-02: Auth guard
from rest_framework.response import Response  # 2026-03-02: DRF JSON response
from rest_framework.views import APIView  # 2026-03-02: Class-based API view
from rest_framework.exceptions import ValidationError  # 2026-03-02: DRF exceptions

from .services import ConversationService  # 2026-03-02: Business logic


def _get_student(request):
    """
    2026-03-02: Extract student from authenticated request.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    if not hasattr(request.user, 'student_profile'):
        return None, Response(
            {'error': 'Only students can access language stages endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None


class ScenarioListView(APIView):
    """
    2026-03-02: GET /api/v1/language-stages/scenarios/?language=<name>

    Returns all 20 conversation scenarios with unlock status for the student.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: JWT required

    def get(self, request):
        """2026-03-02: Return scenario list with unlock/star info."""
        student, error = _get_student(request)
        if error:
            return error

        language = request.query_params.get('language', '').strip()
        if not language:
            return Response(
                {'error': "'language' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            scenarios = ConversationService.get_scenarios(student, language)
        except ValidationError as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'language': language, 'scenarios': scenarios}, status=status.HTTP_200_OK)


class SessionStartView(APIView):
    """
    2026-03-02: POST /api/v1/language-stages/session/start/

    Body: {"language": "Hindi", "scenario_id": "<uuid>"}
    Creates a ConversationSession and returns the AI's opening turn.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: JWT required

    def post(self, request):
        """2026-03-02: Start a conversation session."""
        student, error = _get_student(request)
        if error:
            return error

        language = request.data.get('language', '').strip()
        scenario_id = request.data.get('scenario_id', '').strip()

        if not language or not scenario_id:
            return Response(
                {'error': "'language' and 'scenario_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = ConversationService.start_session(student, language, scenario_id)
        except ValidationError as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:  # 2026-03-02: NotFound and other errors
            return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_201_CREATED)


class SessionTurnView(APIView):
    """
    2026-03-02: POST /api/v1/language-stages/session/<session_id>/turn/

    Body: {"text": "...", "response_time_seconds": 8}
    Submits a student turn, triggers LLM evaluation + response, returns AI reply.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: JWT required

    def post(self, request, session_id):
        """2026-03-02: Submit student turn and receive AI response."""
        student, error = _get_student(request)
        if error:
            return error

        student_text = request.data.get('text', '').strip()
        if not student_text:
            return Response(
                {'error': "'text' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        response_time = request.data.get('response_time_seconds')

        try:
            result = ConversationService.submit_turn(
                session_id=session_id,
                student=student,
                student_text=student_text,
                response_time_seconds=response_time,
            )
        except ValidationError as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)


class SessionCompleteView(APIView):
    """
    2026-03-02: POST /api/v1/language-stages/session/<session_id>/complete/

    Finalises the session, computes fluency stars, updates progress.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: JWT required

    def post(self, request, session_id):
        """2026-03-02: Complete a conversation session."""
        student, error = _get_student(request)
        if error:
            return error

        try:
            result = ConversationService.complete_session(session_id, student)
        except ValidationError as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'error': str(exc)}, status=status.HTTP_404_NOT_FOUND)

        return Response(result, status=status.HTTP_200_OK)


class ProgressView(APIView):
    """
    2026-03-02: GET /api/v1/language-stages/progress/?language=<name>

    Returns StudentConversationProgress for the authenticated student.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: JWT required

    def get(self, request):
        """2026-03-02: Return progress summary for a language."""
        student, error = _get_student(request)
        if error:
            return error

        language = request.query_params.get('language', '').strip()
        if not language:
            return Response(
                {'error': "'language' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = ConversationService.get_progress(student, language)
        except ValidationError as exc:
            return Response({'error': str(exc.detail)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
