"""
2026-02-19: API integration tests for the Comprehension Capture Engine (BS-CMP).

Purpose:
    Test the 2 REST endpoints: SubmitExplanationView and BestEvaluationView.
    Covers authentication, authorization, input validation, and happy-path flows.
"""

import pytest  # 2026-02-19: Pytest framework
from datetime import date  # 2026-02-19: Date for DOB
from unittest.mock import patch  # 2026-02-19: Mocking

from django.contrib.auth import get_user_model  # 2026-02-19: User model
from rest_framework.test import APIClient  # 2026-02-19: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-19: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import (  # 2026-02-19: Teaching models
    TeachingLesson, StudentLessonProgress, DayProgress,
)
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-19: Cache
from services.comprehension_service.models import ComprehensionEvaluation  # 2026-02-19: Own model

User = get_user_model()  # 2026-02-19: Django User model

SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'  # 2026-02-19: Test content

# 2026-02-19: Patch targets
EVAL_PATCH = 'services.comprehension_service.services.evaluate_explanation'
CONTENT_PATCH = 'services.comprehension_service.services.TeachingContentLoader.get_day_content'

# 2026-02-19: Mock LLM scores
MOCK_SCORES = {
    'understanding': 80,
    'accuracy': 75,
    'own_words': 70,
    'depth': 65,
    'clarity': 70,
    'feedback': 'Well done!',
    'llm_error': False,
}


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-19: Create parent user for API tests."""
    user = User.objects.create_user(username='api_parent_cmp', password='testpass123')
    parent = Parent.objects.create(
        user=user,
        phone='+919876543211',
        full_name='API Parent CMP',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-19: Create student user for API tests."""
    user = User.objects.create_user(username='api_student_cmp', password='testpass123')
    student = Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='API Student CMP',
        dob=date(2019, 5, 15),
        age_group='6-12',
        grade=1,
        login_method='pin',
    )
    return student


@pytest.fixture
def student_client(student_user):
    """2026-02-19: Authenticated DRF client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-19: Authenticated DRF client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def published_lesson(db):
    """2026-02-19: Published teaching lesson for API tests."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_API_CMP_W01',
        title='The Wise Owl - API CMP Test',
        subject='English',
        class_number=1,
        chapter_id='MRIDANG_CH01',
        chapter_title='The Wise Owl',
        week_number=1,
        character_name='Ollie',
        learning_objectives=['Understand owls'],
        content_json_path=SAMPLE_CONTENT_PATH,
        status='published',
    )


@pytest.fixture
def lesson_progress(student_user, published_lesson, db):
    """2026-02-19: Lesson progress with day 1 in comprehension_check status."""
    return StudentLessonProgress.objects.create(
        student=student_user,
        lesson=published_lesson,
        iq_level='standard',
        current_day=1,
        day_statuses={'1': 'comprehension_check', '2': 'not_started',
                      '3': 'not_started', '4': 'not_started', '5': 'not_started'},
    )


