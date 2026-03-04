"""
2026-03-02: Service-layer tests for Language Stages Service (BS-LNG-005).

Purpose:
    Verify ConversationService business logic:
    - get_scenarios: 20 returned, unlock gate enforced
    - start_session: DB record created, AI opening generated
    - submit_turn: student + AI turns saved, quality score recorded
    - complete_session: stars computed, progress updated
    - StudentConversationProgress: scenarios_completed, streak, best_star
    - Edge cases: locked scenario, invalid language, session ownership

~22 service tests.
"""

import json  # 2026-03-02: JSON
import pytest  # 2026-03-02: Pytest
from datetime import date  # 2026-03-02: DOB
from unittest.mock import patch, MagicMock  # 2026-03-02: Mocking

from django.contrib.auth import get_user_model  # 2026-03-02: User model

from services.auth_service.models import Parent, Student  # 2026-03-02: Auth
from services.read_along_service.models import Language  # 2026-03-02: Language
from services.language_stages_service.models import (  # 2026-03-02: Models
    ConversationScenario, ConversationSession, ConversationTurn,
    StudentConversationProgress,
)
from services.language_stages_service.services import (  # 2026-03-02: Service
    ConversationService, _quality_to_stars,
)

User = get_user_model()  # 2026-03-02: Django User


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-03-02: Parent user for testing."""
    user = User.objects.create_user(username='ls_parent', password='pass123')
    return Parent.objects.create(
        user=user,
        phone='+919000000088',
        full_name='LS Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Student for testing."""
    user = User.objects.create_user(username='ls_student', password='pass123')
    return Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='LS Student',
        dob=date(2016, 3, 15),
        age_group='6-12',
        grade=2,
        login_method='pin',
    )


@pytest.fixture
def hindi_language(db):
    """2026-03-02: Hindi language (seeded or created)."""
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
            'opening_prompt_template': 'Hello! Tell me your name in {target_language}.',
        },
    )
    return s


@pytest.fixture
def scenario2(db):
    """2026-03-02: Second scenario (locked until scenario 1 completed at ≥2 stars)."""
    s, _ = ConversationScenario.objects.get_or_create(
        scenario_number=2,
        defaults={
            'title': 'At the Market',
            'ai_persona': 'shopkeeper',
            'difficulty': 'beginner',
            'min_turns': 4,
            'max_turns': 10,
            'unlock_after_scenario': 1,
            'context_description': 'Buying things.',
            'opening_prompt_template': 'Welcome! What do you want in {target_language}?',
        },
    )
    return s


@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    """
    2026-03-02: Patch all LLM calls in ConversationService to avoid real network calls.

    _generate_opening → returns 'Hello from AI!'
    _evaluate_turn    → returns quality=70, no grammar error, no recast
    _generate_response→ returns 'AI response here.'
    """
    monkeypatch.setattr(
        ConversationService, '_generate_opening',
        staticmethod(lambda scenario, lang: 'Hello from AI!'),
    )
    monkeypatch.setattr(
        ConversationService, '_evaluate_turn',
        staticmethod(lambda *args, **kwargs: {'quality': 70, 'grammar_error': None, 'recast': None}),
    )
    monkeypatch.setattr(
        ConversationService, '_generate_response',
        staticmethod(lambda *args, **kwargs: 'AI response here.'),
    )


# ── TestQualityToStars ─────────────────────────────────────────────────────

class TestQualityToStars:
    """2026-03-02: Tests for _quality_to_stars helper."""

    def test_zero_quality_gives_zero(self):
        """2026-03-02: quality=0 → 0 stars."""
        assert _quality_to_stars(0) == 0

    def test_quality_below_20_gives_1_star(self):
        """2026-03-02: quality=15 → 1 star."""
        assert _quality_to_stars(15) == 1

    def test_quality_20_to_39_gives_2_stars(self):
        """2026-03-02: quality=35 → 2 stars."""
        assert _quality_to_stars(35) == 2

    def test_quality_40_to_59_gives_3_stars(self):
        """2026-03-02: quality=55 → 3 stars."""
        assert _quality_to_stars(55) == 3

    def test_quality_60_to_79_gives_4_stars(self):
        """2026-03-02: quality=72 → 4 stars."""
        assert _quality_to_stars(72) == 4

    def test_quality_80_plus_gives_5_stars(self):
        """2026-03-02: quality=85 → 5 stars."""
        assert _quality_to_stars(85) == 5

    def test_quality_100_gives_5_stars(self):
        """2026-03-02: quality=100 → 5 stars."""
        assert _quality_to_stars(100) == 5


