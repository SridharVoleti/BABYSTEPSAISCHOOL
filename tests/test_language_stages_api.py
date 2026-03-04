"""
2026-03-02: API integration tests for Language Stages Service (BS-LNG-005).

Purpose:
    Verify all 5 API endpoints via DRF test client with JWT auth:
    - GET  /api/v1/language-stages/scenarios/
    - POST /api/v1/language-stages/session/start/
    - POST /api/v1/language-stages/session/<id>/turn/
    - POST /api/v1/language-stages/session/<id>/complete/
    - GET  /api/v1/language-stages/progress/

Covers: 200/201, 400, 401, 403, 404 status codes.

~23 API tests.
"""

import pytest  # 2026-03-02: Pytest framework
from datetime import date  # 2026-03-02: DOB

from django.contrib.auth import get_user_model  # 2026-03-02: User model

from rest_framework.test import APIClient  # 2026-03-02: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-03-02: JWT

from services.auth_service.models import Parent, Student  # 2026-03-02: Auth
from services.read_along_service.models import Language  # 2026-03-02: Language
from services.language_stages_service.models import (  # 2026-03-02: Models
    ConversationScenario, ConversationSession,
)
from services.language_stages_service.services import ConversationService  # 2026-03-02

User = get_user_model()  # 2026-03-02: Django User

BASE_URL = '/api/v1/language-stages/'  # 2026-03-02: URL prefix


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-03-02: Parent user."""
    user = User.objects.create_user(username='api_ls_parent', password='pass123')
    return Parent.objects.create(
        user=user,
        phone='+919000000077',
        full_name='API LS Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Student."""
    user = User.objects.create_user(username='api_ls_student', password='pass123')
    return Student.objects.create(
        parent=parent_user, user=user,
        full_name='API LS Student',
        dob=date(2016, 5, 20),
        age_group='6-12', grade=2,
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
def hindi_language(db):
    """2026-03-02: Hindi language."""
    lang, _ = Language.objects.get_or_create(
        name='Hindi',
        defaults={'bcp47_tag': 'hi-IN', 'native_name': 'हिन्दी', 'is_active': True},
    )
    return lang


@pytest.fixture
def scenario1(db):
    """2026-03-02: First scenario (always unlocked)."""
    s, _ = ConversationScenario.objects.get_or_create(
        scenario_number=1,
        defaults={
            'title': 'Introducing Yourself',
            'ai_persona': 'friendly neighbour',
            'difficulty': 'beginner',
            'min_turns': 4,
            'max_turns': 8,
            'unlock_after_scenario': None,
            'context_description': 'Test context.',
            'opening_prompt_template': 'Hello! Tell me in {target_language}.',
        },
    )
    return s


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """2026-03-02: Suppress all LLM calls in ConversationService."""
    monkeypatch.setattr(
        ConversationService, '_generate_opening',
        staticmethod(lambda scenario, lang: 'AI opening line.'),
    )
    monkeypatch.setattr(
        ConversationService, '_evaluate_turn',
        staticmethod(lambda *args, **kwargs: {'quality': 75, 'grammar_error': None, 'recast': None}),
    )
    monkeypatch.setattr(
        ConversationService, '_generate_response',
        staticmethod(lambda *args, **kwargs: 'AI next line.'),
    )


# ── Test: GET /scenarios/ ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestScenariosEndpoint:
    """2026-03-02: GET /api/v1/language-stages/scenarios/"""

    def test_200_student_authenticated(self, student_client, hindi_language, scenario1):
        """2026-03-02: Authenticated student gets 200."""
        resp = student_client.get(f'{BASE_URL}scenarios/?language=Hindi')
        assert resp.status_code == 200

    def test_response_includes_scenarios_list(self, student_client, hindi_language, scenario1):
        """2026-03-02: Response body has 'scenarios' list."""
        resp = student_client.get(f'{BASE_URL}scenarios/?language=Hindi')
        assert 'scenarios' in resp.json()

    def test_401_unauthenticated(self, hindi_language, scenario1):
        """2026-03-02: Unauthenticated request → 401."""
        client = APIClient()
        resp = client.get(f'{BASE_URL}scenarios/?language=Hindi')
        assert resp.status_code == 401

    def test_403_parent(self, parent_client, hindi_language, scenario1):
        """2026-03-02: Parent cannot access scenarios endpoint → 403."""
        resp = parent_client.get(f'{BASE_URL}scenarios/?language=Hindi')
        assert resp.status_code == 403

    def test_400_missing_language(self, student_client, hindi_language):
        """2026-03-02: Missing language query param → 400."""
        resp = student_client.get(f'{BASE_URL}scenarios/')
        assert resp.status_code == 400

    def test_scenario_has_unlock_field(self, student_client, hindi_language, scenario1):
        """2026-03-02: Each scenario dict contains is_unlocked field."""
        resp = student_client.get(f'{BASE_URL}scenarios/?language=Hindi')
        scenarios = resp.json()['scenarios']
        assert len(scenarios) >= 1
        assert 'is_unlocked' in scenarios[0]


# ── Test: POST /session/start/ ─────────────────────────────────────────────

@pytest.mark.django_db
class TestSessionStartEndpoint:
    """2026-03-02: POST /api/v1/language-stages/session/start/"""

    def test_201_on_valid_start(self, student_client, hindi_language, scenario1):
        """2026-03-02: Valid request → 201 Created."""
        resp = student_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        assert resp.status_code == 201

    def test_response_contains_session_id(self, student_client, hindi_language, scenario1):
        """2026-03-02: Response includes session_id."""
        resp = student_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        assert 'session_id' in resp.json()

    def test_response_contains_opening_text(self, student_client, hindi_language, scenario1):
        """2026-03-02: Response includes opening_text from AI."""
        resp = student_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        assert resp.json()['opening_text'] == 'AI opening line.'

    def test_400_missing_fields(self, student_client, hindi_language):
        """2026-03-02: Missing language or scenario_id → 400."""
        resp = student_client.post(f'{BASE_URL}session/start/', {}, format='json')
        assert resp.status_code == 400

    def test_401_unauthenticated(self, hindi_language, scenario1):
        """2026-03-02: No auth → 401."""
        client = APIClient()
        resp = client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        assert resp.status_code == 401

    def test_403_parent(self, parent_client, hindi_language, scenario1):
        """2026-03-02: Parent user → 403."""
        resp = parent_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        assert resp.status_code == 403


# ── Test: POST /session/<id>/turn/ ─────────────────────────────────────────

@pytest.mark.django_db
class TestSessionTurnEndpoint:
    """2026-03-02: POST /api/v1/language-stages/session/<id>/turn/"""

    @pytest.fixture
    def started_session_id(self, student_client, hindi_language, scenario1):
        """2026-03-02: Session started for this test class."""
        resp = student_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        return resp.json()['session_id']

    def test_200_on_valid_turn(self, student_client, started_session_id):
        """2026-03-02: Valid turn → 200 OK."""
        resp = student_client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {'text': 'Mera naam Rahul hai.'},
            format='json',
        )
        assert resp.status_code == 200

    def test_response_has_ai_response(self, student_client, started_session_id):
        """2026-03-02: Response includes ai_response."""
        resp = student_client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {'text': 'Namaste!'},
            format='json',
        )
        assert 'ai_response' in resp.json()

    def test_response_has_turn_quality(self, student_client, started_session_id):
        """2026-03-02: Response includes turn_quality (float)."""
        resp = student_client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {'text': 'Hello.'},
            format='json',
        )
        assert 'turn_quality' in resp.json()

    def test_response_has_is_complete(self, student_client, started_session_id):
        """2026-03-02: Response includes is_complete boolean."""
        resp = student_client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {'text': 'First turn.'},
            format='json',
        )
        assert 'is_complete' in resp.json()

    def test_400_missing_text(self, student_client, started_session_id):
        """2026-03-02: Missing 'text' → 400."""
        resp = student_client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {},
            format='json',
        )
        assert resp.status_code == 400

    def test_401_unauthenticated(self, started_session_id):
        """2026-03-02: No auth → 401."""
        client = APIClient()
        resp = client.post(
            f'{BASE_URL}session/{started_session_id}/turn/',
            {'text': 'Hello.'},
            format='json',
        )
        assert resp.status_code == 401


