"""
2026-03-02: API integration tests for Math Service (BS-MTH module).

Purpose:
    Verify all 7 API endpoints via DRF test client with JWT auth:
    - GET  /api/v1/math/lessons/
    - GET  /api/v1/math/lessons/{lesson_id}/
    - POST /api/v1/math/sessions/
    - GET  /api/v1/math/sessions/{session_id}/
    - POST /api/v1/math/sessions/{session_id}/answer/
    - POST /api/v1/math/sessions/{session_id}/hint/
    - GET  /api/v1/math/progress/

Covers: 200/201, 400, 401, 403, 404 status codes.

~15 API tests.
"""

import json  # 2026-03-02: JSON
import pytest  # 2026-03-02: Pytest
from datetime import date  # 2026-03-02: DOB
from unittest.mock import patch  # 2026-03-02: Mocking

from django.contrib.auth import get_user_model  # 2026-03-02: User model

from rest_framework.test import APIClient  # 2026-03-02: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-03-02: JWT

from services.auth_service.models import Parent, Student  # 2026-03-02: Auth
from services.math_service.models import MathLesson  # 2026-03-02: Math models
from services.math_service.content_loader import MathContentLoader  # 2026-03-02: Loader

User = get_user_model()  # 2026-03-02: Django User

BASE_URL = '/api/v1/math/'  # 2026-03-02: URL prefix


# ── Sample content ─────────────────────────────────────────────────────────

SAMPLE_LESSON = {
    "lesson_id": "MATH1_W01",
    "class": 1,
    "subject": "Math",
    "topic": "Counting 1-10",
    "week_number": 1,
    "character": "Bunny",
    "learning_objectives": ["Count 1-10"],
    "days": [
        {
            "day": 1,
            "title": "Numbers 1-5",
            "teaching_summary": "Count objects.",
            "worked_examples": [],
            "problems": {
                "easy": [
                    {
                        "id": "MATH1_W01_D1_E1",
                        "type": "mcq",
                        "question": "How many apples? 🍎🍎🍎",
                        "options": ["2", "3", "4", "5"],
                        "correct_answer": 1,
                        "worked_solution": {
                            "steps": ["Count: 1,2,3"],
                            "answer": "3",
                            "explanation": "3 apples.",
                        },
                        "hint": "Count one by one.",
                    }
                ],
                "medium": [
                    {
                        "id": "MATH1_W01_D1_M1",
                        "type": "numeric_fill",
                        "question": "2 + __ = 5",
                        "correct_answer": 3,
                        "worked_solution": {
                            "steps": ["2 + 3 = 5"],
                            "answer": "3",
                            "explanation": "2 + 3 = 5.",
                        },
                        "hint": "Start at 2.",
                    }
                ],
                "hard": [],
            },
        }
    ],
}


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-03-02: Parent user."""
    user = User.objects.create_user(username='api_math_parent', password='pass123')
    return Parent.objects.create(
        user=user,
        phone='+919100000099',
        full_name='API Math Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Grade 1 student."""
    user = User.objects.create_user(username='api_math_student', password='pass123')
    return Student.objects.create(
        parent=parent_user, user=user,
        full_name='API Math Student',
        dob=date(2017, 6, 15),
        age_group='6-12', grade=1,
        login_method='pin',
    )