@pytest.fixture
def day_progress(lesson_progress, db):
    """2026-02-19: DayProgress in comprehension_check status."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=1,
        status='comprehension_check',
        mastery_star_rating=4,
        mastery_passed=True,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    """2026-02-19: Clear content cache before/after each test."""
    TeachingContentLoader.clear_cache()
    yield
    TeachingContentLoader.clear_cache()


def explain_url(lesson_id, day_number=1):
    """2026-02-19: Build the submit-explanation URL."""
    return f'/api/v1/comprehension/lessons/{lesson_id}/day/{day_number}/explain/'


def best_url(lesson_id, day_number=1):
    """2026-02-19: Build the best-evaluation URL."""
    return f'/api/v1/comprehension/lessons/{lesson_id}/day/{day_number}/best/'


# ── Authentication / Authorization Tests ──────────────────────────────────

@pytest.mark.django_db
class TestSubmitAuthentication:
    """2026-02-19: Auth tests for SubmitExplanationView."""

    def test_submit_unauthenticated_401(self, published_lesson):
        """2026-02-19: Unauthenticated request returns 401."""
        client = APIClient()
        response = client.post(
            explain_url(published_lesson.id),
            {'student_text': 'Test', 'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 401  # 2026-02-19: Unauthorized

    def test_submit_parent_403(self, parent_client, published_lesson):
        """2026-02-19: Parent cannot submit (students only) — returns 403."""
        response = parent_client.post(
            explain_url(published_lesson.id),
            {'student_text': 'Owls are nocturnal hunters.', 'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 403  # 2026-02-19: Forbidden for parents


# ── Input Validation Tests ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitValidation:
    """2026-02-19: Input validation for SubmitExplanationView."""

    def test_submit_missing_student_text_400(self, student_client, published_lesson):
        """2026-02-19: Missing student_text returns 400."""
        response = student_client.post(
            explain_url(published_lesson.id),
            {'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Bad request

    def test_submit_empty_student_text_400(self, student_client, published_lesson):
        """2026-02-19: Empty student_text returns 400."""
        response = student_client.post(
            explain_url(published_lesson.id),
            {'student_text': '   ', 'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Bad request

    def test_submit_missing_practice_stars_400(self, student_client, published_lesson):
        """2026-02-19: Missing practice_stars returns 400."""
        response = student_client.post(
            explain_url(published_lesson.id),
            {'student_text': 'Owls are nocturnal hunters.'},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Bad request

    def test_submit_invalid_day_400(self, student_client, published_lesson):
        """2026-02-19: Day number outside 1-4 returns 400."""
        response = student_client.post(
            explain_url(published_lesson.id, day_number=5),
            {'student_text': 'Owls hunt mice.', 'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Invalid day

    def test_submit_invalid_lesson_404(self, student_client):
        """2026-02-19: Non-existent lesson UUID returns 404."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = student_client.post(
            explain_url(fake_id),
            {'student_text': 'Owls hunt mice at night.', 'practice_stars': 3},
            format='json',
        )
        assert response.status_code == 404  # 2026-02-19: Not found