# ── TestGetScenarios ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetScenarios:
    """2026-03-02: Tests for ConversationService.get_scenarios()."""

    def test_returns_all_20_scenarios_when_seeded(self, student, hindi_language, db):
        """2026-03-02: All 20 seeded scenarios are returned."""
        # Create 20 scenarios
        from services.language_stages_service.scenario_catalog import SCENARIO_CATALOG
        for data in SCENARIO_CATALOG:
            ConversationScenario.objects.get_or_create(
                scenario_number=data['scenario_number'],
                defaults={k: v for k, v in data.items() if k != 'scenario_number'},
            )
        result = ConversationService.get_scenarios(student, 'Hindi')
        assert len(result) == 20

    def test_scenario1_always_unlocked(self, student, hindi_language, scenario1, db):
        """2026-03-02: Scenario 1 has no prerequisite → is_unlocked=True."""
        result = ConversationService.get_scenarios(student, 'Hindi')
        s1 = next(r for r in result if r['scenario_number'] == 1)
        assert s1['is_unlocked'] is True

    def test_scenario2_locked_without_prerequisite(
        self, student, hindi_language, scenario1, scenario2, db
    ):
        """2026-03-02: Scenario 2 locked when scenario 1 not completed at >=2 stars."""
        result = ConversationService.get_scenarios(student, 'Hindi')
        s2 = next(r for r in result if r['scenario_number'] == 2)
        assert s2['is_unlocked'] is False

    def test_scenario2_unlocked_after_scenario1_completed(
        self, student, hindi_language, scenario1, scenario2, db
    ):
        """2026-03-02: Scenario 2 unlocks once scenario 1 has >=2 stars."""
        # Give student 3 stars on scenario 1
        StudentConversationProgress.objects.create(
            student=student,
            language=hindi_language,
            best_star_by_scenario={'1': 3},
        )
        result = ConversationService.get_scenarios(student, 'Hindi')
        s2 = next(r for r in result if r['scenario_number'] == 2)
        assert s2['is_unlocked'] is True

    def test_best_star_shows_in_scenario_list(
        self, student, hindi_language, scenario1, db
    ):
        """2026-03-02: best_star_rating shows correct prior best for each scenario."""
        StudentConversationProgress.objects.create(
            student=student,
            language=hindi_language,
            best_star_by_scenario={'1': 4},
        )
        result = ConversationService.get_scenarios(student, 'Hindi')
        s1 = next(r for r in result if r['scenario_number'] == 1)
        assert s1['best_star_rating'] == 4

    def test_invalid_language_raises(self, student, db):
        """2026-03-02: Unknown language raises ValidationError."""
        from rest_framework.exceptions import ValidationError
        with pytest.raises(Exception):
            ConversationService.get_scenarios(student, 'Klingon')


# ── TestStartSession ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestStartSession:
    """2026-03-02: Tests for ConversationService.start_session()."""

    def test_creates_session_record(self, student, hindi_language, scenario1, db):
        """2026-03-02: ConversationSession is created in DB."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        session = ConversationSession.objects.get(id=result['session_id'])
        assert session.status == 'in_progress'
        assert session.student == student

    def test_returns_opening_text(self, student, hindi_language, scenario1, db):
        """2026-03-02: Opening text is returned and non-empty."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        assert result['opening_text']  # 2026-03-02: Not empty
        assert result['session_id']

    def test_ai_opening_turn_saved(self, student, hindi_language, scenario1, db):
        """2026-03-02: AI turn 1 is persisted to ConversationTurn."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        session = ConversationSession.objects.get(id=result['session_id'])
        turn = session.turns.filter(turn_number=1, role='ai').first()
        assert turn is not None
        assert turn.text == 'Hello from AI!'  # 2026-03-02: Mock value

    def test_locked_scenario_raises(self, student, hindi_language, scenario1, scenario2, db):
        """2026-03-02: Starting a locked scenario raises ValidationError."""
        from rest_framework.exceptions import ValidationError
        with pytest.raises(ValidationError):
            ConversationService.start_session(student, 'Hindi', str(scenario2.id))

    def test_nonexistent_scenario_raises(self, student, hindi_language, db):
        """2026-03-02: Unknown scenario UUID raises NotFound."""
        import uuid
        from rest_framework.exceptions import NotFound
        with pytest.raises(NotFound):
            ConversationService.start_session(student, 'Hindi', str(uuid.uuid4()))


# ── TestSubmitTurn ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestSubmitTurn:
    """2026-03-02: Tests for ConversationService.submit_turn()."""

    @pytest.fixture
    def active_session(self, student, hindi_language, scenario1, db):
        """2026-03-02: An in-progress ConversationSession with AI opening."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        return ConversationSession.objects.get(id=result['session_id'])

    def test_saves_student_turn(self, active_session, student):
        """2026-03-02: Student ConversationTurn is saved."""
        ConversationService.submit_turn(
            str(active_session.id), student, 'Mera naam Rahul hai.'
        )
        student_turns = active_session.turns.filter(role='student')
        assert student_turns.count() == 1

    def test_saves_ai_response_turn(self, active_session, student):
        """2026-03-02: AI ConversationTurn is saved after evaluation."""
        ConversationService.submit_turn(
            str(active_session.id), student, 'Mera naam Rahul hai.'
        )
        ai_turns = active_session.turns.filter(role='ai')
        assert ai_turns.count() == 2  # 2026-03-02: Opening + response

    def test_returns_ai_response(self, active_session, student):
        """2026-03-02: submit_turn returns ai_response string."""
        result = ConversationService.submit_turn(
            str(active_session.id), student, 'Mera naam Rahul hai.'
        )
        assert result['ai_response'] == 'AI response here.'

    def test_returns_turn_quality(self, active_session, student):
        """2026-03-02: submit_turn returns turn_quality 0-1."""
        result = ConversationService.submit_turn(
            str(active_session.id), student, 'Namaste!'
        )
        assert 0.0 <= result['turn_quality'] <= 1.0

    def test_turn_count_increments(self, active_session, student):
        """2026-03-02: session.turn_count increments on each student turn."""
        ConversationService.submit_turn(str(active_session.id), student, 'Hello.')
        active_session.refresh_from_db()
        assert active_session.turn_count == 1

    def test_is_complete_when_min_turns_reached(self, active_session, student):
        """2026-03-02: is_complete=True when turn_count >= min_turns and quality >= 0.5."""
        # scenario1.min_turns=4; submit 4 turns
        for i in range(4):
            result = ConversationService.submit_turn(
                str(active_session.id), student, f'Turn {i+1} text here.'
            )
        assert result['is_complete'] is True

    def test_is_not_complete_below_min_turns(self, active_session, student):
        """2026-03-02: is_complete=False when turn_count < min_turns."""
        result = ConversationService.submit_turn(
            str(active_session.id), student, 'First turn.'
        )
        assert result['is_complete'] is False

    def test_wrong_student_raises(self, active_session, parent_user, db):
        """2026-03-02: Submitting for another student's session raises ValidationError."""
        from rest_framework.exceptions import ValidationError
        other_user = User.objects.create_user(username='other_ls', password='pass')
        other_student = Student.objects.create(
            parent=parent_user, user=other_user,
            full_name='Other',
            dob=date(2016, 1, 1), age_group='6-12',
            grade=1, login_method='pin',
        )
        with pytest.raises(ValidationError):
            ConversationService.submit_turn(str(active_session.id), other_student, 'Hi')


