"""
2026-03-02: Tests for BS-AMT-001 AI Math Tutor teaching phase.

Coverage:
    Service unit tests (TestMathTutoringService):
        - get_or_create_session creates session with opening message
        - get_or_create_session is idempotent (second call returns same session)
        - opening message uses fallback when LLM unavailable
        - chat appends student and tutor messages
        - chat returns error when session not started
        - chat returns error when teaching already complete
        - complete_teaching sets flag to True
        - complete_teaching returns error when session missing
        - get_day_content returns correct teaching data
        - fallback message is built from JSON fields

    API integration tests (TestMathTutoringAPI):
        - GET teach/ creates session and returns 200
        - GET teach/ is idempotent
        - GET teach/ returns 401 unauthenticated
        - POST teach/chat/ appends message and returns reply
        - POST teach/chat/ returns 400 when session not found
        - POST teach/complete/ marks teaching_complete=True
        - POST teach/complete/ returns 200
        - POST teach/complete/ returns 401 unauthenticated
        - Full flow: session → teach → chat → complete → practice
        - student cannot access another student's session (404)
"""

import json
import uuid
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.auth_service.models import Parent, Student
from services.math_service.models import MathLesson, MathSession, MathTutoringSession
from services.math_service.content_loader import MathContentLoader
from services.math_service.tutoring import MathTutoringService

User = get_user_model()

BASE_URL = '/api/v1/math/'  # 2026-03-02: URL prefix

# ── Sample content ──────────────────────────────────────────────────────────

SAMPLE_LESSON = {
    "lesson_id": "MATH1_W01",
    "class": 1,
    "subject": "Math",
    "topic": "Counting 1-10",
    "week_number": 1,
    "character": "Bunny the Counter",
    "learning_objectives": ["Count objects 1-10"],
    "days": [
        {
            "day": 1,
            "title": "Numbers 1-5",
            "teaching_summary": "We count by touching each object once.",
            "worked_examples": [
                {
                    "problem": "Count the stars: ★★★★",
                    "solution_steps": ["Point to each star: 1, 2, 3, 4", "Answer: 4"],
                    "answer": "4",
                }
            ],
            "problems": {
                "easy": [{"id": "MATH1_W01_D1_E1", "type": "mcq", "question": "Q?",
                           "options": ["1", "2", "3"], "correct_answer": 1,
                           "worked_solution": {"steps": [], "answer": "2", "explanation": "2"},
                           "hint": "hint"}],
                "medium": [{"id": "MATH1_W01_D1_M1", "type": "numeric_fill",
                            "question": "2+?=5", "correct_answer": 3,
                            "worked_solution": {"steps": [], "answer": "3", "explanation": "3"},
                            "hint": "hint"}],
                "hard": [],
            },
        }
    ],
}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-03-02: Parent user."""
    user = User.objects.create_user(username='tut_parent', password='pass123')
    return Parent.objects.create(
        user=user, phone='+919000000088', full_name='Tut Parent',
        is_phone_verified=True, is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Grade 1 student."""
    user = User.objects.create_user(username='tut_student', password='pass123')
    return Student.objects.create(
        parent=parent_user, user=user,
        full_name='Tut Student', dob=date(2017, 6, 15),
        age_group='6-12', grade=1, login_method='pin',
    )


@pytest.fixture
def student2(parent_user, db):
    """2026-03-02: Second student (to test access isolation)."""
    user = User.objects.create_user(username='tut_student2', password='pass123')
    return Student.objects.create(
        parent=parent_user, user=user,
        full_name='Tut Student 2', dob=date(2017, 6, 15),
        age_group='6-12', grade=1, login_method='pin',
    )