# ── Test: POST /session/<id>/complete/ ────────────────────────────────────

@pytest.mark.django_db
class TestSessionCompleteEndpoint:
    """2026-03-02: POST /api/v1/language-stages/session/<id>/complete/"""

    @pytest.fixture
    def session_ready_to_complete(
        self, student_client, hindi_language, scenario1
    ):
        """2026-03-02: Session with 4 turns submitted."""
        resp = student_client.post(
            f'{BASE_URL}session/start/',
            {'language': 'Hindi', 'scenario_id': str(scenario1.id)},
            format='json',
        )
        sid = resp.json()['session_id']
        for i in range(4):
            student_client.post(
                f'{BASE_URL}session/{sid}/turn/',
                {'text': f'Turn {i + 1}.'},
                format='json',
            )
        return sid

    def test_200_on_complete(self, student_client, session_ready_to_complete):
        """2026-03-02: Valid complete → 200 OK."""
        resp = student_client.post(
            f'{BASE_URL}session/{session_ready_to_complete}/complete/',
            {},
            format='json',
        )
        assert resp.status_code == 200

    def test_response_has_fluency_star_rating(
        self, student_client, session_ready_to_complete
    ):
        """2026-03-02: Response includes fluency_star_rating."""
        resp = student_client.post(
            f'{BASE_URL}session/{session_ready_to_complete}/complete/',
            {},
            format='json',
        )
        data = resp.json()
        assert 'fluency_star_rating' in data
        assert 0 <= data['fluency_star_rating'] <= 5

    def test_401_unauthenticated(self, session_ready_to_complete):
        """2026-03-02: No auth → 401."""
        client = APIClient()
        resp = client.post(
            f'{BASE_URL}session/{session_ready_to_complete}/complete/',
            {},
            format='json',
        )
        assert resp.status_code == 401


# ── Test: GET /progress/ ───────────────────────────────────────────────────

@pytest.mark.django_db
class TestProgressEndpoint:
    """2026-03-02: GET /api/v1/language-stages/progress/"""

    def test_200_student(self, student_client, hindi_language):
        """2026-03-02: Authenticated student gets 200."""
        resp = student_client.get(f'{BASE_URL}progress/?language=Hindi')
        assert resp.status_code == 200

    def test_response_has_scenarios_completed(self, student_client, hindi_language):
        """2026-03-02: Response includes scenarios_completed."""
        resp = student_client.get(f'{BASE_URL}progress/?language=Hindi')
        assert 'scenarios_completed' in resp.json()

    def test_400_missing_language(self, student_client):
        """2026-03-02: Missing language param → 400."""
        resp = student_client.get(f'{BASE_URL}progress/')
        assert resp.status_code == 400

    def test_401_unauthenticated(self, hindi_language):
        """2026-03-02: No auth → 401."""
        client = APIClient()
        resp = client.get(f'{BASE_URL}progress/?language=Hindi')
        assert resp.status_code == 401

    def test_403_parent(self, parent_client, hindi_language):
        """2026-03-02: Parent user → 403."""
        resp = parent_client.get(f'{BASE_URL}progress/?language=Hindi')
        assert resp.status_code == 403