# ── TestCompleteSession ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestCompleteSession:
    """2026-03-02: Tests for ConversationService.complete_session()."""

    @pytest.fixture
    def session_with_turns(self, student, hindi_language, scenario1, db):
        """2026-03-02: Session with 4 completed turns ready to close."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        session = ConversationSession.objects.get(id=result['session_id'])
        for i in range(4):
            ConversationService.submit_turn(str(session.id), student, f'Turn {i+1}.')
        return session

    def test_session_marked_completed(self, session_with_turns, student):
        """2026-03-02: Session status becomes 'completed'."""
        ConversationService.complete_session(str(session_with_turns.id), student)
        session_with_turns.refresh_from_db()
        assert session_with_turns.status == 'completed'

    def test_returns_fluency_star_rating(self, session_with_turns, student):
        """2026-03-02: Returns an integer fluency_star_rating 0-5."""
        result = ConversationService.complete_session(str(session_with_turns.id), student)
        assert 0 <= result['fluency_star_rating'] <= 5

    def test_high_quality_gives_high_stars(self, student, hindi_language, scenario1, db):
        """2026-03-02: quality=70/100 → ≥3 stars (mock gives 70)."""
        result = ConversationService.start_session(student, 'Hindi', str(scenario1.id))
        session = ConversationSession.objects.get(id=result['session_id'])
        for i in range(4):
            ConversationService.submit_turn(str(session.id), student, f'Turn {i+1}.')
        complete = ConversationService.complete_session(str(session.id), student)
        # mock quality=70 → mean_100=70 → 4 stars
        assert complete['fluency_star_rating'] == 4

    def test_progress_updated(self, session_with_turns, student, hindi_language):
        """2026-03-02: StudentConversationProgress updated after completion."""
        ConversationService.complete_session(str(session_with_turns.id), student)
        progress = StudentConversationProgress.objects.get(
            student=student, language=hindi_language
        )
        assert progress.total_turns >= 4  # 2026-03-02: Turns accumulated

    def test_best_star_recorded(self, session_with_turns, student, hindi_language, scenario1):
        """2026-03-02: best_star_by_scenario updated."""
        ConversationService.complete_session(str(session_with_turns.id), student)
        progress = StudentConversationProgress.objects.get(
            student=student, language=hindi_language
        )
        key = str(scenario1.scenario_number)
        assert key in progress.best_star_by_scenario

    def test_double_complete_raises(self, session_with_turns, student):
        """2026-03-02: Completing an already-completed session raises ValidationError."""
        from rest_framework.exceptions import ValidationError
        ConversationService.complete_session(str(session_with_turns.id), student)
        with pytest.raises(ValidationError):
            ConversationService.complete_session(str(session_with_turns.id), student)