# ── Happy-Path Tests ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitHappyPath:
    """2026-02-19: Happy-path tests for SubmitExplanationView."""

    @patch(EVAL_PATCH, return_value=dict(MOCK_SCORES))
    def test_submit_student_200(
        self, mock_eval, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-19: Valid student submission returns 200 with result."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short lesson.'},
        }):
            response = student_client.post(
                explain_url(published_lesson.id),
                {
                    'student_text': 'Owls can see at night because they have large round eyes.',
                    'practice_stars': 4,
                },
                format='json',
            )

        assert response.status_code == 200  # 2026-02-19: OK
        data = response.json()
        assert data['is_parroting'] is False  # 2026-02-19: Not parroting
        assert 'weighted_star_rating' in data  # 2026-02-19: Has rating
        assert 'comprehension_score' in data  # 2026-02-19: Has score
        assert 'scores' in data  # 2026-02-19: Has dimension scores
        assert 'feedback' in data  # 2026-02-19: Has feedback

    def test_submit_parroting_200_with_flag(
        self, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-19: Parroting detection returns 200 with is_parroting=True."""
        # 2026-02-19: Build a very noun-heavy lesson summary and near-copy student text
        lesson_summary = (
            'Owls forests branches animals wisdom nocturnal predators talons feathers '
            'hunting watching listening darkness silent creatures exceptional eyesight.'
        )
        student_text = (
            'Owls forests branches animals wisdom nocturnal predators talons feathers '
            'hunting watching listening darkness.'
        )

        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1',
            'teaching_content': {'concept_text': lesson_summary},
        }):
            response = student_client.post(
                explain_url(published_lesson.id),
                {'student_text': student_text, 'practice_stars': 4},
                format='json',
            )

        assert response.status_code == 200  # 2026-02-19: OK (not 4xx)
        data = response.json()
        assert data['is_parroting'] is True  # 2026-02-19: Parroting flagged
        assert 'message' in data  # 2026-02-19: Nudge message present

    @patch(EVAL_PATCH, return_value=dict(MOCK_SCORES))
    def test_submit_creates_db_record(
        self, mock_eval, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-19: Successful submission creates a ComprehensionEvaluation record."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            student_client.post(
                explain_url(published_lesson.id),
                {
                    'student_text': 'Owls are birds that hunt animals at night using darkness.',
                    'practice_stars': 3,
                },
                format='json',
            )

        assert ComprehensionEvaluation.objects.count() == 1  # 2026-02-19: Record created

    @patch(EVAL_PATCH, return_value=dict(MOCK_SCORES))
    def test_submit_updates_dayprogress(
        self, mock_eval, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-19: Submission updates DayProgress status to day_complete."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            student_client.post(
                explain_url(published_lesson.id),
                {
                    'student_text': 'Owls hunt mice silently under cover of darkness every night.',
                    'practice_stars': 4,
                },
                format='json',
            )

        day_progress.refresh_from_db()
        assert day_progress.status == 'day_complete'  # 2026-02-19: Status updated

    @patch(EVAL_PATCH, return_value=dict(MOCK_SCORES))
    def test_submit_repeat_attempt_increments_number(
        self, mock_eval, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-19: Second API submission has attempt_number=2."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            r1 = student_client.post(
                explain_url(published_lesson.id),
                {'student_text': 'Owls hunt mice at night silently.', 'practice_stars': 4},
                format='json',
            )
            r2 = student_client.post(
                explain_url(published_lesson.id),
                {'student_text': 'Owls navigate darkness using unique vision biology.', 'practice_stars': 4},
                format='json',
            )

        assert r1.json()['attempt_number'] == 1  # 2026-02-19: First
        assert r2.json()['attempt_number'] == 2  # 2026-02-19: Second


# ── Best Evaluation Tests ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestBestEvaluationAPI:
    """2026-02-19: Tests for the BestEvaluationView."""

    def test_best_unauthenticated_401(self, published_lesson):
        """2026-02-19: Unauthenticated request returns 401."""
        client = APIClient()
        response = client.get(best_url(published_lesson.id))
        assert response.status_code == 401  # 2026-02-19: Unauthorized

    def test_best_no_eval_returns_empty(self, student_client, published_lesson):
        """2026-02-19: No evaluations → returns empty dict with 200."""
        response = student_client.get(best_url(published_lesson.id))
        assert response.status_code == 200  # 2026-02-19: OK
        assert response.json() == {}  # 2026-02-19: Empty

    def test_best_returns_highest_rating(
        self, student_client, student_user, published_lesson
    ):
        """2026-02-19: GET returns the evaluation with the highest star rating."""
        # 2026-02-19: Create two evaluations directly
        ComprehensionEvaluation.objects.create(
            student=student_user,
            lesson=published_lesson,
            day_number=1,
            student_text='First attempt',
            weighted_star_rating=2,
            attempt_number=1,
        )
        ComprehensionEvaluation.objects.create(
            student=student_user,
            lesson=published_lesson,
            day_number=1,
            student_text='Better attempt',
            weighted_star_rating=5,
            attempt_number=2,
        )

        response = student_client.get(best_url(published_lesson.id))
        assert response.status_code == 200  # 2026-02-19: OK
        data = response.json()
        assert data['weighted_star_rating'] == 5  # 2026-02-19: Highest rating


# ── Marks-Based Comprehension Question API Tests (BS-CMP v2) ──────────────

# 2026-02-21: Sample comprehension questions for API tests
SAMPLE_CQ_API = [
    {
        'id': 'D1_CQ1',
        'marks': 2,
        'question': 'Explain what science is in your own words.',
        'key_points': [
            'Science is a systematic way of studying the natural world',
            'Science uses observation and evidence rather than guessing',
        ],
        'model_answer': 'Science systematically studies the world using evidence.',
    },
]

# 2026-02-21: Patch targets for new API tests
API_CONTENT_PATCH = 'services.comprehension_service.services.TeachingContentLoader.get_day_content'
API_KP_EVAL_PATCH = 'services.comprehension_service.services.evaluate_key_points'


def questions_url(lesson_id, day_number=1):
    """2026-02-21: Build the day questions URL."""
    return f'/api/v1/comprehension/lessons/{lesson_id}/day/{day_number}/questions/'


def answer_url(lesson_id, question_id, day_number=1):
    """2026-02-21: Build the question answer URL."""
    return f'/api/v1/comprehension/lessons/{lesson_id}/day/{day_number}/questions/{question_id}/answer/'


@pytest.mark.django_db
class TestDayQuestionsAPI:
    """2026-02-21: Tests for DayQuestionsView."""

    def test_get_questions_200_student(
        self, student_client, published_lesson
    ):
        """2026-02-21: Authenticated student gets 200 with question list."""
        mock_content = {
            'title': 'Day 1',
            'teaching_content': {'concept_text': 'Short.'},
            'comprehension_questions': SAMPLE_CQ_API,
        }
        with patch(API_CONTENT_PATCH, return_value=mock_content):
            response = student_client.get(questions_url(published_lesson.id))

        assert response.status_code == 200  # 2026-02-21: OK
        data = response.json()
        assert isinstance(data, list)  # 2026-02-21: Returns list
        assert len(data) == 1  # 2026-02-21: One question
        # 2026-02-21: key_points must NOT be in response (prevent gaming)
        assert 'key_points' not in data[0]
        assert data[0]['id'] == 'D1_CQ1'

    def test_get_questions_unauthenticated_401(self, published_lesson):
        """2026-02-21: Unauthenticated request returns 401."""
        client = APIClient()
        response = client.get(questions_url(published_lesson.id))
        assert response.status_code == 401  # 2026-02-21: Unauthorized

    def test_get_questions_parent_403(self, parent_client, published_lesson):
        """2026-02-21: Parent cannot access student endpoint — returns 403."""
        response = parent_client.get(questions_url(published_lesson.id))
        assert response.status_code == 403  # 2026-02-21: Forbidden for parents


@pytest.mark.django_db
class TestSubmitQuestionAnswerAPI:
    """2026-02-21: Tests for SubmitQuestionAnswerView."""

    def _mock_content(self):
        """2026-02-21: Return mock day content dict with comprehension_questions."""
        return {
            'title': 'Day 1',
            'teaching_content': {'concept_text': 'Short.'},
            'comprehension_questions': SAMPLE_CQ_API,
        }

    def test_submit_answer_200_typed(
        self, student_client, published_lesson, lesson_progress, day_progress
    ):
        """2026-02-21: Valid typed submission returns 200 with evaluation result."""
        eval_result = {'covered': [True, True], 'feedback': 'Great!', 'llm_error': False}
        with patch(API_CONTENT_PATCH, return_value=self._mock_content()):
            with patch(API_KP_EVAL_PATCH, return_value=eval_result):
                response = student_client.post(
                    answer_url(published_lesson.id, 'D1_CQ1'),
                    {'student_text': 'Science studies the world systematically.', 'input_method': 'typed'},
                    format='json',
                )

        assert response.status_code == 200  # 2026-02-21: OK
        data = response.json()
        assert 'marks_awarded' in data  # 2026-02-21: Has marks_awarded
        assert 'marks_available' in data  # 2026-02-21: Has marks_available
        assert 'key_points_covered' in data  # 2026-02-21: Has coverage list
        assert 'key_points_text' in data  # 2026-02-21: Has key points revealed
        assert 'feedback' in data  # 2026-02-21: Has feedback

    def test_submit_answer_missing_student_text_400(
        self, student_client, published_lesson
    ):
        """2026-02-21: Missing student_text returns 400."""
        response = student_client.post(
            answer_url(published_lesson.id, 'D1_CQ1'),
            {'input_method': 'typed'},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-21: Bad request

    def test_submit_answer_missing_input_method_400(
        self, student_client, published_lesson
    ):
        """2026-02-21: Missing/invalid input_method returns 400."""
        response = student_client.post(
            answer_url(published_lesson.id, 'D1_CQ1'),
            {'student_text': 'Some answer text here.'},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-21: Bad request

    def test_submit_answer_invalid_lesson_404(self, student_client):
        """2026-02-21: Non-existent lesson UUID returns 404."""
        import uuid as uuid_mod
        fake_id = str(uuid_mod.uuid4())
        response = student_client.post(
            answer_url(fake_id, 'D1_CQ1'),
            {'student_text': 'Some answer.', 'input_method': 'typed'},
            format='json',
        )
        assert response.status_code == 404  # 2026-02-21: Not found

    def test_submit_answer_invalid_question_id_404(
        self, student_client, published_lesson
    ):
        """2026-02-21: Non-existent question ID returns 404."""
        with patch(API_CONTENT_PATCH, return_value=self._mock_content()):
            response = student_client.post(
                answer_url(published_lesson.id, 'D1_NONEXISTENT'),
                {'student_text': 'Some answer.', 'input_method': 'typed'},
                format='json',
            )
        assert response.status_code == 404  # 2026-02-21: Not found