@pytest.fixture
def student_client(student):
    """2026-03-02: Authenticated DRF client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-03-02: Authenticated DRF client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def math_lesson(db):
    """2026-03-02: Published math lesson."""
    return MathLesson.objects.create(
        lesson_id='MATH1_W01',
        title='Counting 1-10',
        class_number=1,
        week_number=1,
        topic='Counting',
        content_json_path='json/math/class1/week1.json',
        status='published',
    )


@pytest.fixture
def mock_content(math_lesson):
    """2026-03-02: Patch MathContentLoader to return SAMPLE_LESSON always."""
    with patch.object(MathContentLoader, 'load_lesson', return_value=SAMPLE_LESSON):
        with patch.object(MathContentLoader, '_file_hash', return_value='testhash'):
            yield


# ── Auth guard tests ───────────────────────────────────────────────────────

class TestAuthGuards:
    """2026-03-02: Tests that endpoints require authentication."""

    def test_lessons_unauthenticated(self):
        """2026-03-02: 401 when not logged in."""
        client = APIClient()
        response = client.get(f'{BASE_URL}lessons/')
        assert response.status_code == 401

    def test_sessions_unauthenticated(self):
        """2026-03-02: 401 when not logged in for sessions."""
        client = APIClient()
        response = client.post(f'{BASE_URL}sessions/', {})
        assert response.status_code == 401

    def test_lessons_parent_forbidden(self, parent_client):
        """2026-03-02: 403 when parent tries to access math lessons."""
        response = parent_client.get(f'{BASE_URL}lessons/')
        assert response.status_code == 403


# ── Lesson endpoints ───────────────────────────────────────────────────────

class TestLessonEndpoints:
    """2026-03-02: Tests for lesson list and detail endpoints."""

    def test_list_lessons_returns_published(self, student_client, math_lesson):
        """2026-03-02: GET /lessons/ returns published lessons for student's grade."""
        response = student_client.get(f'{BASE_URL}lessons/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert any(l['lesson_id'] == 'MATH1_W01' for l in data['lessons'])

    def test_list_lessons_empty_for_other_grade(self, student_client, db):
        """2026-03-02: GET /lessons/ returns empty for grade with no lessons."""
        # 2026-03-02: Student is grade 1; create lesson for grade 2 only
        MathLesson.objects.create(
            lesson_id='MATH2_W01', title='Grade2', class_number=2,
            week_number=1, topic='x', content_json_path='x', status='published',
        )
        response = student_client.get(f'{BASE_URL}lessons/')
        data = response.json()
        assert data['success'] is True
        ids = [l['lesson_id'] for l in data['lessons']]
        assert 'MATH2_W01' not in ids

    def test_lesson_detail_found(self, student_client, math_lesson, mock_content):
        """2026-03-02: GET /lessons/{id}/ returns lesson detail."""
        response = student_client.get(f'{BASE_URL}lessons/MATH1_W01/')
        assert response.status_code == 200
        data = response.json()
        assert data['lesson_id'] == 'MATH1_W01'
        assert 'days' in data

    def test_lesson_detail_not_found(self, student_client):
        """2026-03-02: GET /lessons/{id}/ returns 404 for unknown lesson."""
        response = student_client.get(f'{BASE_URL}lessons/NONEXISTENT/')
        assert response.status_code == 404


# ── Session endpoints ──────────────────────────────────────────────────────

class TestSessionEndpoints:
    """2026-03-02: Tests for session start and status endpoints."""

    def test_start_session_creates_session(self, student_client, math_lesson, mock_content):
        """2026-03-02: POST /sessions/ creates session and returns problems."""
        response = student_client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'MATH1_W01',
            'day_number': 1,
        }, format='json')
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert 'session_id' in data
        assert 'problems' in data
        assert len(data['problems']) >= 1

    def test_start_session_invalid_lesson(self, student_client, db):
        """2026-03-02: POST /sessions/ returns 400 for unknown lesson."""
        response = student_client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'NONEXISTENT',
            'day_number': 1,
        }, format='json')
        assert response.status_code == 400

    def test_start_session_invalid_day(self, student_client, math_lesson, mock_content):
        """2026-03-02: POST /sessions/ returns 400 for day out of range."""
        response = student_client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'MATH1_W01',
            'day_number': 10,  # 2026-03-02: Invalid day (serializer max=4)
        }, format='json')
        assert response.status_code == 400

    def test_get_session_status(self, student_client, math_lesson, mock_content):
        """2026-03-02: GET /sessions/{id}/ returns session status."""
        start = student_client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'MATH1_W01',
            'day_number': 1,
        }, format='json')
        session_id = start.json()['session_id']

        response = student_client.get(f'{BASE_URL}sessions/{session_id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'active'
        assert data['session_id'] == session_id


# ── Answer & hint endpoints ────────────────────────────────────────────────

class TestAnswerAndHintEndpoints:
    """2026-03-02: Tests for answer submission and hint endpoints."""

    def _create_session(self, client, mock_content):
        """2026-03-02: Helper to create a session."""
        response = client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'MATH1_W01',
            'day_number': 1,
        }, format='json')
        return response.json()

    def test_submit_correct_answer(self, student_client, math_lesson, mock_content):
        """2026-03-02: POST /sessions/{id}/answer/ correct answer returns is_correct=True.

        Student IQ defaults to 'standard' → medium tier → MATH1_W01_D1_M1
        (numeric_fill, correct_answer=3). We submit '3'.
        """
        session_data = self._create_session(student_client, mock_content)
        session_id = session_data['session_id']
        problem_id = session_data['problems'][0]['id']

        # 2026-03-02: Standard IQ → medium problems → numeric_fill correct_answer=3
        response = student_client.post(
            f'{BASE_URL}sessions/{session_id}/answer/',
            {'problem_id': problem_id, 'answer': '3'},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['is_correct'] is True
        assert 'feedback' in data
        assert 'worked_steps' in data

    def test_submit_wrong_answer(self, student_client, math_lesson, mock_content):
        """2026-03-02: POST /sessions/{id}/answer/ wrong answer returns is_correct=False."""
        session_data = self._create_session(student_client, mock_content)
        session_id = session_data['session_id']
        problem_id = session_data['problems'][0]['id']

        response = student_client.post(
            f'{BASE_URL}sessions/{session_id}/answer/',
            {'problem_id': problem_id, 'answer': '99'},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['is_correct'] is False

    def test_submit_answer_session_completion(self, student_client, math_lesson, mock_content):
        """2026-03-02: Answering all problems sets session_complete=True and star_rating."""
        session_data = self._create_session(student_client, mock_content)
        session_id = session_data['session_id']
        problems = session_data['problems']

        # 2026-03-02: Answer every problem
        last_response = None
        for p in problems:
            last_response = student_client.post(
                f'{BASE_URL}sessions/{session_id}/answer/',
                {'problem_id': p['id'], 'answer': '1'},
                format='json',
            )

        data = last_response.json()
        assert data['session_complete'] is True
        assert data['star_rating'] is not None
        assert 1 <= data['star_rating'] <= 5

    def test_request_hint_returns_text(self, student_client, math_lesson, mock_content):
        """2026-03-02: POST /sessions/{id}/hint/ returns hint text."""
        session_data = self._create_session(student_client, mock_content)
        session_id = session_data['session_id']
        problem_id = session_data['problems'][0]['id']

        response = student_client.post(
            f'{BASE_URL}sessions/{session_id}/hint/',
            {'problem_id': problem_id},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['hint_text']) > 0
        assert data['hint_number'] == 1

    def test_request_hint_unknown_session(self, student_client, db):
        """2026-03-02: POST /hint/ for unknown session returns 400."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = student_client.post(
            f'{BASE_URL}sessions/{fake_id}/hint/',
            {'problem_id': 'ANY'},
            format='json',
        )
        assert response.status_code == 400


# ── Progress endpoint ──────────────────────────────────────────────────────

class TestProgressEndpoint:
    """2026-03-02: Tests for the math progress endpoint."""

    def test_get_progress_empty(self, student_client, db):
        """2026-03-02: GET /progress/ returns zeros for fresh student."""
        response = student_client.get(f'{BASE_URL}progress/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['total_sessions'] == 0
        assert data['total_stars'] == 0


# ── Drill endpoints (AMT-APE-005) ──────────────────────────────────────────

class TestDrillEndpoints:
    """2026-03-03: API integration tests for Mental Maths Drill endpoints (AMT-APE-005)."""

    # 2026-03-03: Helper to start a drill via the API
    def _start_drill(self, client, drill_type='tables', range_min=1, range_max=5,
                     time_limit=30, total_questions=5):
        """2026-03-03: Helper to POST /drills/ and return response data."""
        response = client.post(f'{BASE_URL}drills/', {
            'drill_type': drill_type,
            'number_range_min': range_min,
            'number_range_max': range_max,
            'time_limit_seconds': time_limit,
            'total_questions': total_questions,
        }, format='json')
        return response

    def test_start_drill_unauthenticated_401(self):
        """2026-03-03: POST /drills/ returns 401 when not logged in."""
        client = APIClient()
        response = client.post(f'{BASE_URL}drills/', {
            'drill_type': 'tables',
            'number_range_min': 1,
            'number_range_max': 5,
            'time_limit_seconds': 30,
            'total_questions': 5,
        }, format='json')
        assert response.status_code == 401

    def test_start_drill_as_parent_403(self, parent_client):
        """2026-03-03: POST /drills/ returns 403 for parent user."""
        response = self._start_drill(parent_client)
        assert response.status_code == 403

    def test_start_drill_tables_201(self, student_client):
        """2026-03-03: POST /drills/ creates a tables drill session (201)."""
        response = self._start_drill(student_client, 'tables', 1, 5, 30, 5)
        assert response.status_code == 201
        data = response.json()
        assert data['success'] is True
        assert data['drill_type'] == 'tables'
        assert 'session_id' in data
        assert len(data['questions']) == 5
        assert data['time_limit_seconds'] == 30
        # 2026-03-03: Correct answer must NOT be exposed to client
        for q in data['questions']:
            assert 'correct_answer' not in q

    def test_start_drill_squares_201(self, student_client):
        """2026-03-03: POST /drills/ creates a squares drill session (201)."""
        response = self._start_drill(student_client, 'squares', 2, 8, 60, 5)
        assert response.status_code == 201
        data = response.json()
        assert data['drill_type'] == 'squares'

    def test_start_drill_cubes_201(self, student_client):
        """2026-03-03: POST /drills/ creates a cubes drill session (201)."""
        response = self._start_drill(student_client, 'cubes', 1, 5, 120, 5)
        assert response.status_code == 201
        data = response.json()
        assert data['drill_type'] == 'cubes'

    def test_start_drill_invalid_type_400(self, student_client):
        """2026-03-03: POST /drills/ with invalid drill_type returns 400."""
        response = student_client.post(f'{BASE_URL}drills/', {
            'drill_type': 'divisions',
            'number_range_min': 1,
            'number_range_max': 5,
            'time_limit_seconds': 30,
            'total_questions': 5,
        }, format='json')
        assert response.status_code == 400

    def test_get_drill_status_200(self, student_client):
        """2026-03-03: GET /drills/{id}/ returns session status (200)."""
        start_data = self._start_drill(student_client).json()
        session_id = start_data['session_id']

        response = student_client.get(f'{BASE_URL}drills/{session_id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['session_id'] == session_id
        assert data['status'] == 'active'
        assert data['answered_count'] == 0
        assert len(data['questions_with_answers']) == 5

    def test_submit_drill_answer_correct(self, student_client):
        """2026-03-03: POST /drills/{id}/answer/ correct answer returns is_correct=True."""
        from services.math_service.models import MathDrillSession
        start_data = self._start_drill(student_client, 'squares', 3, 3, 30, 5).json()
        session_id = start_data['session_id']

        # 2026-03-03: 3² = 9; fetch from DB to get correct answer
        session = MathDrillSession.objects.get(id=session_id)
        correct = session.questions[0]['correct_answer']

        response = student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
            'question_index': 0,
            'answer': str(correct),
        }, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['is_correct'] is True
        assert data['score'] == 1

    def test_submit_drill_answer_wrong(self, student_client):
        """2026-03-03: POST /drills/{id}/answer/ wrong answer returns is_correct=False."""
        start_data = self._start_drill(student_client, 'cubes', 2, 4, 30, 5).json()
        session_id = start_data['session_id']

        response = student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
            'question_index': 0,
            'answer': '9999',
        }, format='json')
        assert response.status_code == 200
        data = response.json()
        assert data['is_correct'] is False
        assert data['score'] == 0

    def test_invalid_question_index_returns_400(self, student_client):
        """2026-03-03: POST /drills/{id}/answer/ with out-of-range index returns 400."""
        start_data = self._start_drill(student_client).json()
        session_id = start_data['session_id']

        response = student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
            'question_index': 999,
            'answer': '42',
        }, format='json')
        assert response.status_code == 400

    def test_complete_drill_post_200(self, student_client):
        """2026-03-03: POST /drills/{id}/complete/ finalises session with status='expired'."""
        start_data = self._start_drill(student_client).json()
        session_id = start_data['session_id']

        response = student_client.post(f'{BASE_URL}drills/{session_id}/complete/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['status'] == 'expired'
        assert data['score'] == 0  # 2026-03-03: No answers submitted

    def test_complete_drill_already_completed_200(self, student_client):
        """2026-03-03: POST /drills/{id}/complete/ is idempotent — second call is still 200."""
        start_data = self._start_drill(student_client).json()
        session_id = start_data['session_id']

        student_client.post(f'{BASE_URL}drills/{session_id}/complete/')
        response = student_client.post(f'{BASE_URL}drills/{session_id}/complete/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True

    def test_drill_history_empty(self, student_client, db):
        """2026-03-03: GET /drills/history/ returns empty list for fresh student."""
        response = student_client.get(f'{BASE_URL}drills/history/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['sessions'] == []

    def test_drill_history_after_completion(self, student_client):
        """2026-03-03: GET /drills/history/ returns completed drill in history."""
        start_data = self._start_drill(student_client, 'squares', 2, 8, 30, 5).json()  # 2026-03-03: min 5 questions
        session_id = start_data['session_id']
        student_client.post(f'{BASE_URL}drills/{session_id}/complete/')

        response = student_client.get(f'{BASE_URL}drills/history/')
        assert response.status_code == 200
        data = response.json()
        assert len(data['sessions']) == 1
        assert data['sessions'][0]['drill_type'] == 'squares'
        assert data['sessions'][0]['status'] in ('completed', 'expired')

    def test_full_drill_flow_tables(self, student_client):
        """2026-03-03: Full tables drill: start → answer all → results include star_rating."""
        from services.math_service.models import MathDrillSession
        start_data = self._start_drill(student_client, 'tables', 1, 5, 30, 5).json()  # 2026-03-03: min 5 questions
        session_id = start_data['session_id']
        session = MathDrillSession.objects.get(id=session_id)

        # 2026-03-03: Answer all questions correctly
        for idx, q in enumerate(session.questions):
            student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
                'question_index': idx,
                'answer': str(q['correct_answer']),
            }, format='json')

        status_resp = student_client.get(f'{BASE_URL}drills/{session_id}/')
        data = status_resp.json()
        assert data['status'] == 'completed'
        assert data['score'] == 5  # 2026-03-03: All 5 correct
        assert data['star_rating'] is not None

    def test_full_drill_flow_squares(self, student_client):
        """2026-03-03: Full squares drill: start → answer some wrong → verify score."""
        from services.math_service.models import MathDrillSession
        start_data = self._start_drill(student_client, 'squares', 2, 6, 60, 5).json()
        session_id = start_data['session_id']
        session = MathDrillSession.objects.get(id=session_id)

        # 2026-03-03: Answer Q0 correctly, rest wrong
        student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
            'question_index': 0,
            'answer': str(session.questions[0]['correct_answer']),
        }, format='json')
        for idx in range(1, 5):
            student_client.post(f'{BASE_URL}drills/{session_id}/answer/', {
                'question_index': idx,
                'answer': '0',
            }, format='json')

        status_resp = student_client.get(f'{BASE_URL}drills/{session_id}/')
        data = status_resp.json()
        assert data['status'] == 'completed'
        assert data['score'] == 1

    def test_full_drill_flow_cubes(self, student_client):
        """2026-03-03: Full cubes drill: start → timer expiry via complete/ → status='expired'."""
        start_data = self._start_drill(student_client, 'cubes', 1, 6, 30, 5).json()  # 2026-03-03: min 5 questions
        session_id = start_data['session_id']

        # 2026-03-03: Simulate timer expiry without answering all questions
        complete_resp = student_client.post(f'{BASE_URL}drills/{session_id}/complete/')
        assert complete_resp.status_code == 200
        assert complete_resp.json()['status'] == 'expired'

        status_resp = student_client.get(f'{BASE_URL}drills/{session_id}/')
        assert status_resp.json()['status'] == 'expired'
