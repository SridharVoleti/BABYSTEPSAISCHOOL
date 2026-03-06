"""
2026-03-06: Mentor Dashboard API views (BS-MNT).

Purpose:
    DRF views for staff-only mentor endpoints: student grid, student detail,
    comprehension review queue, weekly summary, parent message drafting.
"""

from rest_framework import status  # 2026-03-06: HTTP status codes
from rest_framework.permissions import IsAdminUser  # 2026-03-06: staff-only gate
from rest_framework.response import Response  # 2026-03-06: API response
from rest_framework.views import APIView  # 2026-03-06: Class-based views

from .serializers import DraftMessageSerializer, ReviewSubmitSerializer  # 2026-03-06: Input validation
from .services import MentorDashboardService  # 2026-03-06: Business logic


class MentorDashboardView(APIView):
    """
    2026-03-06: Return color-coded student grid for the requesting mentor.

    GET /api/v1/mentor/dashboard/
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def get(self, request):
        """2026-03-06: Return performance grid for all assigned students."""
        grid = MentorDashboardService.get_student_grid(request.user)  # 2026-03-06: Aggregate
        return Response(grid, status=status.HTTP_200_OK)


class MentorStudentDetailView(APIView):
    """
    2026-03-06: Return full lesson/day breakdown for a single assigned student.

    GET /api/v1/mentor/students/<uuid>/
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def get(self, request, student_id):
        """2026-03-06: Return detailed progress for one student."""
        detail = MentorDashboardService.get_student_detail(request.user, student_id)
        if detail is None:  # 2026-03-06: Not assigned or not found
            return Response(
                {'error': 'Student not found or not assigned to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(detail, status=status.HTTP_200_OK)


class ReviewQueueView(APIView):
    """
    2026-03-06: Return comprehension responses awaiting mentor spot-check.

    GET /api/v1/mentor/review-queue/         → un-reviewed queue
    GET /api/v1/mentor/review-queue/?reviewed=true → already-reviewed
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def get(self, request):
        """2026-03-06: Return review queue (filtered by ?reviewed=true/false)."""
        reviewed = request.query_params.get('reviewed', 'false').lower() == 'true'
        queue = MentorDashboardService.get_review_queue(request.user, reviewed=reviewed)
        return Response(queue, status=status.HTTP_200_OK)


class SubmitReviewView(APIView):
    """
    2026-03-06: Submit a mentor review score for one comprehension response.

    POST /api/v1/mentor/review-queue/<uuid>/
    Body: { mentor_score: 0-5, mentor_notes: "..." }
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def post(self, request, response_id):
        """2026-03-06: Create or update ComprehensionReview."""
        serializer = ReviewSubmitSerializer(data=request.data)  # 2026-03-06: Validate input
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        review = MentorDashboardService.submit_review(
            mentor_user=request.user,
            response_id=response_id,
            score=serializer.validated_data['mentor_score'],
            notes=serializer.validated_data.get('mentor_notes', ''),
        )

        if review is None:  # 2026-03-06: Not assigned
            return Response(
                {'error': 'Response not found or student not assigned to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                'id': str(review.id),
                'mentor_score': review.mentor_score,
                'mentor_notes': review.mentor_notes,
                'reviewed_at': review.reviewed_at.isoformat(),
            },
            status=status.HTTP_201_CREATED,
        )


class WeeklySummaryView(APIView):
    """
    2026-03-06: Return the existing weekly summary for a student (current week).

    GET /api/v1/mentor/students/<uuid>/summary/
    Returns 404 if no summary has been generated yet for this week.
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def get(self, request, student_id):
        """2026-03-06: Return current-week summary or 404."""
        from datetime import date, timedelta  # 2026-03-06: Local import
        from .models import WeeklySummary  # 2026-03-06: Local import
        from services.auth_service.models import Student  # 2026-03-06: Local import

        # 2026-03-06: Verify assignment
        student = MentorDashboardService.get_assigned_students(request.user).filter(
            id=student_id
        ).first()
        if not student:
            return Response(
                {'error': 'Student not found or not assigned to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2026-03-06: Find this week's summary
        monday = date.today() - timedelta(days=date.today().weekday())
        summary = WeeklySummary.objects.filter(student=student, week_start=monday).first()

        if not summary:  # 2026-03-06: Not generated yet
            return Response(
                {'error': 'No summary for current week. Use POST /summary/generate/ to create one.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_serialize_summary(summary), status=status.HTTP_200_OK)


class GenerateSummaryView(APIView):
    """
    2026-03-06: Force-generate (or regenerate) the weekly summary via LLM.

    POST /api/v1/mentor/students/<uuid>/summary/generate/
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def post(self, request, student_id):
        """2026-03-06: Generate a fresh weekly summary."""
        summary = MentorDashboardService.generate_fresh_summary(request.user, student_id)

        if summary is None:  # 2026-03-06: Not assigned
            return Response(
                {'error': 'Student not found or not assigned to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(_serialize_summary(summary), status=status.HTTP_201_CREATED)


class MentorMessagesView(APIView):
    """
    2026-03-06: Return all parent message threads for the requesting mentor.

    GET /api/v1/mentor/messages/
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def get(self, request):
        """2026-03-06: Return threads where this mentor is the monitor."""
        threads = MentorDashboardService.get_message_threads(request.user)
        result = [
            {
                'id': str(t.id),
                'student_id': str(t.student_id),
                'student_name': t.student.full_name,
                'subject': t.subject,
                'is_closed': t.is_closed,
                'updated_at': t.updated_at.isoformat(),
            }
            for t in threads
        ]
        return Response(result, status=status.HTTP_200_OK)


class DraftMessageView(APIView):
    """
    2026-03-06: Generate an AI-drafted parent message for a student.

    POST /api/v1/mentor/students/<uuid>/draft-message/
    Body: { context_hint: "..." }   (optional)
    """

    permission_classes = [IsAdminUser]  # 2026-03-06: is_staff required

    def post(self, request, student_id):
        """2026-03-06: Return AI-drafted message text."""
        serializer = DraftMessageSerializer(data=request.data)  # 2026-03-06: Validate
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        draft = MentorDashboardService.draft_parent_message(
            mentor_user=request.user,
            student_id=student_id,
            context_hint=serializer.validated_data.get('context_hint', ''),
        )

        if draft is None:  # 2026-03-06: Not assigned
            return Response(
                {'error': 'Student not found or not assigned to you.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({'draft': draft}, status=status.HTTP_200_OK)


def _serialize_summary(summary):
    """
    2026-03-06: Convert WeeklySummary to response dict.

    Args:
        summary: WeeklySummary instance.

    Returns:
        dict: Serialized summary.
    """
    return {
        'id': str(summary.id),
        'week_start': summary.week_start.isoformat(),
        'summary_text': summary.summary_text,
        'strengths': summary.strengths,
        'areas_for_improvement': summary.areas_for_improvement,
        'lessons_completed': summary.lessons_completed,
        'avg_star_rating': summary.avg_star_rating,
        'generated_at': summary.generated_at.isoformat(),
    }