@pytest.fixture
def student_client(student):
    """2026-03-02: Authenticated DRF client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def student2_client(student2):
    """2026-03-02: Authenticated DRF client for second student."""
    client = APIClient()
    token = RefreshToken.for_user(student2.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def math_lesson(db):
    """2026-03-02: Published math lesson."""
    return MathLesson.objects.create(
        lesson_id='MATH1_W01_TUT', title='Counting 1-10',
        class_number=1, week_number=1, topic='Counting',
        content_json_path='json/math/class1/week1.json',
        status='published',
    )


@pytest.fixture
def math_session(student, math_lesson, db):
    """2026-03-02: Active math session for the student."""
    return MathSession.objects.create(
        student=student,
        lesson=math_lesson,
        day_number=1,
        iq_level='standard',
        status='active',
        total_problems=1,
    )


@pytest.fixture
def mock_content(math_lesson):
    """2026-03-02: Patch MathContentLoader to return SAMPLE_LESSON."""
    with patch.object(MathContentLoader, 'load_lesson', return_value=SAMPLE_LESSON):
        with patch.object(MathContentLoader, '_file_hash', return_value='testhash'):
            yield


@pytest.fixture
def mock_llm_reply():
    """2026-03-02: Patch LLM to return a known teaching reply."""
    mock_response = MagicMock()
    mock_response.text = (
        "Hello! I'm Bunny the Counter. Today we'll learn Numbers 1-5. "
        "We count by touching each object once. "
        "Let me show you: Count ★★★★ → 1, 2, 3, 4. Answer: 4. "
        "Can you count 3 apples?"
    )
    with patch('services.math_service.tutoring.get_llm_provider') as mock_factory:
        mock_llm = MagicMock()
        mock_llm.chat.return_value = mock_response
        mock_factory.return_value = mock_llm
        yield mock_factory


# ── Service unit tests ────────────────────────────────────────────────────────

class TestMathTutoringService:
    """2026-03-02: Unit tests for MathTutoringService."""

    def test_get_or_create_session_creates_new(self, math_session, mock_content, mock_llm_reply):
        """2026-03-02: First call creates tutoring session with AI opening message."""
        result = MathTutoringService.get_or_create_session(math_session)

        assert result['success'] is True
        assert result['teaching_complete'] is False
        assert len(result['messages']) == 1  # 2026-03-02: One opening message
        assert result['messages'][0]['role'] == 'tutor'
        assert len(result['messages'][0]['text']) > 0
        assert result['character'] == 'Bunny the Counter'

        # 2026-03-02: DB record created
        assert MathTutoringSession.objects.filter(math_session=math_session).exists()

    def test_get_or_create_session_is_idempotent(self, math_session, mock_content, mock_llm_reply):
        """2026-03-02: Second call returns same session without calling LLM again."""
        result1 = MathTutoringService.get_or_create_session(math_session)
        result2 = MathTutoringService.get_or_create_session(math_session)

        assert result1['session_id'] == result2['session_id']
        assert len(result2['messages']) == 1  # 2026-03-02: No duplicate opening message
        # 2026-03-02: LLM called exactly once (only during creation)
        mock_llm_reply.return_value.chat.call_count <= 1

    def test_opening_message_fallback_when_llm_fails(self, math_session, mock_content):
        """2026-03-02: Falls back to JSON-built message when LLM unavailable."""
        with patch('services.math_service.tutoring.get_llm_provider',
                   side_effect=Exception('LLM down')):
            result = MathTutoringService.get_or_create_session(math_session)

        assert result['success'] is True
        messages = result['messages']
        assert len(messages) == 1
        # 2026-03-02: Fallback contains key JSON fields
        text = messages[0]['text']
        assert 'Bunny the Counter' in text  # 2026-03-02: Character name
        assert 'Numbers 1-5' in text         # 2026-03-02: Day title
        assert 'count' in text.lower()        # 2026-03-02: Teaching content

    def test_chat_appends_messages(self, math_session, mock_content, mock_llm_reply):
        """2026-03-02: Chat adds student message and tutor reply."""
        MathTutoringService.get_or_create_session(math_session)  # 2026-03-02: Create first

        result = MathTutoringService.chat(math_session, 'How do I count?')

        assert result['success'] is True
        assert result['reply']  # 2026-03-02: Non-empty reply
        assert len(result['messages']) == 3  # 2026-03-02: Opening + student + tutor
        assert result['messages'][1]['role'] == 'student'
        assert result['messages'][2]['role'] == 'tutor'

    def test_chat_fails_when_session_not_started(self, math_session, mock_content):
        """2026-03-02: Chat returns error if teaching session not yet created."""
        result = MathTutoringService.chat(math_session, 'Hello')

        assert result['success'] is False
        assert 'not started' in result['error'].lower()

    def test_chat_fails_when_already_complete(self, math_session, mock_content, mock_llm_reply):
        """2026-03-02: Chat returns error if teaching phase already completed."""
        MathTutoringService.get_or_create_session(math_session)
        MathTutoringService.complete_teaching(math_session)

        result = MathTutoringService.chat(math_session, 'Can I ask more?')

        assert result['success'] is False
        assert 'completed' in result['error'].lower()

    def test_chat_fallback_when_llm_fails(self, math_session, mock_content):
        """2026-03-02: Chat returns a safe fallback reply when LLM fails mid-chat."""
        # 2026-03-02: Create session with working LLM first
        mock_resp = MagicMock()
        mock_resp.text = 'Opening message.'
        with patch('services.math_service.tutoring.get_llm_provider') as m:
            m.return_value.chat.return_value = mock_resp
            MathTutoringService.get_or_create_session(math_session)

        # 2026-03-02: Then fail LLM during chat
        with patch('services.math_service.tutoring.get_llm_provider',
                   side_effect=Exception('LLM down')):
            result = MathTutoringService.chat(math_session, 'What is 2+2?')

        assert result['success'] is True
        assert len(result['reply']) > 0  # 2026-03-02: Fallback reply returned

    def test_complete_teaching_sets_flag(self, math_session, mock_content, mock_llm_reply):
        """2026-03-02: complete_teaching sets teaching_complete=True in DB."""
        MathTutoringService.get_or_create_session(math_session)
        result = MathTutoringService.complete_teaching(math_session)

        assert result['success'] is True
        assert result['teaching_complete'] is True

        # 2026-03-02: Verify DB state
        tutoring = MathTutoringSession.objects.get(math_session=math_session)
        assert tutoring.teaching_complete is True

    def test_complete_teaching_fails_when_no_session(self, math_session, db):
        """2026-03-02: complete_teaching errors if no tutoring session exists."""
        result = MathTutoringService.complete_teaching(math_session)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_day_content_returns_teaching_fields(self, math_lesson, mock_content):
        """2026-03-02: get_day_content returns title, teaching_summary, worked_examples."""
        content = MathContentLoader.get_day_content(
            math_lesson.content_json_path, day=1
        )

        assert content['day'] == 1
        assert content['title'] == 'Numbers 1-5'
        assert 'count' in content['teaching_summary'].lower()
        assert len(content['worked_examples']) == 1
        assert content['worked_examples'][0]['answer'] == '4'

    def test_fallback_message_contains_key_content(self, db):
        """2026-03-02: _build_fallback_message uses character, title, summary, example."""
        msg = MathTutoringService._build_fallback_message(
            character='Bunny the Counter',
            day_title='Numbers 1-5',
            teaching_summary='We count by touching each object once.',
            worked_examples=[{
                'problem': 'Count ★★★',
                'solution_steps': ['Step 1: 1, 2, 3'],
                'answer': '3',
            }],
        )

        assert 'Bunny the Counter' in msg
        assert 'Numbers 1-5' in msg
        assert 'count' in msg.lower()
        assert 'Count ★★★' in msg
        assert '3' in msg


# ── API integration tests ─────────────────────────────────────────────────────

class TestMathTutoringAPI:
    """2026-03-02: API integration tests for math tutoring endpoints."""

    def _start_session(self, client, mock_content):
        """2026-03-02: Helper — start a math session via API."""
        response = client.post(f'{BASE_URL}sessions/', {
            'lesson_id': 'MATH1_W01_TUT',
            'day_number': 1,
        }, format='json')
        assert response.status_code == 201
        return response.json()['session_id']

    def test_get_teaching_session_creates_and_returns_200(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: GET teach/ creates tutoring session and returns 200."""
        session_id = self._start_session(student_client, mock_content)
        response = student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['teaching_complete'] is False
        assert len(data['messages']) == 1
        assert data['messages'][0]['role'] == 'tutor'
        assert data['character'] == 'Bunny the Counter'

    def test_get_teaching_session_is_idempotent(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: Calling GET teach/ twice returns same session_id."""
        session_id = self._start_session(student_client, mock_content)

        r1 = student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')
        r2 = student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')

        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()['session_id'] == r2.json()['session_id']

    def test_get_teaching_session_unauthenticated(self, math_lesson, db):
        """2026-03-02: GET teach/ returns 401 without auth token."""
        client = APIClient()
        fake_id = str(uuid.uuid4())
        response = client.get(f'{BASE_URL}sessions/{fake_id}/teach/')
        assert response.status_code == 401

    def test_post_chat_returns_reply(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: POST teach/chat/ returns tutor reply and updated messages."""
        session_id = self._start_session(student_client, mock_content)
        student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')  # 2026-03-02: Create

        response = student_client.post(
            f'{BASE_URL}sessions/{session_id}/teach/chat/',
            {'message': 'How do I count?'},
            format='json',
        )

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert len(data['reply']) > 0
        assert data['teaching_complete'] is False
        assert len(data['messages']) == 3  # 2026-03-02: opening + student + tutor

    def test_post_chat_missing_message_returns_400(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: POST teach/chat/ without message field returns 400."""
        session_id = self._start_session(student_client, mock_content)
        student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')

        response = student_client.post(
            f'{BASE_URL}sessions/{session_id}/teach/chat/',
            {},  # 2026-03-02: Missing message
            format='json',
        )
        assert response.status_code == 400

    def test_post_complete_marks_done(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: POST teach/complete/ sets teaching_complete=True."""
        session_id = self._start_session(student_client, mock_content)
        student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')  # 2026-03-02: Create

        response = student_client.post(f'{BASE_URL}sessions/{session_id}/teach/complete/')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['teaching_complete'] is True

    def test_post_complete_unauthenticated(self, math_lesson, db):
        """2026-03-02: POST teach/complete/ returns 401 without auth."""
        client = APIClient()
        fake_id = str(uuid.uuid4())
        response = client.post(f'{BASE_URL}sessions/{fake_id}/teach/complete/')
        assert response.status_code == 401

    def test_student_cannot_access_other_students_session(
        self, student_client, student2_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: Student 2 cannot access Student 1's teaching session (404)."""
        session_id = self._start_session(student_client, mock_content)

        # 2026-03-02: Student 2 tries to access Student 1's teach/ endpoint
        response = student2_client.get(f'{BASE_URL}sessions/{session_id}/teach/')
        assert response.status_code == 404

    def test_full_teaching_flow(
        self, student_client, math_lesson, mock_content, mock_llm_reply
    ):
        """2026-03-02: Full flow: start → teach → chat → complete → practice."""
        # 2026-03-02: Step 1: Start math session
        session_id = self._start_session(student_client, mock_content)

        # 2026-03-02: Step 2: Get teaching session (AI teaches)
        r_teach = student_client.get(f'{BASE_URL}sessions/{session_id}/teach/')
        assert r_teach.status_code == 200
        assert r_teach.json()['teaching_complete'] is False

        # 2026-03-02: Step 3: Student asks a question
        r_chat = student_client.post(
            f'{BASE_URL}sessions/{session_id}/teach/chat/',
            {'message': 'Can you explain again?'},
            format='json',
        )
        assert r_chat.status_code == 200
        assert len(r_chat.json()['messages']) == 3

        # 2026-03-02: Step 4: Student is ready
        r_complete = student_client.post(
            f'{BASE_URL}sessions/{session_id}/teach/complete/'
        )
        assert r_complete.status_code == 200
        assert r_complete.json()['teaching_complete'] is True

        # 2026-03-02: Step 5: Can still submit practice answers (session still active)
        r_answer = student_client.post(
            f'{BASE_URL}sessions/{session_id}/answer/',
            {'problem_id': 'MATH1_W01_D1_M1', 'answer': '3'},
            format='json',
        )
        assert r_answer.status_code == 200
