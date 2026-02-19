"""
2026-02-19: Tests for Read-Along & Mimic Engine service layer (BS-RAM).

Purpose:
    15 unit tests covering _score_to_stars thresholds, get_content,
    submit_session, get_history, and language registry helpers.
"""

import pytest  # 2026-02-19: Pytest framework
from datetime import date  # 2026-02-19: DOB for student fixture
from unittest.mock import patch, MagicMock  # 2026-02-19: Mocking

from django.contrib.auth import get_user_model  # 2026-02-19: User model
from rest_framework.exceptions import ValidationError, NotFound  # 2026-02-19: Exceptions

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import TeachingLesson  # 2026-02-19: Lesson model
from services.read_along_service.services import ReadAlongService  # 2026-02-19: Under test
from services.read_along_service.models import Language, ReadAlongSession  # 2026-02-19: Models
from services.read_along_service.language_registry import (  # 2026-02-19: Registry helpers
    LANGUAGE_SEED, get_active_languages, get_language, is_valid_language,
    get_student_languages,
)

User = get_user_model()  # 2026-02-19: Django User model

# 2026-02-19: Sample content JSON path (has read_along on all 4 days)
SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-19: Create parent user for testing."""
    user = User.objects.create_user(username='ra_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919876543291', full_name='RA Test Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-19: Create student with Telugu+Hindi+English languages."""
    user = User.objects.create_user(username='ra_student', password='testpass123')
    student = Student.objects.create(
        parent=parent_user, user=user, full_name='RA Test Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1, login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )
    return student


@pytest.fixture
def lesson(db):
    """2026-02-19: Create a published teaching lesson pointing at week1.json."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_MRIDANG_W01_RAM',
        title='The Wise Owl',
        subject='English',
        class_number=1,
        week_number=1,
        content_json_path=SAMPLE_CONTENT_PATH,
        status='published',
    )


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


# ── 1. _score_to_stars ─────────────────────────────────────────────────────

class TestScoreToStars:
    """2026-02-19: Tests for the pure _score_to_stars helper."""

    def test_score_to_stars_boundaries(self):
        """2026-02-19: Verify all 6 threshold boundaries map to correct stars."""
        fn = ReadAlongService._score_to_stars
        assert fn(0.00) == 0   # 2026-02-19: Below first threshold
        assert fn(0.39) == 0   # 2026-02-19: Just below 0 → 1 boundary
        assert fn(0.40) == 1   # 2026-02-19: At boundary
        assert fn(0.54) == 1   # 2026-02-19: Just below 1 → 2 boundary
        assert fn(0.55) == 2   # 2026-02-19: At boundary
        assert fn(0.69) == 2   # 2026-02-19: Just below 2 → 3 boundary
        assert fn(0.70) == 3   # 2026-02-19: At boundary
        assert fn(0.81) == 3   # 2026-02-19: Just below 3 → 4 boundary
        assert fn(0.82) == 4   # 2026-02-19: At boundary
        assert fn(0.91) == 4   # 2026-02-19: Just below 4 → 5 boundary
        assert fn(0.92) == 5   # 2026-02-19: At boundary
        assert fn(1.00) == 5   # 2026-02-19: Perfect score


# ── 2. get_content ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetContent:
    """2026-02-19: Tests for ReadAlongService.get_content."""

    def test_get_content_english(self, student_user, lesson):
        """2026-02-19: English content returns correct sentences."""
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'English')
        assert len(result['sentences']) == 4  # 2026-02-19: Day 1 has 4 sentences
        assert result['bcp47_tag'] == 'en-IN'
        assert result['tts_rate'] == 0.9
        assert 'Ollie' in result['sentences'][0]  # 2026-02-19: Correct content
        assert result['transliterations'] == []  # 2026-02-19: Empty for English

    def test_get_content_hindi(self, student_user, lesson):
        """2026-02-19: Hindi content returns sentences and transliterations."""
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'Hindi')
        assert len(result['sentences']) == 4
        assert result['bcp47_tag'] == 'hi-IN'
        assert len(result['transliterations']) == 4  # 2026-02-19: Hindi has transliterations
        assert result['tts_rate'] == 0.85

    def test_get_content_telugu(self, student_user, lesson):
        """2026-02-19: Telugu content returns Devanagari sentences."""
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'Telugu')
        assert len(result['sentences']) == 4
        assert result['bcp47_tag'] == 'te-IN'
        assert len(result['transliterations']) == 4

    def test_get_content_invalid_language(self, student_user, lesson):
        """2026-02-19: Invalid language raises ValidationError."""
        with pytest.raises(ValidationError):
            ReadAlongService.get_content(student_user, str(lesson.id), 1, 'Klingon')

    def test_get_content_missing_day(self, student_user, lesson):
        """2026-02-19: Day not in JSON raises NotFound."""
        with pytest.raises(NotFound):
            ReadAlongService.get_content(student_user, str(lesson.id), 9, 'English')

    def test_get_content_student_languages(self, student_user, lesson):
        """2026-02-19: student_languages includes student's assigned languages."""
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'English')
        langs = result['student_languages']
        assert 'English' in langs
        assert 'Hindi' in langs
        assert 'Telugu' in langs

    def test_get_content_previous_best_none(self, student_user, lesson):
        """2026-02-19: No prior sessions → previous_best is None."""
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'English')
        assert result['previous_best'] is None

    def test_get_content_previous_best(self, student_user, lesson):
        """2026-02-19: After a session, previous_best has star_rating."""
        # 2026-02-19: Create a completed session
        ReadAlongSession.objects.create(
            student=student_user,
            lesson=lesson,
            day_number=1,
            language='English',
            bcp47_tag='en-IN',
            sentence_scores=[0.9, 0.8],
            overall_score=0.85,
            star_rating=4,
            sentences_attempted=2,
            sentences_total=2,
            attempt_number=1,
            status='completed',
        )
        result = ReadAlongService.get_content(student_user, str(lesson.id), 1, 'English')
        assert result['previous_best'] is not None
        assert result['previous_best']['star_rating'] == 4
        assert result['previous_best']['overall_score'] == 0.85


