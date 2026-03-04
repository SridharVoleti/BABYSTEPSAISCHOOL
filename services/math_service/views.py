"""
2026-03-02: Math Service DRF views (BS-MTH module).

Purpose:
    DRF APIView endpoints for listing lessons, starting sessions,
    submitting answers, requesting hints, checking session status,
    and viewing progress. All views require authentication.
"""

from rest_framework import status  # 2026-03-02: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-03-02: Auth guard
from rest_framework.response import Response  # 2026-03-02: DRF response
from rest_framework.views import APIView  # 2026-03-02: Class-based views

from services.auth_service.models import Student  # 2026-03-02: Student model
from .serializers import (  # 2026-03-02: Request validators
    StartSessionSerializer, SubmitAnswerSerializer, RequestHintSerializer,
    TeachingChatSerializer,
    StartDrillSerializer, SubmitDrillAnswerSerializer,  # 2026-03-03: Drill serializers
)
from .services import MathService  # 2026-03-02: Business logic
from .tutoring import MathTutoringService  # 2026-03-02: BS-AMT-001 teaching service
from .models import MathSession  # 2026-03-02: Session model for teaching views
from .drill_service import MathDrillService  # 2026-03-03: Drill service (AMT-APE-005)


def _get_student(request):
    """
    2026-03-02: Extract student from an authenticated request.

    Args:
        request: Authenticated HTTP request.

    Returns:
        tuple: (student, error_response) — one will always be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-03-02: Must be student
        return None, Response(
            {'error': 'Only students can access math lessons.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None  # 2026-03-02: Return student


class LessonListView(APIView):
    """
    2026-03-02: List published math lessons for the student's grade.

    GET /api/v1/math/lessons/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def get(self, request):
        """2026-03-02: List lessons for student's class."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        result = MathService.list_lessons(class_number=student.grade)  # 2026-03-02: Business logic
        return Response(result, status=status.HTTP_200_OK)


class LessonDetailView(APIView):
    """
    2026-03-02: Get lesson metadata and day titles.

    GET /api/v1/math/lessons/{lesson_id}/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def get(self, request, lesson_id):
        """2026-03-02: Get lesson detail."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        result = MathService.get_lesson_detail(lesson_id=lesson_id)  # 2026-03-02: Business logic
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class StartSessionView(APIView):
    """
    2026-03-02: Start a math practice session.

    POST /api/v1/math/sessions/
    Body: {lesson_id, day_number}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def post(self, request):
        """2026-03-02: Create a new math session."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        serializer = StartSessionSerializer(data=request.data)  # 2026-03-02: Validate
        serializer.is_valid(raise_exception=True)

        result = MathService.start_session(  # 2026-03-02: Business logic
            student=student,
            lesson_id=serializer.validated_data['lesson_id'],
            day_number=serializer.validated_data['day_number'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class SessionStatusView(APIView):
    """
    2026-03-02: Get current session status.

    GET /api/v1/math/sessions/{session_id}/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def get(self, request, session_id):
        """2026-03-02: Get session status."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        result = MathService.get_session_status(session_id=str(session_id))  # 2026-03-02: Logic
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class SubmitAnswerView(APIView):
    """
    2026-03-02: Submit an answer for a problem in an active session.

    POST /api/v1/math/sessions/{session_id}/answer/
    Body: {problem_id, answer, time_taken}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def post(self, request, session_id):
        """2026-03-02: Submit an answer."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        serializer = SubmitAnswerSerializer(data=request.data)  # 2026-03-02: Validate
        serializer.is_valid(raise_exception=True)

        result = MathService.submit_answer(  # 2026-03-02: Business logic
            session_id=str(session_id),
            problem_id=serializer.validated_data['problem_id'],
            student_answer=serializer.validated_data['answer'],
            time_taken=serializer.validated_data.get('time_taken'),
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class RequestHintView(APIView):
    """
    2026-03-02: Request a hint for a problem in an active session.

    POST /api/v1/math/sessions/{session_id}/hint/
    Body: {problem_id}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def post(self, request, session_id):
        """2026-03-02: Request a hint."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        serializer = RequestHintSerializer(data=request.data)  # 2026-03-02: Validate
        serializer.is_valid(raise_exception=True)

        result = MathService.request_hint(  # 2026-03-02: Business logic
            session_id=str(session_id),
            problem_id=serializer.validated_data['problem_id'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class MathProgressView(APIView):
    """
    2026-03-02: Get student's aggregated math progress.

    GET /api/v1/math/progress/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def get(self, request):
        """2026-03-02: Get progress summary."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        result = MathService.get_progress(student=student)  # 2026-03-02: Business logic
        return Response(result, status=status.HTTP_200_OK)


# ── BS-AMT-001: AI Math Tutor teaching phase views ────────────────────────────

def _get_math_session(session_id, student):
    """
    2026-03-02: Retrieve a MathSession that belongs to the given student.

    Args:
        session_id: UUID of the MathSession.
        student: Authenticated student instance.

    Returns:
        tuple: (math_session, error_response) — one will always be None.
    """
    try:
        session = MathSession.objects.get(id=session_id, student=student)  # 2026-03-02: Lookup
        return session, None  # 2026-03-02: Found
    except MathSession.DoesNotExist:  # 2026-03-02: Not found or wrong student
        return None, Response(
            {'error': 'Math session not found.'},
            status=status.HTTP_404_NOT_FOUND,
        )


class TeachingSessionView(APIView):
    """
    2026-03-02: Get or create the AI tutor teaching session for a math session (BS-AMT-001).

    GET /api/v1/math/sessions/{session_id}/teach/

    Creates the tutoring session on first call (AI generates opening message).
    Returns existing session on subsequent calls. Safe to call multiple times.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def get(self, request, session_id):
        """2026-03-02: Get or create teaching session."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        math_session, err = _get_math_session(session_id, student)  # 2026-03-02: Get session
        if err:
            return err

        result = MathTutoringService.get_or_create_session(math_session)  # 2026-03-02: Logic
        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class TeachingChatView(APIView):
    """
    2026-03-02: Send a student message during the teaching phase (BS-AMT-001).

    POST /api/v1/math/sessions/{session_id}/teach/chat/
    Body: {message: str}

    AI tutor responds using Socratic method anchored to the lesson content.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def post(self, request, session_id):
        """2026-03-02: Handle student teaching chat message."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        math_session, err = _get_math_session(session_id, student)  # 2026-03-02: Get session
        if err:
            return err

        serializer = TeachingChatSerializer(data=request.data)  # 2026-03-02: Validate
        serializer.is_valid(raise_exception=True)

        result = MathTutoringService.chat(  # 2026-03-02: Business logic
            math_session=math_session,
            student_message=serializer.validated_data['message'],
        )

        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class TeachingCompleteView(APIView):
    """
    2026-03-02: Mark the teaching phase complete — student is ready to practice (BS-AMT-001).

    POST /api/v1/math/sessions/{session_id}/teach/complete/
    Body: {} (empty)

    Sets teaching_complete=True. Frontend transitions to practice phase.
    """

    permission_classes = [IsAuthenticated]  # 2026-03-02: Require auth

    def post(self, request, session_id):
        """2026-03-02: Complete teaching phase."""
        student, error = _get_student(request)  # 2026-03-02: Get student
        if error:
            return error

        math_session, err = _get_math_session(session_id, student)  # 2026-03-02: Get session
        if err:
            return err

        result = MathTutoringService.complete_teaching(math_session)  # 2026-03-02: Logic
        if result.get('success'):
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


# ── AMT-APE-005: Mental Maths Drill views ────────────────────────────────────

class StartDrillView(APIView):
    """
    2026-03-03: Start a new mental maths drill session (AMT-APE-005).

    POST /api/v1/math/drills/
    Body: {drill_type, number_range_min, number_range_max, time_limit_seconds, total_questions}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-03: Require auth

    def post(self, request):
        """2026-03-03: Create a new drill session."""
        student, error = _get_student(request)  # 2026-03-03: Get student
        if error:
            return error

        serializer = StartDrillSerializer(data=request.data)  # 2026-03-03: Validate
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = MathDrillService.start_drill(  # 2026-03-03: Business logic
            student=student,
            drill_type=data['drill_type'],
            min_n=data['number_range_min'],
            max_n=data['number_range_max'],
            time_limit=int(data['time_limit_seconds']),
            total_questions=data['total_questions'],
        )

        if result['success']:
            return Response(result, status=status.HTTP_201_CREATED)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class DrillStatusView(APIView):
    """
    2026-03-03: Get the current state of a drill session (AMT-APE-005).

    GET /api/v1/math/drills/{session_id}/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-03: Require auth

    def get(self, request, session_id):
        """2026-03-03: Get drill session status."""
        student, error = _get_student(request)  # 2026-03-03: Get student
        if error:
            return error

        result = MathDrillService.get_drill_status(session_id=str(session_id))  # 2026-03-03: Logic
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class SubmitDrillAnswerView(APIView):
    """
    2026-03-03: Submit a student answer for a drill question (AMT-APE-005).

    POST /api/v1/math/drills/{session_id}/answer/
    Body: {question_index, answer, response_time_ms}
    """

    permission_classes = [IsAuthenticated]  # 2026-03-03: Require auth

    def post(self, request, session_id):
        """2026-03-03: Submit drill answer."""
        student, error = _get_student(request)  # 2026-03-03: Get student
        if error:
            return error

        serializer = SubmitDrillAnswerSerializer(data=request.data)  # 2026-03-03: Validate
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = MathDrillService.submit_answer(  # 2026-03-03: Business logic
            session_id=str(session_id),
            question_index=data['question_index'],
            answer=data['answer'],
            response_time_ms=data.get('response_time_ms'),
        )

        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class CompleteDrillView(APIView):
    """
    2026-03-03: Force-complete a drill session on timer expiry (AMT-APE-005).

    POST /api/v1/math/drills/{session_id}/complete/
    Body: {} (empty)
    """

    permission_classes = [IsAuthenticated]  # 2026-03-03: Require auth

    def post(self, request, session_id):
        """2026-03-03: Force-complete drill (timer expiry)."""
        student, error = _get_student(request)  # 2026-03-03: Get student
        if error:
            return error

        result = MathDrillService.complete_drill(session_id=str(session_id))  # 2026-03-03: Logic
        if result['success']:
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class DrillHistoryView(APIView):
    """
    2026-03-03: Get student's drill history — last 20 completed/expired sessions (AMT-APE-005).

    GET /api/v1/math/drills/history/
    """

    permission_classes = [IsAuthenticated]  # 2026-03-03: Require auth

    def get(self, request):
        """2026-03-03: Get drill history."""
        student, error = _get_student(request)  # 2026-03-03: Get student
        if error:
            return error

        result = MathDrillService.get_drill_history(student=student)  # 2026-03-03: Logic
        return Response(result, status=status.HTTP_200_OK)
