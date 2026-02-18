"""
2026-02-17: AI Teaching Engine views.

Purpose:
    DRF views for teaching engine endpoints: list/detail lessons,
    start/complete days, get/submit assessments, and tutoring chat.
"""

from rest_framework import status  # 2026-02-17: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-17: Auth required
from rest_framework.response import Response  # 2026-02-17: API responses
from rest_framework.views import APIView  # 2026-02-17: Class-based views

from services.auth_service.models import Student  # 2026-02-17: Student model
from .serializers import (  # 2026-02-17: Serializers
    StartDaySerializer, CompleteDaySerializer,
    SubmitAssessmentSerializer, TutoringChatSerializer,
    StartPracticeSerializer, SubmitPracticeAnswerSerializer,  # 2026-02-18: Mastery practice
)
from .services import TeachingService, MasteryPracticeService  # 2026-02-18: Business logic
from .tutoring import TutoringService  # 2026-02-17: Tutoring logic


def _get_student(request):
    """
    2026-02-17: Extract student from authenticated request.

    Args:
        request: HTTP request with authenticated user.

    Returns:
        tuple: (student, error_response) - one will be None.
    """
    if not hasattr(request.user, 'student_profile'):  # 2026-02-17: Must be student
        return None, Response(
            {'error': 'Only students can access teaching lessons.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    return request.user.student_profile, None  # 2026-02-17: Return student


class LessonListView(APIView):
    """
    2026-02-17: List published lessons for student's grade.

    GET /api/v1/teaching/lessons/
    Query params: subject (optional)
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def get(self, request):
        """2026-02-17: List lessons for student's class."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        subject = request.query_params.get('subject')  # 2026-02-17: Optional filter
        result = TeachingService.list_lessons(  # 2026-02-17: Business logic
            class_number=student.grade,
            subject=subject,
        )
        return Response(result, status=status.HTTP_200_OK)


class LessonDetailView(APIView):
    """
    2026-02-17: Get lesson detail with student's progress.

    GET /api/v1/teaching/lessons/{lesson_id}/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def get(self, request, lesson_id):
        """2026-02-17: Get lesson detail."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        result = TeachingService.get_lesson_detail(student, lesson_id)  # 2026-02-17: Business logic

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class StartDayView(APIView):
    """
    2026-02-17: Start a day's micro-lesson with IQ-adapted content.

    POST /api/v1/teaching/lessons/{lesson_id}/start-day/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def post(self, request, lesson_id):
        """2026-02-17: Start a micro-lesson day."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        serializer = StartDaySerializer(data=request.data)  # 2026-02-17: Validate
        serializer.is_valid(raise_exception=True)

        result = TeachingService.start_day(  # 2026-02-17: Business logic
            student=student,
            lesson_id=lesson_id,
            day_number=serializer.validated_data.get('day_number'),
        )

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class CompleteDayView(APIView):
    """
    2026-02-17: Complete a day's micro-lesson with practice answers.

    POST /api/v1/teaching/lessons/{lesson_id}/complete-day/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def post(self, request, lesson_id):
        """2026-02-17: Complete a micro-lesson day."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        serializer = CompleteDaySerializer(data=request.data)  # 2026-02-17: Validate
        serializer.is_valid(raise_exception=True)

        result = TeachingService.complete_day(  # 2026-02-17: Business logic
            student=student,
            lesson_id=lesson_id,
            day_number=serializer.validated_data['day_number'],
            practice_answers=serializer.validated_data['practice_answers'],
            time_spent=serializer.validated_data['time_spent'],
        )

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class AssessmentView(APIView):
    """
    2026-02-17: Get Day 5 weekly assessment questions.

    GET /api/v1/teaching/lessons/{lesson_id}/assessment/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def get(self, request, lesson_id):
        """2026-02-17: Get assessment questions."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        result = TeachingService.get_assessment(student, lesson_id)  # 2026-02-17: Business logic

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class SubmitAssessmentView(APIView):
    """
    2026-02-17: Submit Day 5 weekly assessment.

    POST /api/v1/teaching/lessons/{lesson_id}/submit-assessment/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def post(self, request, lesson_id):
        """2026-02-17: Submit assessment answers."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        serializer = SubmitAssessmentSerializer(data=request.data)  # 2026-02-17: Validate
        serializer.is_valid(raise_exception=True)

        result = TeachingService.submit_assessment(  # 2026-02-17: Business logic
            student=student,
            lesson_id=lesson_id,
            answers=serializer.validated_data['answers'],
            time_spent=serializer.validated_data['time_spent'],
        )

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class StartPracticeView(APIView):
    """
    2026-02-18: Start a mastery practice session for a day.

    POST /api/v1/teaching/lessons/{lesson_id}/practice/start/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-18: Auth required

    def post(self, request, lesson_id):
        """2026-02-18: Start mastery practice."""
        student, error = _get_student(request)  # 2026-02-18: Get student
        if error:
            return error

        serializer = StartPracticeSerializer(data=request.data)  # 2026-02-18: Validate
        serializer.is_valid(raise_exception=True)

        result = MasteryPracticeService.start_practice(  # 2026-02-18: Business logic
            student=student,
            lesson_id=lesson_id,
            day_number=serializer.validated_data['day_number'],
        )

        if result['success']:  # 2026-02-18: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class SubmitPracticeAnswerView(APIView):
    """
    2026-02-18: Submit an answer for a mastery practice question.

    POST /api/v1/teaching/practice/{session_id}/answer/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-18: Auth required

    def post(self, request, session_id):
        """2026-02-18: Submit practice answer."""
        student, error = _get_student(request)  # 2026-02-18: Get student
        if error:
            return error

        serializer = SubmitPracticeAnswerSerializer(data=request.data)  # 2026-02-18: Validate
        serializer.is_valid(raise_exception=True)

        result = MasteryPracticeService.submit_answer(  # 2026-02-18: Business logic
            student=student,
            session_id=session_id,
            question_id=serializer.validated_data['question_id'],
            answer=serializer.validated_data['answer'],
            time_taken=serializer.validated_data.get('time_taken', 0),
            hints_used=serializer.validated_data.get('hints_used', 0),
        )

        if result['success']:  # 2026-02-18: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


class PracticeStatusView(APIView):
    """
    2026-02-18: Get mastery practice status for all 4 days.

    GET /api/v1/teaching/lessons/{lesson_id}/practice/status/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-18: Auth required

    def get(self, request, lesson_id):
        """2026-02-18: Get practice status."""
        student, error = _get_student(request)  # 2026-02-18: Get student
        if error:
            return error

        result = MasteryPracticeService.get_practice_status(  # 2026-02-18: Business logic
            student=student,
            lesson_id=lesson_id,
        )

        if result['success']:  # 2026-02-18: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_404_NOT_FOUND)


class TutoringChatView(APIView):
    """
    2026-02-17: AI tutoring chat endpoint.

    POST /api/v1/teaching/chat/
    """

    permission_classes = [IsAuthenticated]  # 2026-02-17: Auth required

    def post(self, request):
        """2026-02-17: Send a tutoring chat message."""
        student, error = _get_student(request)  # 2026-02-17: Get student
        if error:
            return error

        serializer = TutoringChatSerializer(data=request.data)  # 2026-02-17: Validate
        serializer.is_valid(raise_exception=True)

        result = TutoringService.chat(  # 2026-02-17: Business logic
            student=student,
            message=serializer.validated_data['message'],
            lesson_id=serializer.validated_data.get('lesson_id'),
            day_number=serializer.validated_data.get('day_number'),
        )

        if result['success']:  # 2026-02-17: Success
            return Response(result, status=status.HTTP_200_OK)
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
