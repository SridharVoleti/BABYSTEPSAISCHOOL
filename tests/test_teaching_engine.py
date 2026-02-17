"""
2026-02-17: Tests for AI Teaching Engine service.

Purpose:
    Test content loader, teaching service, tutoring service,
    and API endpoints for the teaching engine module.
"""

import json  # 2026-02-17: JSON
import os  # 2026-02-17: File operations
import pytest  # 2026-02-17: Pytest framework
from datetime import date  # 2026-02-17: Date for DOB
from unittest.mock import patch, MagicMock  # 2026-02-17: Mocking

from django.contrib.auth import get_user_model  # 2026-02-17: User model
from django.conf import settings  # 2026-02-17: Settings
from rest_framework.test import APIClient  # 2026-02-17: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-17: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-17: Auth models
from services.teaching_engine.models import (  # 2026-02-17: Models
    TeachingLesson, StudentLessonProgress, DayProgress,
    WeeklyAssessmentAttempt, TutoringSession,
)
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-17: Loader
from services.teaching_engine.services import TeachingService  # 2026-02-17: Service
from services.teaching_engine.tutoring import TutoringService  # 2026-02-17: Tutoring

User = get_user_model()  # 2026-02-17: Django User model

# 2026-02-17: Sample content JSON path (relative to project root)
SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-17: Create a parent user for testing."""
    user = User.objects.create_user(  # 2026-02-17: Django user
        username='test_parent_teach', password='testpass123'
    )
    parent = Parent.objects.create(  # 2026-02-17: Parent profile
        user=user,
        phone='+919876543299',
        full_name='Test Parent Teach',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-17: Create a student user for testing."""
    user = User.objects.create_user(  # 2026-02-17: Django user
        username='test_student_teach', password='testpass123'
    )
    student = Student.objects.create(  # 2026-02-17: Student profile
        parent=parent_user,
        user=user,
        full_name='Test Student Teach',
        dob=date(2019, 5, 15),  # 2026-02-17: Class 1 age
        age_group='6-12',
        grade=1,
        login_method='pin',
    )
    return student


@pytest.fixture
def student_client(student_user):
    """2026-02-17: Authenticated API client for student."""
    client = APIClient()  # 2026-02-17: DRF test client
    token = RefreshToken.for_user(student_user.user)  # 2026-02-17: JWT
    client.credentials(  # 2026-02-17: Auth header
        HTTP_AUTHORIZATION=f'Bearer {token.access_token}'
    )
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-17: Authenticated API client for parent (should be denied)."""
    client = APIClient()  # 2026-02-17: DRF test client
    token = RefreshToken.for_user(parent_user.user)  # 2026-02-17: JWT
    client.credentials(  # 2026-02-17: Auth header
        HTTP_AUTHORIZATION=f'Bearer {token.access_token}'
    )
    return client


@pytest.fixture
def published_lesson(db):
    """2026-02-17: Create a published teaching lesson."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_MRIDANG_W01',
        title='The Wise Owl - Week 1',
        subject='English',
        class_number=1,
        chapter_id='MRIDANG_CH01',
        chapter_title='The Wise Owl',
        week_number=1,
        character_name='Ollie the Owl',
        learning_objectives=['Identify vocabulary', 'Explain wise'],
        content_json_path=SAMPLE_CONTENT_PATH,
        status='published',
    )