# ── 3. submit_session ──────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitSession:
    """2026-02-19: Tests for ReadAlongService.submit_session."""

    def test_submit_session_creates_record(self, student_user, lesson):
        """2026-02-19: submit_session creates a ReadAlongSession row in DB."""
        ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English',
            [0.9, 0.8, 0.85, 0.92], 45,
        )
        assert ReadAlongSession.objects.filter(
            student=student_user, lesson=lesson, day_number=1, language='English'
        ).count() == 1

    def test_submit_session_calculates_stars(self, student_user, lesson):
        """2026-02-19: overall_score → correct star_rating via thresholds."""
        result = ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English',
            [0.95, 0.94, 0.93, 0.92], 40,
        )
        assert result['star_rating'] == 5
        assert result['overall_score'] >= 0.92

    def test_submit_session_is_new_best(self, student_user, lesson):
        """2026-02-19: First session is always a new best."""
        result = ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'Telugu',
            [0.75, 0.80, 0.70], 30,
        )
        assert result['is_new_best'] is True
        assert result['attempt_number'] == 1

    def test_submit_session_not_new_best(self, student_user, lesson):
        """2026-02-19: Lower score than previous is not a new best."""
        # 2026-02-19: First session with high score
        ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English',
            [0.95, 0.95, 0.95, 0.95], 40,
        )
        # 2026-02-19: Second session with lower score
        result = ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English',
            [0.40, 0.42, 0.38, 0.41], 40,
        )
        assert result['is_new_best'] is False

    def test_submit_session_attempt_number(self, student_user, lesson):
        """2026-02-19: attempt_number increments on retries."""
        r1 = ReadAlongService.submit_session(
            student_user, str(lesson.id), 2, 'Hindi', [0.7, 0.8], 20,
        )
        r2 = ReadAlongService.submit_session(
            student_user, str(lesson.id), 2, 'Hindi', [0.75, 0.85], 22,
        )
        assert r1['attempt_number'] == 1
        assert r2['attempt_number'] == 2

    def test_submit_session_invalid_language(self, student_user, lesson):
        """2026-02-19: Invalid language raises ValidationError."""
        with pytest.raises(ValidationError):
            ReadAlongService.submit_session(
                student_user, str(lesson.id), 1, 'Esperanto', [0.8], 10,
            )

    def test_submit_session_invalid_scores(self, student_user, lesson):
        """2026-02-19: Score > 1.0 raises ValidationError."""
        with pytest.raises(ValidationError):
            ReadAlongService.submit_session(
                student_user, str(lesson.id), 1, 'English', [1.5, 0.8], 10,
            )


# ── 4. get_history ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetHistory:
    """2026-02-19: Tests for ReadAlongService.get_history."""

    def test_get_history_empty(self, student_user, lesson):
        """2026-02-19: No sessions → empty list."""
        result = ReadAlongService.get_history(
            student_user, str(lesson.id), 1, 'English'
        )
        assert result['sessions'] == []

    def test_get_history_with_sessions(self, student_user, lesson):
        """2026-02-19: Returns sessions in newest-first order."""
        ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English', [0.8, 0.9], 20,
        )
        ReadAlongService.submit_session(
            student_user, str(lesson.id), 1, 'English', [0.85, 0.92], 22,
        )
        result = ReadAlongService.get_history(
            student_user, str(lesson.id), 1, 'English'
        )
        sessions = result['sessions']
        assert len(sessions) == 2
        assert sessions[0]['attempt_number'] == 2  # 2026-02-19: Newest first
        assert sessions[1]['attempt_number'] == 1


# ── 5. language_registry helpers ───────────────────────────────────────────

@pytest.mark.django_db
class TestLanguageRegistry:
    """2026-02-19: Tests for DB helper functions in language_registry."""

    def test_get_language_registry_bcp47(self):
        """2026-02-19: get_language returns correct bcp47_tag from DB."""
        lang = get_language('Telugu')
        assert lang.bcp47_tag == 'te-IN'

    def test_is_valid_language_active(self):
        """2026-02-19: Active language is valid."""
        assert is_valid_language('Hindi') is True

    def test_is_valid_language_inactive(self):
        """2026-02-19: Deactivated language is not valid."""
        Language.objects.filter(name='Sanskrit').update(is_active=False)
        assert is_valid_language('Sanskrit') is False

    def test_get_student_languages(self, student_user):
        """2026-02-19: Returns student's active languages in order."""
        langs = get_student_languages(student_user)
        assert langs[0] == 'English'  # 2026-02-19: Always first / language_1
        assert 'Hindi' in langs
        assert 'Telugu' in langs
