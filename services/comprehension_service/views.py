"""
2026-02-19: Comprehension Capture Engine API views (BS-CMP).

Purpose:
    Two endpoints:
    - POST  .../explain/ — submit and evaluate a comprehension explanation
    - GET   .../best/   — retrieve the best evaluation for a student+lesson+day
"""

import logging  # 2026-02-19: Logging

from rest_framework.views import APIView  # 2026-02-19: DRF APIView
from rest_framework.response import Response  # 2026-02-19: DRF Response
from rest_framework import status  # 2026-02-19: HTTP status codes
from rest_framework.permissions import IsAuthenticated  # 2026-02-19: Auth guard

from services.auth_service.models import Student  # 2026-02-19: Student model
from services.auth_service.permissions import IsStudent  # 2026-02-19: Role permission
from .services import ComprehensionService  # 2026-02-19: Business logic

logger = logging.getLogger(__name__)  # 2026-02-19: Module logger


class SubmitExplanationView(APIView):
    """
    2026-02-19: POST endpoint to submit a comprehension explanation.

    Students only. Validates input, checks for existing lesson, delegates
    to ComprehensionService.submit_explanation().

    URL: POST /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/explain/

    Request body:
        {
            "student_text": "Owls can see in the dark...",
            "practice_stars": 4
        }

    Response (non-parroting, 200):
        {
            "is_parroting": false,
            "comprehension_score": 78.0,
            "weighted_star_rating": 4,
            ...
        }

    Response (parroting, 200):
        {
            "is_parroting": true,
            "message": "Try explaining in your own words!"
        }
    """

    permission_classes = [IsAuthenticated, IsStudent]  # 2026-02-19: Students only

    def post(self, request, lesson_id, day_number):
        """
        2026-02-19: Handle comprehension explanation submission.

        Args:
            request: DRF request with student_text and practice_stars in body.
            lesson_id: TeachingLesson UUID from URL.
            day_number: Day number (1-4) from URL.

        Returns:
            Response: Evaluation result or error.
        """
        # 2026-02-19: Validate day_number range
        if day_number < 1 or day_number > 4:
            return Response(
                {'error': 'day_number must be 1-4.', 'code': 'INVALID_DAY'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2026-02-19: Get student from authenticated user
        try:
            student = Student.objects.get(user=request.user)  # 2026-02-19: Lookup
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found.', 'code': 'STUDENT_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-02-19: Extract and validate request body
        student_text = request.data.get('student_text', '').strip()  # 2026-02-19: Explanation
        if not student_text:  # 2026-02-19: Required field
            return Response(
                {'error': 'student_text is required.', 'code': 'MISSING_STUDENT_TEXT'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        practice_stars_raw = request.data.get('practice_stars')  # 2026-02-19: Stars
        if practice_stars_raw is None:  # 2026-02-19: Required field
            return Response(
                {'error': 'practice_stars is required.', 'code': 'MISSING_PRACTICE_STARS'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            practice_stars = int(practice_stars_raw)  # 2026-02-19: Convert to int
        except (TypeError, ValueError):
            return Response(
                {'error': 'practice_stars must be an integer.', 'code': 'INVALID_PRACTICE_STARS'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2026-02-19: Delegate to service
        result = ComprehensionService.submit_explanation(
            student=student,
            lesson_id=str(lesson_id),
            day_number=day_number,
            student_text=student_text,
            practice_stars=practice_stars,
        )

        # 2026-02-19: Handle lesson-not-found error from service
        if isinstance(result, dict) and result.get('code') == 'LESSON_NOT_FOUND':
            return Response(
                {'error': result['error'], 'code': result['code']},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(result, status=status.HTTP_200_OK)  # 2026-02-19: Return result


class BestEvaluationView(APIView):
    """
    2026-02-19: GET endpoint to retrieve a student's best evaluation.

    URL: GET /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/best/

    Response (200, with data):
        { "evaluation_id": "...", "weighted_star_rating": 4, ... }

    Response (200, no data yet):
        {}
    """

    permission_classes = [IsAuthenticated, IsStudent]  # 2026-02-19: Students only

    def get(self, request, lesson_id, day_number):
        """
        2026-02-19: Retrieve best comprehension evaluation.

        Args:
            request: Authenticated DRF request.
            lesson_id: TeachingLesson UUID from URL.
            day_number: Day number (1-4) from URL.

        Returns:
            Response: Best evaluation dict or empty dict.
        """
        # 2026-02-19: Get student from authenticated user
        try:
            student = Student.objects.get(user=request.user)  # 2026-02-19: Lookup
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found.', 'code': 'STUDENT_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        result = ComprehensionService.get_best_evaluation(  # 2026-02-19: Delegate
            student=student,
            lesson_id=str(lesson_id),
            day_number=day_number,
        )

        return Response(result or {}, status=status.HTTP_200_OK)  # 2026-02-19: Return


class DayQuestionsView(APIView):
    """
    2026-02-21: GET endpoint to list comprehension questions for a lesson day (BS-CMP).

    Returns only the public fields (id, marks, question) — key_points are
    withheld until after submission to prevent gaming.

    URL: GET /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/questions/

    Response (200):
        [{"id": "D1_CQ1", "marks": 2, "question": "Explain what science is."}]

    Returns an empty list when the lesson has no comprehension questions.
    """

    permission_classes = [IsAuthenticated, IsStudent]  # 2026-02-21: Students only

    def get(self, request, lesson_id, day_number):
        """
        2026-02-21: Return the list of comprehension questions for a lesson day.

        Args:
            request: Authenticated DRF request.
            lesson_id: TeachingLesson UUID from URL.
            day_number: Day number (1-4) from URL.

        Returns:
            Response: List of question dicts (id, marks, question only).
        """
        questions = ComprehensionService.get_day_questions(  # 2026-02-21: Load questions
            lesson_id=str(lesson_id),
            day_number=day_number,
        )

        # 2026-02-21: Strip key_points and model_answer from public response
        public_questions = [
            {
                'id': q.get('id'),
                'marks': q.get('marks'),
                'question': q.get('question'),
            }
            for q in questions
        ]

        return Response(public_questions, status=status.HTTP_200_OK)  # 2026-02-21: Return


class SubmitQuestionAnswerView(APIView):
    """
    2026-02-21: POST endpoint to submit a student answer to a comprehension question (BS-CMP).

    Students only. The server loads key_points from content JSON (not from the client)
    to prevent gaming. LLM evaluates coverage; result is returned immediately.

    URL: POST /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/questions/<question_id>/answer/

    Request body:
        {"student_text": "...", "input_method": "typed"}

    Response (200):
        {"marks_awarded": 1, "marks_available": 2,
         "key_points_covered": [true, false],
         "key_points_text": ["Point 1", "Point 2"],
         "feedback": "Great start!",
         "llm_error": false, "attempt_number": 1, "is_new_best": true}
    """

    permission_classes = [IsAuthenticated, IsStudent]  # 2026-02-21: Students only

    def post(self, request, lesson_id, day_number, question_id):
        """
        2026-02-21: Handle comprehension question answer submission.

        Args:
            request: DRF request with student_text and input_method in body.
            lesson_id: TeachingLesson UUID from URL.
            day_number: Day number (1-4) from URL.
            question_id: Question ID string from URL (e.g. "D1_CQ1").

        Returns:
            Response: Evaluation result or error.
        """
        # 2026-02-21: Validate day_number range
        if day_number < 1 or day_number > 4:
            return Response(
                {'error': 'day_number must be 1-4.', 'code': 'INVALID_DAY'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2026-02-21: Get student from authenticated user
        try:
            student = Student.objects.get(user=request.user)  # 2026-02-21: Lookup
        except Student.DoesNotExist:
            return Response(
                {'error': 'Student profile not found.', 'code': 'STUDENT_NOT_FOUND'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-02-21: Extract and validate request body
        student_text = request.data.get('student_text', '').strip()  # 2026-02-21: Answer text
        if not student_text:  # 2026-02-21: Required
            return Response(
                {'error': 'student_text is required.', 'code': 'MISSING_STUDENT_TEXT'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        input_method = request.data.get('input_method', '').strip()  # 2026-02-21: typed/spoken
        if input_method not in ('typed', 'spoken'):  # 2026-02-21: Validate
            return Response(
                {
                    'error': 'input_method must be "typed" or "spoken".',
                    'code': 'INVALID_INPUT_METHOD',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2026-02-21: Delegate to service
        result = ComprehensionService.submit_question_answer(
            student=student,
            lesson_id=str(lesson_id),
            day_number=day_number,
            question_id=question_id,
            student_text=student_text,
            input_method=input_method,
        )

        # 2026-02-21: Handle error codes from service
        error_code = result.get('code') if isinstance(result, dict) else None
        if error_code == 'LESSON_NOT_FOUND':
            return Response(
                {'error': result['error'], 'code': error_code},
                status=status.HTTP_404_NOT_FOUND,
            )
        if error_code in ('DAY_NOT_FOUND', 'QUESTION_NOT_FOUND'):
            return Response(
                {'error': result['error'], 'code': error_code},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(result, status=status.HTTP_200_OK)  # 2026-02-21: Return result