@pytest.fixture
def draft_lesson(db):
    """2026-02-17: Create a draft (unpublished) lesson."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_MRIDANG_W02',
        title='The Wise Owl - Week 2',
        subject='English',
        class_number=1,
        week_number=2,
        content_json_path='json/teaching/class1/English/week2.json',
        status='draft',
    )


@pytest.fixture(autouse=True)
def clear_content_cache():
    """2026-02-17: Clear content loader cache before each test."""
    TeachingContentLoader.clear_cache()  # 2026-02-17: Reset
    yield
    TeachingContentLoader.clear_cache()  # 2026-02-17: Cleanup


# ── Content Loader Tests ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestTeachingContentLoader:
    """2026-02-17: Tests for TeachingContentLoader."""

    def test_load_lesson(self):
        """2026-02-17: Should load full lesson JSON from file."""
        data = TeachingContentLoader.load_lesson(SAMPLE_CONTENT_PATH)
        assert data['lesson_id'] == 'ENG1_MRIDANG_W01'
        assert data['class'] == 1
        assert data['subject'] == 'English'
        assert len(data['micro_lessons']) == 4

    def test_load_lesson_caching(self):
        """2026-02-17: Second load should use cache."""
        data1 = TeachingContentLoader.load_lesson(SAMPLE_CONTENT_PATH)
        data2 = TeachingContentLoader.load_lesson(SAMPLE_CONTENT_PATH)
        assert data1 is data2  # 2026-02-17: Same object from cache

    def test_load_lesson_file_not_found(self):
        """2026-02-17: Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            TeachingContentLoader.load_lesson('nonexistent/path.json')

    def test_get_day_content_foundation(self):
        """2026-02-17: Should return foundation-level content for day 1."""
        content = TeachingContentLoader.get_day_content(
            SAMPLE_CONTENT_PATH, 1, 'foundation'
        )
        assert content['micro_lesson_id'] == 'ENG1_MRIDANG_W01_D1'
        assert content['teaching_content']['pacing'] == 'slow'
        assert content['teaching_content']['repetition_count'] == 3
        assert content['teaching_content']['tts_rate'] == 0.7
        assert len(content['vocabulary']) == 3
        assert len(content['practice_questions']) == 3

    def test_get_day_content_advanced(self):
        """2026-02-17: Should return advanced-level content."""
        content = TeachingContentLoader.get_day_content(
            SAMPLE_CONTENT_PATH, 1, 'advanced'
        )
        assert content['teaching_content']['pacing'] == 'fast'
        assert content['teaching_content']['repetition_count'] == 1

    def test_get_day_content_invalid_day(self):
        """2026-02-17: Should raise ValueError for invalid day."""
        with pytest.raises(ValueError, match='day_number must be 1-4'):
            TeachingContentLoader.get_day_content(SAMPLE_CONTENT_PATH, 5, 'standard')

    def test_get_day_content_invalid_iq(self):
        """2026-02-17: Should raise ValueError for invalid IQ level."""
        with pytest.raises(ValueError, match='iq_level must be'):
            TeachingContentLoader.get_day_content(SAMPLE_CONTENT_PATH, 1, 'genius')

    def test_get_revision_prompts_day1(self):
        """2026-02-17: Day 1 should return empty revision prompts."""
        prompts = TeachingContentLoader.get_revision_prompts(
            SAMPLE_CONTENT_PATH, 1, 'standard'
        )
        assert prompts == []

    def test_get_revision_prompts_day2_foundation(self):
        """2026-02-17: Day 2 foundation should have more revision prompts."""
        prompts = TeachingContentLoader.get_revision_prompts(
            SAMPLE_CONTENT_PATH, 2, 'foundation'
        )
        assert len(prompts) == 3  # 2026-02-17: Foundation gets more revision

    def test_get_revision_prompts_day2_advanced(self):
        """2026-02-17: Day 2 advanced should have fewer revision prompts."""
        prompts = TeachingContentLoader.get_revision_prompts(
            SAMPLE_CONTENT_PATH, 2, 'advanced'
        )
        assert len(prompts) == 1  # 2026-02-17: Advanced gets brief revision

    def test_get_assessment(self):
        """2026-02-17: Should return weekly assessment data."""
        assessment = TeachingContentLoader.get_assessment(SAMPLE_CONTENT_PATH)
        assert assessment['assessment_id'] == 'ENG1_MRIDANG_W01_ASSESS'
        assert len(assessment['questions']) == 10
        assert assessment['time_limit_minutes'] == 15
        assert assessment['star_thresholds']['three_stars'] == 80

    def test_clear_cache(self):
        """2026-02-17: Cache should be clearable."""
        TeachingContentLoader.load_lesson(SAMPLE_CONTENT_PATH)
        assert len(TeachingContentLoader._cache) > 0
        TeachingContentLoader.clear_cache()
        assert len(TeachingContentLoader._cache) == 0


# ── Teaching Service Tests ────────────────────────────────────────────────

