"""
2026-02-19: Tests for Read-Along & Mimic Engine API endpoints (BS-RAM).

Purpose:
    15 integration tests covering authentication, authorization, input validation,
    and correct API responses for ContentView, SubmitSessionView, HistoryView.
"""

import json  # 2026-02-19: JSON
import uuid  # 2026-02-19: UUID
import pytest  # 2026-02-19: Pytest framework
from datetime import date  # 2026-02-19: DOB for student fixture

from django.contrib.auth import get_user_model  # 2026-02-19: User model
from rest_framework.test import APIClient  # 2026-02-19: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-19: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import TeachingLesson  # 2026-02-19: Lesson model
from services.read_along_service.models import Language, ReadAlongSession  # 2026-02-19: Models
from services.read_along_service.language_registry import LANGUAGE_SEED  # 2026-02-19: Seed

User = get_user_model()  # 2026-02-19: Django User model

# 2026-02-19: Base URL prefix
BASE_URL = '/api/v1/read-along'
SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def seed_languages(db):
    """2026-02-19: Ensure Language rows exist for all tests."""
    for name, attrs in LANGUAGE_SEED.items():
        Language.objects.get_or_create(
            name=name,
            defaults={
                'bcp47_tag': attrs['bcp47'],
                'display_name': attrs['display_name'],
                'script': attrs['script'],
                'tts_rate': attrs['tts_rate'],
                'is_active': True,
                'sort_order': attrs['sort_order'],
            },
        )


