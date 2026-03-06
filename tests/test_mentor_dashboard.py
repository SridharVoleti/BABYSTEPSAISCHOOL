"""
2026-03-06: Tests for Mentor Dashboard Service (BS-MNT).

30 tests:
  - 15 service unit tests (MentorDashboardService logic)
  - 15 API integration tests (HTTP endpoints, auth, access control)
"""

import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.auth_service.models import Parent, Student
from services.communication_service.models import MessageThread
from services.comprehension_service.models import ComprehensionQuestionResponse
from services.mentor_dashboard_service.models import (
    ComprehensionReview,
    MentorAssignment,
    WeeklySummary,
)
from services.mentor_dashboard_service.services import (
    MentorDashboardService,
    _compute_color,
)
from services.teaching_engine.models import (
    DayProgress,
    StudentLessonProgress,
    TeachingLesson,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mentor(db):
    """2026-03-06: Staff user acting as mentor."""
    return User.objects.create_user(
        username='test_mentor', password='pass', is_staff=True
    )


@pytest.fixture
def mentor_client(mentor):
    """2026-03-06: JWT-authenticated API client for mentor."""
    client = APIClient()
    token = RefreshToken.for_user(mentor)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_obj(db):
    """2026-03-06: Parent model instance."""
    user = User.objects.create_user(username='mnt_parent', password='pass')
    return Parent.objects.create(
        user=user, phone='+919911223344', full_name='MNT Parent',
        is_phone_verified=True, is_profile_complete=True,
    )


@pytest.fixture
def student(db, parent_obj):
    """2026-03-06: Student assigned to the mentor."""
    user = User.objects.create_user(username='mnt_student', password='pass')
    return Student.objects.create(
        user=user, parent=parent_obj, full_name='Mnt Student',
        dob=date(2014, 6, 1), grade=5,
    )


@pytest.fixture
def other_student(db, parent_obj):
    """2026-03-06: Student NOT assigned to the mentor."""
    user = User.objects.create_user(username='mnt_other_student', password='pass')
    return Student.objects.create(
        user=user, parent=parent_obj, full_name='Other Student',
        dob=date(2014, 6, 1), grade=5,
    )


@pytest.fixture
def assignment(db, mentor, student):
    """2026-03-06: Active mentor–student assignment."""
    return MentorAssignment.objects.create(mentor=mentor, student=student, is_active=True)


@pytest.fixture
def lesson(db):
    """2026-03-06: A published TeachingLesson."""
    return TeachingLesson.objects.create(
        lesson_id='MNT_TEST_W01',
        title='MNT Test Lesson',
        subject='Science',
        class_number=5,
        week_number=1,
        content_json_path='json/teaching/class5/Science/week1.json',
        status='published',
    )


@pytest.fixture
def lesson_progress(db, student, lesson):
    """2026-03-06: StudentLessonProgress for the student."""
    return StudentLessonProgress.objects.create(
        student=student,
        lesson=lesson,
        iq_level='standard',
        current_day=3,
        status='in_progress',
    )


@pytest.fixture
def day_progress(db, lesson_progress):
    """2026-03-06: DayProgress record with 4-star mastery."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=1,
        status='completed',
        mastery_star_rating=4,
        mastery_passed=True,
        practice_score=8,
        comprehension_score=75.0,
    )


@pytest.fixture
def comprehension_response(db, student, lesson):
    """2026-03-06: A ComprehensionQuestionResponse with partial credit."""
    return ComprehensionQuestionResponse.objects.create(
        student=student,
        lesson=lesson,
        day_number=1,
        question_id='D1_CQ1',
        question_text='What is photosynthesis?',
        marks_available=3,
        marks_awarded=1,
        student_text='Plants make food using light.',
        llm_feedback='Good start! Mention chlorophyll.',
        llm_error=False,
    )


@pytest.fixture
def llm_error_response(db, student, lesson):
    """2026-03-06: A ComprehensionQuestionResponse where LLM failed."""
    return ComprehensionQuestionResponse.objects.create(
        student=student,
        lesson=lesson,
        day_number=2,
        question_id='D2_CQ1',
        question_text='Explain the water cycle.',
        marks_available=5,
        marks_awarded=0,
        student_text='Water evaporates and comes back as rain.',
        llm_feedback='',
        llm_error=True,
    )


@pytest.fixture
def non_staff_client(db):
    """2026-03-06: Regular (non-staff) user client."""
    user = User.objects.create_user(username='regular_user', password='pass', is_staff=False)
    client = APIClient()
    token = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


# ---------------------------------------------------------------------------
# Service unit tests (15)
# ---------------------------------------------------------------------------

class TestStudentGrid:
    """2026-03-06: Tests for MentorDashboardService.get_student_grid."""

    @pytest.mark.django_db
    def test_student_grid_green_status(self, mentor, student, assignment, day_progress):
        """2026-03-06: Student with high stars and recent activity → green."""
        grid = MentorDashboardService.get_student_grid(mentor)
        assert len(grid) == 1
        item = grid[0]
        assert item['student_id'] == str(student.id)
        # 2026-03-06: avg_stars=4.0 and last_active today → should be green
        assert item['color'] == 'green'
        assert item['avg_stars'] == 4.0

    @pytest.mark.django_db
    def test_student_grid_amber_status(self, mentor, student, assignment, lesson_progress, lesson):
        """2026-03-06: Student with low-ish stars → amber."""
        DayProgress.objects.create(
            lesson_progress=lesson_progress, day_number=1,
            status='completed', mastery_star_rating=2,
        )
        grid = MentorDashboardService.get_student_grid(mentor)
        assert len(grid) == 1
        assert grid[0]['color'] == 'amber'

    @pytest.mark.django_db
    def test_student_grid_red_status(self, mentor, student, assignment, lesson_progress, lesson):
        """2026-03-06: Student inactive > 7 days → red."""
        old_date = date.today() - timedelta(days=10)
        dp = DayProgress.objects.create(
            lesson_progress=lesson_progress, day_number=1,
            status='completed', mastery_star_rating=4,
        )
        # 2026-03-06: Manipulate updated_at to simulate old activity
        StudentLessonProgress.objects.filter(pk=lesson_progress.pk).update(
            updated_at=old_date
        )
        grid = MentorDashboardService.get_student_grid(mentor)
        assert len(grid) == 1
        assert grid[0]['color'] == 'red'

    @pytest.mark.django_db
    def test_student_grid_grey_no_activity(self, mentor, student, assignment):
        """2026-03-06: Student with no day progress → grey."""
        grid = MentorDashboardService.get_student_grid(mentor)
        assert len(grid) == 1
        assert grid[0]['color'] == 'grey'
        assert grid[0]['avg_stars'] is None

    @pytest.mark.django_db
    def test_student_grid_pending_reviews_count(
        self, mentor, student, assignment, comprehension_response
    ):
        """2026-03-06: pending_reviews reflects un-reviewed partial responses."""
        grid = MentorDashboardService.get_student_grid(mentor)
        assert grid[0]['pending_reviews'] == 1

    @pytest.mark.django_db
    def test_get_student_detail_returns_lesson_breakdown(
        self, mentor, student, assignment, lesson_progress, day_progress
    ):
        """2026-03-06: Student detail returns lesson and day data."""
        detail = MentorDashboardService.get_student_detail(mentor, str(student.id))
        assert detail is not None
        assert detail['student_id'] == str(student.id)
        assert len(detail['lessons']) == 1
        assert len(detail['lessons'][0]['days']) == 1
        assert detail['lessons'][0]['days'][0]['mastery_star_rating'] == 4


class TestReviewQueue:
    """2026-03-06: Tests for MentorDashboardService.get_review_queue / submit_review."""

    @pytest.mark.django_db
    def test_review_queue_returns_low_scoring_responses(
        self, mentor, student, assignment, comprehension_response
    ):
        """2026-03-06: Partial-credit response appears in queue."""
        queue = MentorDashboardService.get_review_queue(mentor)
        assert len(queue) == 1
        assert queue[0]['id'] == str(comprehension_response.id)
        assert queue[0]['marks_awarded'] == 1

    @pytest.mark.django_db
    def test_review_queue_returns_llm_error_responses(
        self, mentor, student, assignment, llm_error_response
    ):
        """2026-03-06: LLM-error response appears in queue."""
        queue = MentorDashboardService.get_review_queue(mentor)
        assert len(queue) == 1
        assert queue[0]['llm_error'] is True

    @pytest.mark.django_db
    def test_submit_review_creates_record(
        self, mentor, student, assignment, comprehension_response
    ):
        """2026-03-06: submit_review creates a ComprehensionReview record."""
        review = MentorDashboardService.submit_review(
            mentor, str(comprehension_response.id), score=3, notes='Decent effort.'
        )
        assert review is not None
        assert review.mentor_score == 3
        assert review.mentor_notes == 'Decent effort.'
        assert ComprehensionReview.objects.filter(pk=review.pk).exists()

    @pytest.mark.django_db
    def test_submit_review_requires_assigned_student(
        self, mentor, other_student, comprehension_response
    ):
        """2026-03-06: submit_review returns None for unassigned student's response."""
        # 2026-03-06: comprehension_response belongs to 'student', not 'other_student'
        # mentor has no assignment to other_student — but response is already for 'student'
        # so we look up by ID but mentor has no assignment → returns None
        # Create a response for other_student to test the guard
        other_lesson = TeachingLesson.objects.create(
            lesson_id='MNT_OTHER_W01', title='Other', subject='Math',
            class_number=5, week_number=1,
            content_json_path='json/math/class5/week1.json', status='published',
        )
        other_resp = ComprehensionQuestionResponse.objects.create(
            student=other_student, lesson=other_lesson,
            day_number=1, question_id='D1_CQ1', question_text='Q',
            marks_available=2, marks_awarded=0, student_text='A',
        )
        result = MentorDashboardService.submit_review(mentor, str(other_resp.id), score=2)
        assert result is None

    @pytest.mark.django_db
    def test_mentor_assignment_unique_together(self, mentor, student, assignment):
        """2026-03-06: Duplicate (mentor, student) assignment raises IntegrityError."""
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            MentorAssignment.objects.create(mentor=mentor, student=student)


class TestWeeklySummary:
    """2026-03-06: Tests for MentorDashboardService weekly summary methods."""

    @pytest.mark.django_db
    def test_get_weekly_summary_returns_existing(self, mentor, student, assignment):
        """2026-03-06: Returns cached summary if one exists for current week."""
        monday = date.today() - timedelta(days=date.today().weekday())
        summary = WeeklySummary.objects.create(
            student=student, week_start=monday,
            summary_text='Great week!', lessons_completed=3,
            avg_star_rating=4.0, generated_by=mentor,
        )
        result = MentorDashboardService.get_or_generate_weekly_summary(mentor, str(student.id))
        assert result.id == summary.id
        assert result.summary_text == 'Great week!'

    @pytest.mark.django_db
    def test_generate_weekly_summary_calls_llm(self, mentor, student, assignment):
        """2026-03-06: generate_fresh_summary invokes LLM and stores result."""
        mock_response = MagicMock()
        mock_response.text = 'AI-generated summary text.'
        mock_llm = MagicMock()
        mock_llm.chat.return_value = mock_response

        with patch(
            'services.mentor_dashboard_service.services.get_llm_provider',
            return_value=mock_llm,
        ):
            summary = MentorDashboardService.generate_fresh_summary(mentor, str(student.id))

        assert summary is not None
        assert summary.summary_text == 'AI-generated summary text.'
        mock_llm.chat.assert_called_once()

    @pytest.mark.django_db
    def test_generate_weekly_summary_llm_fallback(self, mentor, student, assignment):
        """2026-03-06: LLM failure → fallback summary text is used."""
        with patch(
            'services.mentor_dashboard_service.services.get_llm_provider',
            side_effect=Exception('LLM offline'),
        ):
            summary = MentorDashboardService.generate_fresh_summary(mentor, str(student.id))

        assert summary is not None
        assert student.full_name in summary.summary_text


class TestDraftMessage:
    """2026-03-06: Tests for MentorDashboardService.draft_parent_message."""

    @pytest.mark.django_db
    def test_draft_message_calls_llm(self, mentor, student, assignment):
        """2026-03-06: draft_parent_message returns LLM-generated text."""
        mock_response = MagicMock()
        mock_response.text = 'Dear Parent, your child is doing well.'
        mock_llm = MagicMock()
        mock_llm.chat.return_value = mock_response

        with patch(
            'services.mentor_dashboard_service.services.get_llm_provider',
            return_value=mock_llm,
        ):
            draft = MentorDashboardService.draft_parent_message(
                mentor, str(student.id), context_hint='focus on math'
            )

        assert draft == 'Dear Parent, your child is doing well.'
        mock_llm.chat.assert_called_once()

    @pytest.mark.django_db
    def test_get_message_threads_filters_by_mentor(self, mentor, student, parent_obj, assignment):
        """2026-03-06: get_message_threads returns only this mentor's threads."""
        thread = MessageThread.objects.create(
            student=student, parent=parent_obj, monitor=mentor, subject='Weekly check'
        )
        other_mentor = User.objects.create_user(
            username='other_mentor', password='pass', is_staff=True
        )
        MessageThread.objects.create(
            student=student, parent=parent_obj, monitor=other_mentor, subject='Other'
        )
        threads = list(MentorDashboardService.get_message_threads(mentor))
        assert len(threads) == 1
        assert threads[0].id == thread.id


# ---------------------------------------------------------------------------
# API integration tests (15)
# ---------------------------------------------------------------------------

class TestDashboardAuth:
    """2026-03-06: Auth and access control tests for dashboard endpoint."""

    @pytest.mark.django_db
    def test_dashboard_requires_staff_auth(self, db):
        """2026-03-06: Unauthenticated request → 401."""
        client = APIClient()
        resp = client.get('/api/v1/mentor/dashboard/')
        assert resp.status_code == 401

    @pytest.mark.django_db
    def test_non_staff_cannot_access_dashboard(self, non_staff_client):
        """2026-03-06: Non-staff (is_staff=False) user → 403."""
        resp = non_staff_client.get('/api/v1/mentor/dashboard/')
        assert resp.status_code == 403

    @pytest.mark.django_db
    def test_dashboard_returns_student_grid(self, mentor_client, student, assignment):
        """2026-03-06: Staff mentor gets list of assigned students."""
        resp = mentor_client.get('/api/v1/mentor/dashboard/')
        assert resp.status_code == 200
        assert isinstance(resp.data, list)
        assert len(resp.data) == 1
        assert resp.data[0]['student_id'] == str(student.id)


class TestStudentDetailAPI:
    """2026-03-06: /api/v1/mentor/students/<uuid>/ endpoint tests."""

    @pytest.mark.django_db
    def test_student_detail_404_unassigned(self, mentor_client, other_student):
        """2026-03-06: Unassigned student → 404."""
        resp = mentor_client.get(f'/api/v1/mentor/students/{other_student.id}/')
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_student_detail_200_assigned(self, mentor_client, student, assignment, lesson_progress):
        """2026-03-06: Assigned student → 200 with lessons data."""
        resp = mentor_client.get(f'/api/v1/mentor/students/{student.id}/')
        assert resp.status_code == 200
        assert resp.data['student_id'] == str(student.id)
        assert 'lessons' in resp.data


class TestReviewQueueAPI:
    """2026-03-06: /api/v1/mentor/review-queue/ endpoint tests."""

    @pytest.mark.django_db
    def test_review_queue_empty(self, mentor_client, assignment):
        """2026-03-06: No low-scoring responses → empty list."""
        resp = mentor_client.get('/api/v1/mentor/review-queue/')
        assert resp.status_code == 200
        assert resp.data == []

    @pytest.mark.django_db
    def test_review_queue_with_items(
        self, mentor_client, assignment, comprehension_response
    ):
        """2026-03-06: Partial-credit response appears in queue."""
        resp = mentor_client.get('/api/v1/mentor/review-queue/')
        assert resp.status_code == 200
        assert len(resp.data) == 1

    @pytest.mark.django_db
    def test_submit_review_valid(
        self, mentor_client, assignment, comprehension_response
    ):
        """2026-03-06: Valid POST → 201 with review data."""
        payload = {'mentor_score': 3, 'mentor_notes': 'Nice try.'}
        resp = mentor_client.post(
            f'/api/v1/mentor/review-queue/{comprehension_response.id}/', payload, format='json'
        )
        assert resp.status_code == 201
        assert resp.data['mentor_score'] == 3

    @pytest.mark.django_db
    def test_submit_review_invalid_score(
        self, mentor_client, assignment, comprehension_response
    ):
        """2026-03-06: Score out of range → 400."""
        payload = {'mentor_score': 9}
        resp = mentor_client.post(
            f'/api/v1/mentor/review-queue/{comprehension_response.id}/', payload, format='json'
        )
        assert resp.status_code == 400

    @pytest.mark.django_db
    def test_submit_review_unassigned_student_404(
        self, mentor_client, other_student
    ):
        """2026-03-06: Review for unassigned student's response → 404."""
        other_lesson = TeachingLesson.objects.create(
            lesson_id='MNT_API_OTHER_W01', title='Other API', subject='Math',
            class_number=5, week_number=1,
            content_json_path='json/math/class5/week1.json', status='published',
        )
        resp_obj = ComprehensionQuestionResponse.objects.create(
            student=other_student, lesson=other_lesson,
            day_number=1, question_id='D1_CQ1', question_text='Q',
            marks_available=2, marks_awarded=0, student_text='A',
        )
        payload = {'mentor_score': 2}
        resp = mentor_client.post(
            f'/api/v1/mentor/review-queue/{resp_obj.id}/', payload, format='json'
        )
        assert resp.status_code == 404


class TestWeeklySummaryAPI:
    """2026-03-06: /api/v1/mentor/students/<uuid>/summary/ endpoint tests."""

    @pytest.mark.django_db
    def test_weekly_summary_not_found_404(self, mentor_client, student, assignment):
        """2026-03-06: No existing summary → 404."""
        resp = mentor_client.get(f'/api/v1/mentor/students/{student.id}/summary/')
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_weekly_summary_found_200(self, mentor_client, student, assignment, mentor):
        """2026-03-06: Existing summary → 200."""
        monday = date.today() - timedelta(days=date.today().weekday())
        WeeklySummary.objects.create(
            student=student, week_start=monday, summary_text='Good week.',
            lessons_completed=2, avg_star_rating=3.5, generated_by=mentor,
        )
        resp = mentor_client.get(f'/api/v1/mentor/students/{student.id}/summary/')
        assert resp.status_code == 200
        assert resp.data['summary_text'] == 'Good week.'

    @pytest.mark.django_db
    def test_generate_summary_creates(self, mentor_client, student, assignment):
        """2026-03-06: POST /summary/generate/ creates a WeeklySummary."""
        mock_response = MagicMock()
        mock_response.text = 'Generated by API test.'
        mock_llm = MagicMock()
        mock_llm.chat.return_value = mock_response

        with patch(
            'services.mentor_dashboard_service.services.get_llm_provider',
            return_value=mock_llm,
        ):
            resp = mentor_client.post(
                f'/api/v1/mentor/students/{student.id}/summary/generate/'
            )

        assert resp.status_code == 201
        assert WeeklySummary.objects.filter(student=student).exists()


class TestMessagingAPI:
    """2026-03-06: /api/v1/mentor/messages/ and draft-message endpoint tests."""

    @pytest.mark.django_db
    def test_messages_returns_threads(
        self, mentor_client, mentor, student, parent_obj, assignment
    ):
        """2026-03-06: Mentor sees their own threads."""
        MessageThread.objects.create(
            student=student, parent=parent_obj, monitor=mentor, subject='Hello'
        )
        resp = mentor_client.get('/api/v1/mentor/messages/')
        assert resp.status_code == 200
        assert len(resp.data) == 1
        assert resp.data[0]['student_id'] == str(student.id)

    @pytest.mark.django_db
    def test_draft_message_returns_text(self, mentor_client, student, assignment):
        """2026-03-06: POST /draft-message/ returns AI-generated draft."""
        mock_response = MagicMock()
        mock_response.text = 'Dear Parent, just a quick note.'
        mock_llm = MagicMock()
        mock_llm.chat.return_value = mock_response

        with patch(
            'services.mentor_dashboard_service.services.get_llm_provider',
            return_value=mock_llm,
        ):
            resp = mentor_client.post(
                f'/api/v1/mentor/students/{student.id}/draft-message/',
                {'context_hint': 'attendance'},
                format='json',
            )

        assert resp.status_code == 200
        assert 'draft' in resp.data
        assert resp.data['draft'] == 'Dear Parent, just a quick note.'