@pytest.mark.django_db
class TestTeachingServiceIQLevel:
    """2026-02-17: Tests for IQ level resolution."""

    def test_default_iq_level(self, student_user):
        """2026-02-17: Should return 'standard' when no diagnostic result."""
        level = TeachingService.get_student_iq_level(student_user)
        assert level == 'standard'

    def test_iq_from_diagnostic(self, student_user):
        """2026-02-17: Should return IQ from diagnostic result."""
        from services.diagnostic_service.models import DiagnosticSession, DiagnosticResult
        session = DiagnosticSession.objects.create(  # 2026-02-17: Required FK
            student=student_user,
            status='completed',
            theta_estimate=-1.0,
            items_administered=25,
            total_items=25,
            result_level='foundation',
        )
        DiagnosticResult.objects.create(
            student=student_user,
            session=session,
            overall_level='foundation',
            theta_final=-1.0,
            domain_levels={'literacy': 'foundation'},
        )
        level = TeachingService.get_student_iq_level(student_user)
        assert level == 'foundation'


@pytest.mark.django_db
class TestTeachingServiceLessons:
    """2026-02-17: Tests for lesson listing and detail."""

    def test_list_lessons(self, published_lesson, draft_lesson):
        """2026-02-17: Should only return published lessons."""
        result = TeachingService.list_lessons(class_number=1)
        assert result['success'] is True
        assert len(result['lessons']) == 1
        assert result['lessons'][0]['lesson_id'] == 'ENG1_MRIDANG_W01'

    def test_list_lessons_with_subject(self, published_lesson):
        """2026-02-17: Should filter by subject."""
        result = TeachingService.list_lessons(class_number=1, subject='English')
        assert len(result['lessons']) == 1
        result = TeachingService.list_lessons(class_number=1, subject='Math')
        assert len(result['lessons']) == 0

    def test_lesson_detail(self, student_user, published_lesson):
        """2026-02-17: Should return lesson detail without progress."""
        result = TeachingService.get_lesson_detail(student_user, 'ENG1_MRIDANG_W01')
        assert result['success'] is True
        assert result['lesson']['lesson_id'] == 'ENG1_MRIDANG_W01'
        assert result['progress'] is None

    def test_lesson_detail_not_found(self, student_user):
        """2026-02-17: Should return error for missing lesson."""
        result = TeachingService.get_lesson_detail(student_user, 'NONEXISTENT')
        assert result['success'] is False
        assert result['code'] == 'LESSON_NOT_FOUND'