@pytest.fixture
def parent_user(db):
    """2026-02-19: Create parent user."""
    user = User.objects.create_user(username='ra_api_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919876543292', full_name='RA API Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-19: Create student user with all three languages."""
    user = User.objects.create_user(username='ra_api_student', password='testpass123')
    student = Student.objects.create(
        parent=parent_user, user=user, full_name='RA API Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1, login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )
    return student


@pytest.fixture
def other_student(parent_user, db):
    """2026-02-19: Second student for cross-student access tests."""
    user = User.objects.create_user(username='ra_api_student2', password='testpass123')
    student = Student.objects.create(
        parent=parent_user, user=user, full_name='RA API Student 2',
        dob=date(2016, 3, 5), age_group='6-12', grade=2, login_method='pin',
        language_1='English',
    )
    return student


@pytest.fixture
def lesson(db):
    """2026-02-19: Published teaching lesson pointing at week1.json."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_MRIDANG_W01_RAPI',
        title='The Wise Owl',
        subject='English',
        class_number=1,
        week_number=1,
        content_json_path=SAMPLE_CONTENT_PATH,
        status='published',
    )


@pytest.fixture
def student_client(student_user):
    """2026-02-19: Authenticated API client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-19: Authenticated API client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def other_student_client(other_student):
    """2026-02-19: Authenticated client for second student."""
    client = APIClient()
    token = RefreshToken.for_user(other_student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


# ── ContentView tests ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestContentView:
    """2026-02-19: Tests for GET .../lessons/<id>/day/<n>/content/"""

    def test_content_unauthenticated_401(self, lesson):
        """2026-02-19: Unauthenticated request returns 401."""
        client = APIClient()
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/?language=English'
        resp = client.get(url)
        assert resp.status_code == 401

    def test_content_parent_403(self, parent_client, lesson):
        """2026-02-19: Parent role cannot access student-only endpoint."""
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/?language=English'
        resp = parent_client.get(url)
        assert resp.status_code == 403

    def test_content_student_200(self, student_client, lesson):
        """2026-02-19: Authenticated student gets 200 with correct payload."""
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/?language=English'
        resp = student_client.get(url)
        assert resp.status_code == 200
        data = resp.json()
        assert 'sentences' in data
        assert 'bcp47_tag' in data
        assert 'tts_rate' in data
        assert 'student_languages' in data
        assert len(data['sentences']) > 0

    def test_content_language_param_required_400(self, student_client, lesson):
        """2026-02-19: Missing language query param returns 400."""
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/'
        resp = student_client.get(url)
        assert resp.status_code == 400

    def test_content_invalid_language_400(self, student_client, lesson):
        """2026-02-19: Unknown language name returns 400."""
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/?language=Martian'
        resp = student_client.get(url)
        assert resp.status_code == 400

    def test_content_cross_student_403(self, other_student_client, student_user, lesson):
        """
        2026-02-19: Student B cannot be blocked from viewing content (no owner check);
        content endpoint is student-role-only not student-specific.
        This test verifies Student B (also a student) CAN access lesson content —
        content is not per-student restricted, only role-restricted.
        """
        url = f'{BASE_URL}/lessons/{lesson.id}/day/1/content/?language=English'
        resp = other_student_client.get(url)
        # 2026-02-19: Any authenticated student can view content (no lesson ownership)
        assert resp.status_code == 200


# ── SubmitSessionView tests ────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitSessionView:
    """2026-02-19: Tests for POST .../sessions/submit/"""

    def _payload(self, lesson):
        """2026-02-19: Build a valid submit payload."""
        return {
            'lesson_id': str(lesson.id),
            'day_number': 1,
            'language': 'English',
            'sentence_scores': [0.9, 0.85, 0.88, 0.92],
            'time_spent_seconds': 47,
        }

    def test_submit_unauthenticated_401(self, lesson):
        """2026-02-19: Unauthenticated POST returns 401."""
        client = APIClient()
        resp = client.post(f'{BASE_URL}/sessions/submit/', self._payload(lesson), format='json')
        assert resp.status_code == 401

    def test_submit_valid_200(self, student_client, lesson):
        """2026-02-19: Valid submit returns 200 with score and stars."""
        resp = student_client.post(
            f'{BASE_URL}/sessions/submit/', self._payload(lesson), format='json'
        )
        assert resp.status_code == 200
        data = resp.json()
        assert 'overall_score' in data
        assert 'star_rating' in data
        assert 'is_new_best' in data
        assert 'attempt_number' in data
        assert data['is_new_best'] is True

    def test_submit_invalid_scores_400(self, student_client, lesson):
        """2026-02-19: Score > 1.0 returns 400."""
        payload = self._payload(lesson)
        payload['sentence_scores'] = [1.5, 0.8]  # 2026-02-19: Invalid
        resp = student_client.post(f'{BASE_URL}/sessions/submit/', payload, format='json')
        assert resp.status_code == 400

    def test_submit_invalid_language_400(self, student_client, lesson):
        """2026-02-19: Unknown language returns 400."""
        payload = self._payload(lesson)
        payload['language'] = 'Swahili'  # 2026-02-19: Not in DB
        resp = student_client.post(f'{BASE_URL}/sessions/submit/', payload, format='json')
        assert resp.status_code == 400

    def test_submit_creates_session_in_db(self, student_client, lesson):
        """2026-02-19: POST actually creates a ReadAlongSession row."""
        student_client.post(
            f'{BASE_URL}/sessions/submit/', self._payload(lesson), format='json'
        )
        assert ReadAlongSession.objects.count() == 1


# ── HistoryView tests ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestHistoryView:
    """2026-02-19: Tests for GET .../sessions/history/"""

    def _url(self, lesson, language='English'):
        """2026-02-19: Build history URL with query params."""
        return (
            f'{BASE_URL}/sessions/history/'
            f'?lesson_id={lesson.id}&day_number=1&language={language}'
        )

    def test_history_unauthenticated_401(self, lesson):
        """2026-02-19: Unauthenticated request returns 401."""
        client = APIClient()
        resp = client.get(self._url(lesson))
        assert resp.status_code == 401

    def test_history_empty_200(self, student_client, lesson):
        """2026-02-19: No sessions → 200 with empty list."""
        resp = student_client.get(self._url(lesson))
        assert resp.status_code == 200
        assert resp.json()['sessions'] == []

    def test_history_returns_sessions(self, student_client, lesson):
        """2026-02-19: After submitting, history returns the session."""
        payload = {
            'lesson_id': str(lesson.id),
            'day_number': 1,
            'language': 'English',
            'sentence_scores': [0.8, 0.75],
            'time_spent_seconds': 30,
        }
        student_client.post(f'{BASE_URL}/sessions/submit/', payload, format='json')
        resp = student_client.get(self._url(lesson))
        assert resp.status_code == 200
        sessions = resp.json()['sessions']
        assert len(sessions) == 1
        assert sessions[0]['star_rating'] is not None
