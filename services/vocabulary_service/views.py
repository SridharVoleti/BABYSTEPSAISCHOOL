"""
2026-02-20: Vocabulary Acquisition System API views (BS-LNG).

Purpose:
    Five endpoints for student vocabulary sessions:
    - TodaySessionView: GET session for today (or create it).
    - RecordPronunciationView: POST pronunciation score for a word.
    - RecordMCQView: POST MCQ answer for a word.
    - CompleteSessionView: POST to finalize session and compute stars.
    - ProgressView: GET overall vocabulary progress for a language.
    All require IsAuthenticated + student role.
"""

from rest_framework import status  # 2026-02-20: HTTP status codes
from rest_framework.exceptions import ValidationError, NotFound  # 2026-02-20: DRF exceptions
from rest_framework.permissions import IsAuthenticated  # 2026-02-20: Auth check
from rest_framework.response import Response  # 2026-02-20: API responses
from rest_framework.views import APIView  # 2026-02-20: Class-based views

from .services import VocabularyService  # 2026-02-20: Business logic


def _get_student(request):
    """
    2026-02-20: Extract student from authenticated request.

    Args:
        request: HTTP request with authenticated user.

    Returns:
        tuple: (student, error_response) — one will be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-02-20: Must be student
        return None, Response(
            {'error': 'Only students can access vocabulary endpoints.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None  # 2026-02-20: Return student


class TodaySessionView(APIView):
    """
    2026-02-20: Get (or create) today's vocabulary session.

    GET /api/v1/vocabulary/session/?language=Hindi
    Returns the 10-word session for today. Idempotent.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return today's session data with 10 words."""
        student, error = _get_student(request)  # 2026-02-20: Get student
        if error:
            return error

        language = request.query_params.get('language')  # 2026-02-20: Required param
        if not language:
            return Response(
                {'error': "'language' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = VocabularyService.get_today_session(  # 2026-02-20: Business logic
                student=student,
                language_name=language,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)


class RecordPronunciationView(APIView):
    """
    2026-02-20: Record pronunciation score for a word in a session.

    POST /api/v1/vocabulary/session/<session_id>/word/<word_id>/pronunciation/
    Body: { "score": 0.85 }
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request, session_id, word_id):
        """2026-02-20: Save pronunciation score and update progress."""
        student, error = _get_student(request)  # 2026-02-20: Get student
        if error:
            return error

        score = request.data.get('score')  # 2026-02-20: Required field
        if score is None:
            return Response(
                {'error': "'score' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            score_float = float(score)  # 2026-02-20: Convert to float
        except (ValueError, TypeError):
            return Response(
                {'error': "'score' must be a number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from rest_framework.exceptions import PermissionDenied  # 2026-02-20: Local import
            result = VocabularyService.record_pronunciation(  # 2026-02-20: Business logic
                session_id=str(session_id),
                word_id=str(word_id),
                score=score_float,
                student=student,
            )
        except (ValidationError, NotFound) as exc:
            code = (
                status.HTTP_400_BAD_REQUEST
                if isinstance(exc, ValidationError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response(exc.detail, status=code)
        except Exception as exc:  # 2026-02-20: PermissionDenied
            if 'PermissionDenied' in type(exc).__name__ or hasattr(exc, 'status_code') and exc.status_code == 403:
                return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
            raise

        return Response(result, status=status.HTTP_200_OK)


class RecordMCQView(APIView):
    """
    2026-02-20: Record MCQ answer for a word in a session.

    POST /api/v1/vocabulary/session/<session_id>/word/<word_id>/mcq/
    Body: { "correct": true }
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request, session_id, word_id):
        """2026-02-20: Save MCQ result and update progress."""
        student, error = _get_student(request)  # 2026-02-20: Get student
        if error:
            return error

        correct = request.data.get('correct')  # 2026-02-20: Required field
        if correct is None:
            return Response(
                {'error': "'correct' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = VocabularyService.record_mcq(  # 2026-02-20: Business logic
                session_id=str(session_id),
                word_id=str(word_id),
                correct=bool(correct),
                student=student,
            )
        except (ValidationError, NotFound) as exc:
            code = (
                status.HTTP_400_BAD_REQUEST
                if isinstance(exc, ValidationError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response(exc.detail, status=code)
        except Exception as exc:  # 2026-02-20: PermissionDenied
            if 'PermissionDenied' in type(exc).__name__ or hasattr(exc, 'status_code') and exc.status_code == 403:
                return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
            raise

        return Response(result, status=status.HTTP_200_OK)


class CompleteSessionView(APIView):
    """
    2026-02-20: Complete a vocabulary session and compute stars.

    POST /api/v1/vocabulary/session/<session_id>/complete/
    Returns fluency_star_rating and mastery stats.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def post(self, request, session_id):
        """2026-02-20: Finalize session, compute stars, update mastery."""
        student, error = _get_student(request)  # 2026-02-20: Get student
        if error:
            return error

        try:
            result = VocabularyService.complete_session(  # 2026-02-20: Business logic
                session_id=str(session_id),
                student=student,
            )
        except (ValidationError, NotFound) as exc:
            code = (
                status.HTTP_400_BAD_REQUEST
                if isinstance(exc, ValidationError)
                else status.HTTP_404_NOT_FOUND
            )
            return Response(exc.detail, status=code)
        except Exception as exc:  # 2026-02-20: PermissionDenied
            if 'PermissionDenied' in type(exc).__name__ or hasattr(exc, 'status_code') and exc.status_code == 403:
                return Response({'error': str(exc)}, status=status.HTTP_403_FORBIDDEN)
            raise

        return Response(result, status=status.HTTP_200_OK)


class ProgressView(APIView):
    """
    2026-02-20: Get vocabulary progress for a student in a language.

    GET /api/v1/vocabulary/progress/?language=Hindi
    Returns mastery counts and current streak.
    """

    permission_classes = [IsAuthenticated]  # 2026-02-20: Auth required

    def get(self, request):
        """2026-02-20: Return progress stats for requested language."""
        student, error = _get_student(request)  # 2026-02-20: Get student
        if error:
            return error

        language = request.query_params.get('language')  # 2026-02-20: Required param
        if not language:
            return Response(
                {'error': "'language' query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = VocabularyService.get_progress(  # 2026-02-20: Business logic
                student=student,
                language_name=language,
            )
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

        return Response(result, status=status.HTTP_200_OK)