@pytest.mark.django_db
class TestTeachingServiceDayFlow:
    """2026-02-17: Tests for start_day and complete_day flow."""

    def test_start_day1(self, student_user, published_lesson):
        """2026-02-17: Should start day 1 with teaching content."""
        result = TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        assert result['success'] is True
        assert result['day_number'] == 1
        assert result['iq_level'] == 'standard'
        assert result['day_status'] == 'teaching'  # 2026-02-17: Day 1 skips revision
        assert result['revision_prompts'] == []
        assert 'content' in result
        assert result['content']['micro_lesson_id'] == 'ENG1_MRIDANG_W01_D1'

    def test_start_day_creates_progress(self, student_user, published_lesson):
        """2026-02-17: Starting a day should create progress records."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        progress = StudentLessonProgress.objects.get(
            student=student_user, lesson=published_lesson
        )
        assert progress.current_day == 1
        assert progress.iq_level == 'standard'

    def test_cannot_skip_day(self, student_user, published_lesson):
        """2026-02-17: Should not allow skipping ahead."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.start_day(
            student_user, 'ENG1_MRIDANG_W01', day_number=3
        )
        assert result['success'] is False
        assert result['code'] == 'DAY_NOT_UNLOCKED'

    def test_complete_day1(self, student_user, published_lesson):
        """2026-02-17: Should complete day 1 and advance to day 2."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.complete_day(
            student_user, 'ENG1_MRIDANG_W01',
            day_number=1,
            practice_answers={'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
            time_spent=120,
        )
        assert result['success'] is True
        assert result['questions_correct'] == 3  # 2026-02-17: All correct
        assert result['score'] == 100
        assert result['next_day'] == 2
        assert result['assessment_unlocked'] is False

    def test_complete_day_partial_score(self, student_user, published_lesson):
        """2026-02-17: Should score partial answers correctly."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.complete_day(
            student_user, 'ENG1_MRIDANG_W01',
            day_number=1,
            practice_answers={'D1_Q1': 0, 'D1_Q2': 0, 'D1_Q3': 0},  # 2026-02-17: 1 correct
            time_spent=60,
        )
        assert result['questions_correct'] == 1
        assert result['score'] == 33  # 2026-02-17: 1/3 = 33%

    def test_start_day2_has_revision(self, student_user, published_lesson):
        """2026-02-17: Day 2 should start with revision prompts."""
        # 2026-02-17: Complete day 1 first
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        TeachingService.complete_day(
            student_user, 'ENG1_MRIDANG_W01',
            day_number=1,
            practice_answers={'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
            time_spent=120,
        )
        # 2026-02-17: Start day 2
        result = TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        assert result['success'] is True
        assert result['day_number'] == 2
        assert result['day_status'] == 'revision'  # 2026-02-17: Starts with revision
        assert len(result['revision_prompts']) > 0

    def test_complete_day4_unlocks_assessment(self, student_user, published_lesson):
        """2026-02-17: Completing day 4 should unlock assessment."""
        # 2026-02-17: Complete days 1-4
        answers_map = {
            1: {'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
            2: {'D2_Q1': 1, 'D2_Q2': 1, 'D2_Q3': 1},
            3: {'D3_Q1': 1, 'D3_Q2': 1, 'D3_Q3': 1},
            4: {'D4_Q1': 1, 'D4_Q2': 1, 'D4_Q3': 0},
        }
        for day in range(1, 5):
            TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
            result = TeachingService.complete_day(
                student_user, 'ENG1_MRIDANG_W01',
                day_number=day,
                practice_answers=answers_map[day],
                time_spent=120,
            )
        assert result['next_day'] == 5
        assert result['assessment_unlocked'] is True

    def test_lesson_not_found(self, student_user):
        """2026-02-17: Should return error for nonexistent lesson."""
        result = TeachingService.start_day(student_user, 'NONEXISTENT')
        assert result['success'] is False
        assert result['code'] == 'LESSON_NOT_FOUND'

    def test_invalid_day_number(self, student_user, published_lesson):
        """2026-02-17: Should reject day 5 for start_day."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.start_day(
            student_user, 'ENG1_MRIDANG_W01', day_number=5
        )
        assert result['success'] is False
        assert result['code'] == 'INVALID_DAY'


@pytest.mark.django_db
class TestTeachingServiceAssessment:
    """2026-02-17: Tests for weekly assessment flow."""

    def _complete_all_days(self, student, lesson_id):
        """2026-02-17: Helper to complete all 4 days."""
        answers_map = {
            1: {'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
            2: {'D2_Q1': 1, 'D2_Q2': 1, 'D2_Q3': 1},
            3: {'D3_Q1': 1, 'D3_Q2': 1, 'D3_Q3': 1},
            4: {'D4_Q1': 1, 'D4_Q2': 1, 'D4_Q3': 0},
        }
        for day in range(1, 5):
            TeachingService.start_day(student, lesson_id)
            TeachingService.complete_day(
                student, lesson_id,
                day_number=day,
                practice_answers=answers_map[day],
                time_spent=120,
            )

    def test_assessment_locked(self, student_user, published_lesson):
        """2026-02-17: Assessment should be locked before completing days."""
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.get_assessment(student_user, 'ENG1_MRIDANG_W01')
        assert result['success'] is False
        assert result['code'] == 'ASSESSMENT_LOCKED'

    def test_get_assessment(self, student_user, published_lesson):
        """2026-02-17: Should return assessment questions after days 1-4."""
        self._complete_all_days(student_user, 'ENG1_MRIDANG_W01')
        result = TeachingService.get_assessment(student_user, 'ENG1_MRIDANG_W01')
        assert result['success'] is True
        assert len(result['questions']) == 10
        assert result['attempt_number'] == 1
        # 2026-02-17: Verify correct answers are stripped
        for q in result['questions']:
            assert 'correct_answer' not in q

    def test_submit_assessment_three_stars(self, student_user, published_lesson):
        """2026-02-17: Perfect score should get 3 stars."""
        self._complete_all_days(student_user, 'ENG1_MRIDANG_W01')
        # 2026-02-17: All correct answers
        answers = {
            'WA_Q1': 1, 'WA_Q2': 2, 'WA_Q3': 1, 'WA_Q4': 2, 'WA_Q5': 1,
            'WA_Q6': 2, 'WA_Q7': 1, 'WA_Q8': 1, 'WA_Q9': 1, 'WA_Q10': 2,
        }
        result = TeachingService.submit_assessment(
            student_user, 'ENG1_MRIDANG_W01', answers, time_spent=300
        )
        assert result['success'] is True
        assert result['score'] == 20  # 2026-02-17: 10 x 2 points
        assert result['total_points'] == 20
        assert result['percentage'] == 100
        assert result['star_rating'] == 3

    def test_submit_assessment_zero_stars(self, student_user, published_lesson):
        """2026-02-17: All wrong should get 0 stars."""
        self._complete_all_days(student_user, 'ENG1_MRIDANG_W01')
        # 2026-02-17: All wrong answers
        answers = {
            'WA_Q1': 0, 'WA_Q2': 0, 'WA_Q3': 0, 'WA_Q4': 0, 'WA_Q5': 0,
            'WA_Q6': 0, 'WA_Q7': 0, 'WA_Q8': 0, 'WA_Q9': 0, 'WA_Q10': 0,
        }
        result = TeachingService.submit_assessment(
            student_user, 'ENG1_MRIDANG_W01', answers, time_spent=300
        )
        assert result['star_rating'] == 0
        assert result['percentage'] == 0

    def test_submit_assessment_marks_lesson_complete(self, student_user, published_lesson):
        """2026-02-17: Submitting assessment should mark lesson as completed."""
        self._complete_all_days(student_user, 'ENG1_MRIDANG_W01')
        answers = {
            'WA_Q1': 1, 'WA_Q2': 2, 'WA_Q3': 1, 'WA_Q4': 2, 'WA_Q5': 1,
            'WA_Q6': 2, 'WA_Q7': 1, 'WA_Q8': 1, 'WA_Q9': 1, 'WA_Q10': 2,
        }
        TeachingService.submit_assessment(
            student_user, 'ENG1_MRIDANG_W01', answers, time_spent=300
        )
        progress = StudentLessonProgress.objects.get(
            student=student_user, lesson=published_lesson
        )
        assert progress.status == 'completed'
        assert progress.assessment_star_rating == 3
        assert progress.completed_at is not None


# ── Tutoring Service Tests ────────────────────────────────────────────────

@pytest.mark.django_db
class TestTutoringService:
    """2026-02-17: Tests for AI tutoring chat service."""

    def test_chat_without_lesson(self, student_user):
        """2026-02-17: Should work without lesson context."""
        mock_response = MagicMock()
        mock_response.text = "Hello! What would you like to learn today?"

        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.return_value = mock_response
            result = TutoringService.chat(student_user, "Hello!")

        assert result['success'] is True
        assert 'reply' in result
        assert result['character'] == 'Mentor'
        assert result['message_count'] == 2  # 2026-02-17: Student + mentor

    def test_chat_with_lesson_context(self, student_user, published_lesson):
        """2026-02-17: Should use lesson context when available."""
        # 2026-02-17: Start a day to create progress
        TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01')

        mock_response = MagicMock()
        mock_response.text = "Great question about Ollie!"

        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.return_value = mock_response
            result = TutoringService.chat(
                student_user, "Who is Ollie?",
                lesson_id='ENG1_MRIDANG_W01', day_number=1,
            )

        assert result['success'] is True
        assert result['character'] == 'Ollie the Owl'

    def test_chat_llm_error_fallback(self, student_user):
        """2026-02-17: Should return fallback on LLM error."""
        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.side_effect = Exception("LLM down")
            result = TutoringService.chat(student_user, "Hello!")

        assert result['success'] is True
        assert 'trouble' in result['reply'].lower()

    def test_chat_safety_filter(self, student_user):
        """2026-02-17: Should filter unsafe content."""
        mock_response = MagicMock()
        mock_response.text = "Let me tell you about violence and weapons."

        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.return_value = mock_response
            result = TutoringService.chat(student_user, "Tell me something")

        assert result['success'] is True
        assert 'violence' not in result['reply'].lower()
        assert "focus on what we're learning" in result['reply'].lower()

    def test_chat_creates_session(self, student_user):
        """2026-02-17: Should create a tutoring session record."""
        mock_response = MagicMock()
        mock_response.text = "Hello!"

        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.return_value = mock_response
            result = TutoringService.chat(student_user, "Hi there!")

        session = TutoringSession.objects.get(id=result['session_id'])
        assert len(session.messages) == 2
        assert session.messages[0]['role'] == 'student'
        assert session.messages[1]['role'] == 'mentor'


# ── API Integration Tests ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestLessonListAPI:
    """2026-02-17: Tests for GET /api/v1/teaching/lessons/."""

    def test_list_lessons(self, student_client, published_lesson):
        """2026-02-17: Should return published lessons for student's class."""
        response = student_client.get('/api/v1/teaching/lessons/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['lessons']) == 1

    def test_list_lessons_subject_filter(self, student_client, published_lesson):
        """2026-02-17: Should filter by subject query param."""
        response = student_client.get('/api/v1/teaching/lessons/?subject=Math')
        assert response.status_code == 200
        assert len(response.json()['lessons']) == 0

    def test_parent_denied(self, parent_client, published_lesson):
        """2026-02-17: Parent should be denied access."""
        response = parent_client.get('/api/v1/teaching/lessons/')
        assert response.status_code == 403

    def test_unauthenticated_denied(self, published_lesson):
        """2026-02-17: Unauthenticated should be denied."""
        client = APIClient()
        response = client.get('/api/v1/teaching/lessons/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestStartDayAPI:
    """2026-02-17: Tests for POST /api/v1/teaching/lessons/{id}/start-day/."""

    def test_start_day(self, student_client, published_lesson):
        """2026-02-17: Should start day 1 via API."""
        response = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/start-day/',
            data={},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['day_number'] == 1
        assert 'content' in data

    def test_start_specific_day(self, student_client, published_lesson):
        """2026-02-17: Should allow starting specific day number."""
        response = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/start-day/',
            data={'day_number': 1},
            format='json',
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestCompleteDayAPI:
    """2026-02-17: Tests for POST /api/v1/teaching/lessons/{id}/complete-day/."""

    def test_complete_day(self, student_client, published_lesson):
        """2026-02-17: Should complete day via API."""
        # 2026-02-17: Start first
        student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/start-day/',
            data={}, format='json',
        )
        # 2026-02-17: Complete
        response = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/complete-day/',
            data={
                'day_number': 1,
                'practice_answers': {'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
                'time_spent': 120,
            },
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['questions_correct'] == 3


@pytest.mark.django_db
class TestAssessmentAPI:
    """2026-02-17: Tests for assessment endpoints."""

    def _complete_all_days_via_api(self, client):
        """2026-02-17: Helper to complete all 4 days via API."""
        answers_map = {
            1: {'D1_Q1': 0, 'D1_Q2': 1, 'D1_Q3': 1},
            2: {'D2_Q1': 1, 'D2_Q2': 1, 'D2_Q3': 1},
            3: {'D3_Q1': 1, 'D3_Q2': 1, 'D3_Q3': 1},
            4: {'D4_Q1': 1, 'D4_Q2': 1, 'D4_Q3': 0},
        }
        for day in range(1, 5):
            client.post(
                '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/start-day/',
                data={}, format='json',
            )
            client.post(
                '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/complete-day/',
                data={
                    'day_number': day,
                    'practice_answers': answers_map[day],
                    'time_spent': 120,
                },
                format='json',
            )

    def test_get_assessment(self, student_client, published_lesson):
        """2026-02-17: Should return assessment after completing all days."""
        self._complete_all_days_via_api(student_client)
        response = student_client.get(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/assessment/'
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['questions']) == 10

    def test_submit_assessment(self, student_client, published_lesson):
        """2026-02-17: Should submit assessment and return star rating."""
        self._complete_all_days_via_api(student_client)
        response = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/submit-assessment/',
            data={
                'answers': {
                    'WA_Q1': 1, 'WA_Q2': 2, 'WA_Q3': 1, 'WA_Q4': 2, 'WA_Q5': 1,
                    'WA_Q6': 2, 'WA_Q7': 1, 'WA_Q8': 1, 'WA_Q9': 1, 'WA_Q10': 2,
                },
                'time_spent': 300,
            },
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['star_rating'] == 3


@pytest.mark.django_db
class TestTutoringChatAPI:
    """2026-02-17: Tests for POST /api/v1/teaching/chat/."""

    def test_chat(self, student_client):
        """2026-02-17: Should send chat message and get response."""
        mock_response = MagicMock()
        mock_response.text = "Hello young learner!"

        with patch('services.teaching_engine.tutoring.get_llm_provider') as mock_llm:
            mock_llm.return_value.chat.return_value = mock_response
            response = student_client.post(
                '/api/v1/teaching/chat/',
                data={'message': 'Hello!'},
                format='json',
            )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'reply' in data

    def test_chat_validation(self, student_client):
        """2026-02-17: Should reject empty message."""
        response = student_client.post(
            '/api/v1/teaching/chat/',
            data={},
            format='json',
        )
        assert response.status_code == 400
