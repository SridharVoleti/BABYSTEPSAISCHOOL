"""
2026-02-20: Tests for Vocabulary Acquisition System API endpoints (BS-LNG).

Purpose:
    15 integration tests covering authentication, authorization, input
    validation, and correct API responses for all 5 vocabulary endpoints.
"""

import pytest  # 2026-02-20: Pytest framework
from datetime import date  # 2026-02-20: DOB for student fixture
from unittest.mock import patch, MagicMock  # 2026-02-20: LLM mock

from django.contrib.auth import get_user_model  # 2026-02-20: User model
from rest_framework.test import APIClient  # 2026-02-20: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-20: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-20: Auth models
from services.read_along_service.models import Language  # 2026-02-20: Language model
from services.read_along_service.language_registry import LANGUAGE_SEED  # 2026-02-20: Seed data
from services.vocabulary_service.models import (  # 2026-02-20: Vocabulary models
    VocabularyWord, VocabularySession, StudentWordProgress,
)

User = get_user_model()  # 2026-02-20: Django User model

# 2026-02-20: Base URL prefix
BASE_URL = '/api/v1/vocabulary'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def seed_languages(db):
    """2026-02-20: Ensure Language rows exist for all tests."""
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
    """2026-02-20: Create parent user."""
    user = User.objects.create_user(username='voc_api_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000000201', full_name='Vocab API Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-20: Grade 1 student with Hindi and Telugu languages."""
    user = User.objects.create_user(username='voc_api_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Vocab API Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1, login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )


@pytest.fixture
def ten_hindi_words(db):
    """2026-02-20: Create 12 Hindi Grade 1 words for session creation."""
    language = Language.objects.get(name='Hindi')
    words = []
    for i in range(1, 13):
        word = VocabularyWord.objects.create(
            language=language,
            grade=1,
            frequency_rank=2000 + i,
            word=f'एपीआई{i}',
            romanization=f'api{i}',
            word_type='noun',
            image_keyword=f'api_word{i}',
        )
        words.append(word)
    return words


@pytest.fixture
def student_client(student):
    """2026-02-20: Authenticated API client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-20: Authenticated API client for parent (wrong role)."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


def _mock_llm_context():
    """2026-02-20: Context manager that patches LLM to return valid content."""
    mock_response = MagicMock()
    mock_response.text = (
        '{"definition": "test def", "example_sentence": "test sent", '
        '"example_translation": "test trans", "mnemonic": ""}'
    )
    mock_provider = MagicMock()
    mock_provider.chat.return_value = mock_response
    return patch(
        'services.vocabulary_service.content_generator.get_llm_provider',
        return_value=mock_provider,
    )


# ── Auth tests ─────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAuth:
    """2026-02-20: Tests for authentication and role enforcement."""

    def test_unauthenticated_401(self):
        """2026-02-20: Unauthenticated request returns 401."""
        client = APIClient()
        resp = client.get(f'{BASE_URL}/session/?language=Hindi')
        assert resp.status_code == 401

    def test_parent_role_403(self, parent_client):
        """2026-02-20: Parent role cannot access student-only vocabulary endpoint."""
        resp = parent_client.get(f'{BASE_URL}/session/?language=Hindi')
        assert resp.status_code == 403


# ── TodaySession tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestTodaySession:
    """2026-02-20: Tests for GET /api/v1/vocabulary/session/"""

    def test_returns_200_with_10_words(self, student_client, ten_hindi_words):
        """2026-02-20: Valid request returns 200 with 10 words payload."""
        with _mock_llm_context():
            resp = student_client.get(f'{BASE_URL}/session/?language=Hindi')

        assert resp.status_code == 200
        data = resp.json()
        assert data['language'] == 'Hindi'
        assert len(data['words']) == 10
        assert 'session_id' in data
        assert 'bcp47_tag' in data
        assert 'student_languages' in data

    def test_missing_language_400(self, student_client):
        """2026-02-20: Missing ?language parameter returns 400."""
        resp = student_client.get(f'{BASE_URL}/session/')
        assert resp.status_code == 400

    def test_unknown_language_400(self, student_client):
        """2026-02-20: Unknown language name returns 400."""
        resp = student_client.get(f'{BASE_URL}/session/?language=Martian')
        assert resp.status_code == 400


# ── RecordPronunciation tests ──────────────────────────────────────────────

@pytest.mark.django_db
class TestRecordPronunciation:
    """2026-02-20: Tests for POST /api/v1/vocabulary/session/<id>/word/<id>/pronunciation/"""

    def _create_session(self, student_client, ten_hindi_words):
        """2026-02-20: Helper to create a session and return data."""
        with _mock_llm_context():
            resp = student_client.get(f'{BASE_URL}/session/?language=Hindi')
        return resp.json()

    def test_returns_200_ok(self, student_client, ten_hindi_words):
        """2026-02-20: Valid pronunciation score returns 200."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        url = f'{BASE_URL}/session/{session_id}/word/{word_id}/pronunciation/'
        resp = student_client.post(url, {'score': 0.85}, format='json')

        assert resp.status_code == 200
        data = resp.json()
        assert data['pronunciation_score'] == 0.85

    def test_invalid_score_400(self, student_client, ten_hindi_words):
        """2026-02-20: Score > 1.0 returns 400."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        url = f'{BASE_URL}/session/{session_id}/word/{word_id}/pronunciation/'
        resp = student_client.post(url, {'score': 1.5}, format='json')

        assert resp.status_code == 400

    def test_wrong_session_403(self, student_client, parent_user, ten_hindi_words, db):
        """2026-02-20: Using a different student's session returns 403."""
        # 2026-02-20: Create session for original student
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        # 2026-02-20: Create a second student and their client
        user2 = User.objects.create_user(username='voc_other_student', password='pass')
        other_student = Student.objects.create(
            parent=parent_user, user=user2, full_name='Other Student',
            dob=date(2016, 1, 1), age_group='6-12', grade=1, login_method='pin',
            language_1='English',
        )
        other_client = APIClient()
        token = RefreshToken.for_user(user2)
        other_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')

        url = f'{BASE_URL}/session/{session_id}/word/{word_id}/pronunciation/'
        resp = other_client.post(url, {'score': 0.80}, format='json')

        assert resp.status_code == 403


# ── RecordMCQ tests ────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecordMCQ:
    """2026-02-20: Tests for POST /api/v1/vocabulary/session/<id>/word/<id>/mcq/"""

    def _create_session(self, student_client, ten_hindi_words):
        """2026-02-20: Helper to create a session and return data."""
        with _mock_llm_context():
            resp = student_client.get(f'{BASE_URL}/session/?language=Hindi')
        return resp.json()

    def test_returns_200_correct(self, student_client, ten_hindi_words):
        """2026-02-20: Correct MCQ answer returns 200."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        url = f'{BASE_URL}/session/{session_id}/word/{word_id}/mcq/'
        resp = student_client.post(url, {'correct': True}, format='json')

        assert resp.status_code == 200
        assert resp.json()['mcq_correct'] is True

    def test_returns_200_wrong(self, student_client, ten_hindi_words):
        """2026-02-20: Wrong MCQ answer also returns 200 (not an error)."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        url = f'{BASE_URL}/session/{session_id}/word/{word_id}/mcq/'
        resp = student_client.post(url, {'correct': False}, format='json')

        assert resp.status_code == 200
        assert resp.json()['mcq_correct'] is False

    def test_word_not_in_session_404(self, student_client, ten_hindi_words, db):
        """2026-02-20: Using a word not in the session returns 404."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']

        # 2026-02-20: Use a word UUID that doesn't exist in the session
        import uuid
        fake_word_id = str(uuid.uuid4())
        url = f'{BASE_URL}/session/{session_id}/word/{fake_word_id}/mcq/'
        resp = student_client.post(url, {'correct': True}, format='json')

        assert resp.status_code == 404


# ── CompleteSession tests ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompleteSession:
    """2026-02-20: Tests for POST /api/v1/vocabulary/session/<id>/complete/"""

    def _create_session(self, student_client, ten_hindi_words):
        """2026-02-20: Helper to create a session."""
        with _mock_llm_context():
            resp = student_client.get(f'{BASE_URL}/session/?language=Hindi')
        return resp.json()

    def test_returns_200_with_stars(self, student_client, ten_hindi_words):
        """2026-02-20: Complete session returns 200 with star rating."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']

        url = f'{BASE_URL}/session/{session_id}/complete/'
        resp = student_client.post(url)

        assert resp.status_code == 200
        data = resp.json()
        assert 'fluency_star_rating' in data
        assert 'fluency_score' in data
        assert 'words_mastered' in data

    def test_already_completed_400(self, student_client, ten_hindi_words):
        """2026-02-20: Completing an already-completed session returns 400."""
        session_data = self._create_session(student_client, ten_hindi_words)
        session_id = session_data['session_id']

        url = f'{BASE_URL}/session/{session_id}/complete/'
        student_client.post(url)  # 2026-02-20: First completion
        resp = student_client.post(url)  # 2026-02-20: Second completion

        assert resp.status_code == 400


# ── Progress tests ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestProgress:
    """2026-02-20: Tests for GET /api/v1/vocabulary/progress/"""

    def test_returns_200_with_stats(self, student_client):
        """2026-02-20: Valid progress request returns 200 with stats."""
        resp = student_client.get(f'{BASE_URL}/progress/?language=Hindi')

        assert resp.status_code == 200
        data = resp.json()
        assert 'introduced_count' in data
        assert 'mastered_count' in data
        assert 'current_streak' in data
        assert 'today_completed' in data

    def test_no_activity_returns_zeros(self, student_client):
        """2026-02-20: New student returns all zero counts."""
        resp = student_client.get(f'{BASE_URL}/progress/?language=Hindi')

        assert resp.status_code == 200
        data = resp.json()
        assert data['introduced_count'] == 0
        assert data['mastered_count'] == 0
        assert data['current_streak'] == 0
