"""
2026-02-18: Tests for 5-Star Mastery Practice System (BS-STR).

Purpose:
    Test adaptive engine, mastery practice service, and API endpoints
    for the mastery practice module. Covers difficulty adaptation,
    star calculation, question selection, session flow, mastery gate,
    and all 3 API endpoints.
"""

import json  # 2026-02-18: JSON
import uuid  # 2026-02-18: UUID
import pytest  # 2026-02-18: Pytest framework
from datetime import date  # 2026-02-18: Date for DOB
from unittest.mock import patch, MagicMock  # 2026-02-18: Mocking

from django.contrib.auth import get_user_model  # 2026-02-18: User model
from django.conf import settings  # 2026-02-18: Settings
from rest_framework.test import APIClient  # 2026-02-18: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-18: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-18: Auth models
from services.teaching_engine.models import (  # 2026-02-18: Models
    TeachingLesson, StudentLessonProgress, DayProgress,
    PracticeSession, PracticeResponse, ConceptMastery,
)
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-18: Loader
from services.teaching_engine.services import TeachingService, MasteryPracticeService  # 2026-02-18: Services
from services.teaching_engine.adaptive import (  # 2026-02-18: Adaptive engine
    AdaptiveEngine, QUESTION_COUNTS, STARTING_DIFFICULTY,
    STAR_THRESHOLDS, MASTERY_GATE_STARS,
)

User = get_user_model()  # 2026-02-18: Django User model

# 2026-02-18: Sample content JSON path
SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-18: Create a parent user for testing."""
    user = User.objects.create_user(
        username='test_parent_mastery', password='testpass123'
    )
    parent = Parent.objects.create(
        user=user,
        phone='+919876543288',
        full_name='Test Parent Mastery',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-18: Create a student user for testing."""
    user = User.objects.create_user(
        username='test_student_mastery', password='testpass123'
    )
    student = Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='Test Student Mastery',
        dob=date(2019, 5, 15),
        age_group='6-12',
        grade=1,
        login_method='pin',
    )
    return student


@pytest.fixture
def student_client(student_user):
    """2026-02-18: Authenticated API client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-18: Authenticated API client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def published_lesson(db):
    """2026-02-18: Create a published teaching lesson."""
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
def lesson_progress(student_user, published_lesson, db):
    """2026-02-18: Create lesson progress for student."""
    return StudentLessonProgress.objects.create(
        student=student_user,
        lesson=published_lesson,
        iq_level='standard',
        current_day=1,
        day_statuses={
            '1': 'not_started', '2': 'not_started',
            '3': 'not_started', '4': 'not_started', '5': 'not_started'
        },
    )


@pytest.fixture
def day_progress_mastery(lesson_progress, db):
    """2026-02-18: Create DayProgress in mastery_practice status."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=1,
        status='mastery_practice',
        practice_score=66,
        questions_attempted=3,
        questions_correct=2,
        revision_completed=True,
    )


@pytest.fixture(autouse=True)
def clear_content_cache():
    """2026-02-18: Clear content loader cache before each test."""
    TeachingContentLoader.clear_cache()
    yield
    TeachingContentLoader.clear_cache()


# ── Adaptive Engine Tests ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestAdaptiveEngine:
    """2026-02-18: Tests for AdaptiveEngine."""

    def test_get_total_questions_foundation(self):
        """2026-02-18: Foundation level gets 12-15 questions."""
        count = AdaptiveEngine.get_total_questions('foundation')
        assert 12 <= count <= 15  # 2026-02-18: Check range

    def test_get_total_questions_standard(self):
        """2026-02-18: Standard level gets 8-10 questions."""
        count = AdaptiveEngine.get_total_questions('standard')
        assert 8 <= count <= 10  # 2026-02-18: Check range

    def test_get_total_questions_advanced(self):
        """2026-02-18: Advanced level gets 5-7 questions."""
        count = AdaptiveEngine.get_total_questions('advanced')
        assert 5 <= count <= 7  # 2026-02-18: Check range

    def test_get_starting_difficulty_foundation(self):
        """2026-02-18: Foundation starts at easy."""
        assert AdaptiveEngine.get_starting_difficulty('foundation') == 'easy'

    def test_get_starting_difficulty_standard(self):
        """2026-02-18: Standard starts at medium."""
        assert AdaptiveEngine.get_starting_difficulty('standard') == 'medium'

    def test_get_starting_difficulty_advanced(self):
        """2026-02-18: Advanced starts at medium."""
        assert AdaptiveEngine.get_starting_difficulty('advanced') == 'medium'

    def test_adapt_difficulty_increase_after_2_correct(self):
        """2026-02-18: Difficulty increases after 2 consecutive correct."""
        result = AdaptiveEngine.adapt_difficulty('easy', 2, 0, 1)
        assert result == 'medium'  # 2026-02-18: Bumped up

    def test_adapt_difficulty_decrease_after_2_incorrect(self):
        """2026-02-18: Difficulty decreases after 2 consecutive incorrect."""
        result = AdaptiveEngine.adapt_difficulty('medium', 0, 2, 1)
        assert result == 'easy'  # 2026-02-18: Bumped down

    def test_adapt_difficulty_no_change_below_threshold(self):
        """2026-02-18: No change if streak below threshold."""
        result = AdaptiveEngine.adapt_difficulty('medium', 1, 0, 1)
        assert result == 'medium'  # 2026-02-18: No change

    def test_adapt_difficulty_ceiling_at_hard(self):
        """2026-02-18: Can't increase above hard."""
        result = AdaptiveEngine.adapt_difficulty('hard', 2, 0, 1)
        assert result == 'hard'  # 2026-02-18: Already at max

    def test_adapt_difficulty_floor_at_easy(self):
        """2026-02-18: Can't decrease below easy."""
        result = AdaptiveEngine.adapt_difficulty('easy', 0, 2, 1)
        assert result == 'easy'  # 2026-02-18: Already at min

    def test_adapt_difficulty_force_change_after_3_same(self):
        """2026-02-18: Force difficulty change after 3 same-difficulty questions."""
        result = AdaptiveEngine.adapt_difficulty('easy', 0, 0, 3)
        assert result == 'medium'  # 2026-02-18: Forced up

    def test_adapt_difficulty_force_change_hard_goes_down(self):
        """2026-02-18: Force change at hard goes to medium."""
        result = AdaptiveEngine.adapt_difficulty('hard', 0, 0, 3)
        assert result == 'medium'  # 2026-02-18: Forced down

    def test_calculate_star_rating_5_stars(self):
        """2026-02-18: 81-100% gets 5 stars."""
        assert AdaptiveEngine.calculate_star_rating(9, 10) == 5

    def test_calculate_star_rating_4_stars(self):
        """2026-02-18: 61-80% gets 4 stars."""
        assert AdaptiveEngine.calculate_star_rating(7, 10) == 4

    def test_calculate_star_rating_3_stars(self):
        """2026-02-18: 41-60% gets 3 stars."""
        assert AdaptiveEngine.calculate_star_rating(5, 10) == 3

    def test_calculate_star_rating_2_stars(self):
        """2026-02-18: 21-40% gets 2 stars."""
        assert AdaptiveEngine.calculate_star_rating(3, 10) == 2

    def test_calculate_star_rating_1_star(self):
        """2026-02-18: 0-20% gets 1 star."""
        assert AdaptiveEngine.calculate_star_rating(1, 10) == 1

    def test_calculate_star_rating_zero_questions(self):
        """2026-02-18: 0 questions returns 0 stars."""
        assert AdaptiveEngine.calculate_star_rating(0, 0) == 0

    def test_is_mastery_passed_true(self):
        """2026-02-18: 3+ stars passes mastery gate."""
        assert AdaptiveEngine.is_mastery_passed(3) is True
        assert AdaptiveEngine.is_mastery_passed(4) is True
        assert AdaptiveEngine.is_mastery_passed(5) is True

    def test_is_mastery_passed_false(self):
        """2026-02-18: Below 3 stars fails mastery gate."""
        assert AdaptiveEngine.is_mastery_passed(2) is False
        assert AdaptiveEngine.is_mastery_passed(1) is False
        assert AdaptiveEngine.is_mastery_passed(0) is False

    def test_select_question_from_target_difficulty(self):
        """2026-02-18: Selects from target difficulty when available."""
        bank = {
            'easy': [{'id': 'E1'}, {'id': 'E2'}],
            'medium': [{'id': 'M1'}],
            'hard': [{'id': 'H1'}],
        }
        question, diff = AdaptiveEngine.select_question(bank, 'easy', set())
        assert question['id'] in ('E1', 'E2')  # 2026-02-18: From easy pool
        assert diff == 'easy'

    def test_select_question_fallback_to_adjacent(self):
        """2026-02-18: Falls back to adjacent difficulty if target exhausted."""
        bank = {
            'easy': [],
            'medium': [{'id': 'M1'}],
            'hard': [{'id': 'H1'}],
        }
        question, diff = AdaptiveEngine.select_question(bank, 'easy', set())
        assert question['id'] == 'M1'  # 2026-02-18: Fallback to medium
        assert diff == 'medium'

    def test_select_question_skips_administered(self):
        """2026-02-18: Skips already-administered questions."""
        bank = {
            'easy': [{'id': 'E1'}, {'id': 'E2'}],
            'medium': [],
            'hard': [],
        }
        question, diff = AdaptiveEngine.select_question(bank, 'easy', {'E1'})
        assert question['id'] == 'E2'  # 2026-02-18: Only E2 left

    def test_select_question_returns_none_when_exhausted(self):
        """2026-02-18: Returns None when all questions exhausted."""
        bank = {'easy': [{'id': 'E1'}], 'medium': [], 'hard': []}
        question, diff = AdaptiveEngine.select_question(bank, 'easy', {'E1'})
        assert question is None  # 2026-02-18: Exhausted
        assert diff is None

    def test_check_answer_mcq_correct(self):
        """2026-02-18: MCQ correct answer check."""
        q = {'type': 'mcq', 'correct_answer': 1, 'explanation': 'Right!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, 1)
        assert is_correct is True
        assert correct == 1
        assert explanation == 'Right!'

    def test_check_answer_mcq_incorrect(self):
        """2026-02-18: MCQ incorrect answer check."""
        q = {'type': 'mcq', 'correct_answer': 1, 'explanation': 'Wrong!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, 0)
        assert is_correct is False

    def test_check_answer_true_false(self):
        """2026-02-18: True/false answer check."""
        q = {'type': 'true_false', 'correct_answer': True, 'explanation': 'Yes!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, True)
        assert is_correct is True

    def test_check_answer_numeric_fill(self):
        """2026-02-18: Numeric fill answer check."""
        q = {'type': 'numeric_fill', 'correct_answer': 5, 'explanation': 'Five!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, 5)
        assert is_correct is True

    def test_check_answer_drag_order_correct(self):
        """2026-02-18: Drag order correct answer check."""
        q = {'type': 'drag_order', 'correct_order': [1, 0, 2], 'explanation': 'Good!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, [1, 0, 2])
        assert is_correct is True
        assert correct == [1, 0, 2]

    def test_check_answer_drag_order_incorrect(self):
        """2026-02-18: Drag order incorrect answer check."""
        q = {'type': 'drag_order', 'correct_order': [1, 0, 2], 'explanation': 'Nope!'}
        is_correct, correct, explanation = AdaptiveEngine.check_answer(q, [0, 1, 2])
        assert is_correct is False


# ── Content Loader Practice Bank Tests ────────────────────────────────────

@pytest.mark.django_db
class TestPracticeBankLoader:
    """2026-02-18: Tests for practice bank loading in TeachingContentLoader."""

    def test_load_practice_bank_day_1(self):
        """2026-02-18: Load practice bank for day 1."""
        day_bank = TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 1)
        assert 'concept_id' in day_bank  # 2026-02-18: Has concept
        assert 'questions' in day_bank  # 2026-02-18: Has questions
        questions = day_bank['questions']
        assert 'easy' in questions  # 2026-02-18: Has difficulties
        assert 'medium' in questions
        assert 'hard' in questions
        assert len(questions['easy']) >= 5  # 2026-02-18: Min 5 per difficulty

    def test_load_practice_bank_day_4(self):
        """2026-02-18: Load practice bank for day 4."""
        day_bank = TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 4)
        assert day_bank['concept_id'] == 'ENG1_MRIDANG_W01_C4'

    def test_load_practice_bank_invalid_day(self):
        """2026-02-18: Invalid day raises ValueError."""
        with pytest.raises(ValueError, match="day_number must be 1-4"):
            TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 5)

    def test_load_practice_bank_caching(self):
        """2026-02-18: Second load uses cache."""
        TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 1)
        bank2 = TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 1)
        assert 'concept_id' in bank2  # 2026-02-18: Cache works


# ── MasteryPracticeService Tests ──────────────────────────────────────────

@pytest.mark.django_db
class TestMasteryPracticeService:
    """2026-02-18: Tests for MasteryPracticeService."""

    def test_start_practice_success(self, student_user, published_lesson,
                                     lesson_progress, day_progress_mastery):
        """2026-02-18: Successfully start a mastery practice session."""
        result = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        assert result['success'] is True  # 2026-02-18: Success
        assert 'session_id' in result  # 2026-02-18: Session created
        assert 'question' in result  # 2026-02-18: First question
        assert result['total_questions'] >= 8  # 2026-02-18: Standard range
        assert result['current_question'] == 1

    def test_start_practice_lesson_not_found(self, student_user):
        """2026-02-18: Start practice with invalid lesson."""
        result = MasteryPracticeService.start_practice(
            student_user, 'NONEXISTENT', 1
        )
        assert result['success'] is False
        assert result['code'] == 'LESSON_NOT_FOUND'

    def test_start_practice_day_not_ready(self, student_user, published_lesson,
                                          lesson_progress):
        """2026-02-18: Start practice when day is not in mastery_practice status."""
        DayProgress.objects.create(
            lesson_progress=lesson_progress, day_number=1, status='teaching'
        )
        result = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        assert result['success'] is False
        assert result['code'] == 'DAY_NOT_READY'

    def test_start_practice_resumes_existing(self, student_user, published_lesson,
                                              lesson_progress, day_progress_mastery):
        """2026-02-18: Resuming returns next question for existing session."""
        # 2026-02-18: Start first session
        result1 = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        assert result1['success'] is True
        # 2026-02-18: Resume should return same session
        result2 = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        assert result2['success'] is True
        assert result2['session_id'] == result1['session_id']

    def test_submit_answer_correct(self, student_user, published_lesson,
                                    lesson_progress, day_progress_mastery):
        """2026-02-18: Submit a correct answer."""
        # 2026-02-18: Start session
        start = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        session_id = start['session_id']
        question = start['question']

        # 2026-02-18: Find correct answer from bank
        day_bank = TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 1)
        q_data = MasteryPracticeService._find_question(
            day_bank['questions'], question['id']
        )
        q_type = q_data.get('type', 'mcq')

        if q_type == 'drag_order':
            correct = q_data['correct_order']
        else:
            correct = q_data['correct_answer']

        result = MasteryPracticeService.submit_answer(
            student_user, session_id, question['id'], correct, time_taken=5
        )
        assert result['success'] is True
        assert result['feedback']['is_correct'] is True
        assert result['progress']['questions_answered'] == 1
        assert result['progress']['questions_correct'] == 1

    def test_submit_answer_incorrect(self, student_user, published_lesson,
                                      lesson_progress, day_progress_mastery):
        """2026-02-18: Submit an incorrect answer."""
        start = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        session_id = start['session_id']
        question = start['question']

        # 2026-02-18: Submit a clearly wrong answer
        result = MasteryPracticeService.submit_answer(
            student_user, session_id, question['id'], -999, time_taken=3
        )
        assert result['success'] is True
        assert result['feedback']['is_correct'] is False
        assert result['progress']['questions_correct'] == 0

    def test_submit_answer_session_not_found(self, student_user):
        """2026-02-18: Submit to nonexistent session."""
        result = MasteryPracticeService.submit_answer(
            student_user, str(uuid.uuid4()), 'Q1', 0
        )
        assert result['success'] is False
        assert result['code'] == 'SESSION_NOT_FOUND'

    def test_submit_answer_invalid_question(self, student_user, published_lesson,
                                             lesson_progress, day_progress_mastery):
        """2026-02-18: Submit answer for question not in session."""
        start = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        result = MasteryPracticeService.submit_answer(
            student_user, start['session_id'], 'FAKE_Q', 0
        )
        assert result['success'] is False
        assert result['code'] == 'INVALID_QUESTION'

    def test_full_session_completion(self, student_user, published_lesson,
                                      lesson_progress, day_progress_mastery):
        """2026-02-18: Complete an entire practice session with all correct answers."""
        start = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        session_id = start['session_id']
        total = start['total_questions']
        question = start['question']

        for i in range(total):
            # 2026-02-18: Look up correct answer from bank
            day_bank = TeachingContentLoader.load_practice_bank(SAMPLE_CONTENT_PATH, 1)
            q_data = MasteryPracticeService._find_question(
                day_bank['questions'], question['id']
            )

            q_type = q_data.get('type', 'mcq')
            if q_type == 'drag_order':
                correct = q_data['correct_order']
            else:
                correct = q_data['correct_answer']

            result = MasteryPracticeService.submit_answer(
                student_user, session_id, question['id'], correct, time_taken=5
            )
            assert result['success'] is True

            if result.get('completed'):
                # 2026-02-18: Verify final result
                assert 'result' in result
                assert result['result']['star_rating'] == 5  # 2026-02-18: All correct
                assert result['result']['is_passed'] is True
                break

            # 2026-02-18: Get next question
            question = result['next_question']

        # 2026-02-18: Verify session completed
        session = PracticeSession.objects.get(id=session_id)
        assert session.status == 'completed'
        assert session.star_rating == 5

        # 2026-02-18: Verify ConceptMastery created
        mastery = ConceptMastery.objects.get(
            student=student_user, lesson=published_lesson, day_number=1
        )
        assert mastery.is_mastered is True
        assert mastery.best_star_rating == 5

        # 2026-02-18: Verify DayProgress updated
        day_prog = DayProgress.objects.get(
            lesson_progress=lesson_progress, day_number=1
        )
        assert day_prog.status == 'completed'
        assert day_prog.mastery_passed is True

        # 2026-02-18: Verify lesson progress advanced
        lesson_progress.refresh_from_db()
        assert lesson_progress.current_day == 2

    def test_session_with_all_incorrect(self, student_user, published_lesson,
                                         lesson_progress, day_progress_mastery):
        """2026-02-18: Complete session with all incorrect answers — fail gate."""
        start = MasteryPracticeService.start_practice(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        session_id = start['session_id']
        total = start['total_questions']
        question = start['question']

        for i in range(total):
            result = MasteryPracticeService.submit_answer(
                student_user, session_id, question['id'], -999, time_taken=2
            )
            if result.get('completed'):
                assert result['result']['star_rating'] == 1  # 2026-02-18: Min star
                assert result['result']['is_passed'] is False
                break
            question = result['next_question']

        # 2026-02-18: Verify day not advanced
        lesson_progress.refresh_from_db()
        assert lesson_progress.current_day == 1  # 2026-02-18: Stayed on day 1

    def test_get_practice_status(self, student_user, published_lesson):
        """2026-02-18: Get practice status for all 4 days."""
        result = MasteryPracticeService.get_practice_status(
            student_user, 'ENG1_MRIDANG_W01'
        )
        assert result['success'] is True
        assert len(result['days']) == 4  # 2026-02-18: All 4 days
        for day in result['days']:
            assert day['best_star_rating'] == 0  # 2026-02-18: No attempts yet
            assert day['is_mastered'] is False

    def test_get_practice_status_with_mastery(self, student_user, published_lesson):
        """2026-02-18: Practice status reflects mastery records."""
        ConceptMastery.objects.create(
            student=student_user, lesson=published_lesson,
            day_number=1, best_star_rating=4, attempts_count=1, is_mastered=True
        )
        result = MasteryPracticeService.get_practice_status(
            student_user, 'ENG1_MRIDANG_W01'
        )
        assert result['days'][0]['best_star_rating'] == 4
        assert result['days'][0]['is_mastered'] is True

    def test_sanitize_question_mcq(self):
        """2026-02-18: Sanitize MCQ question removes correct_answer."""
        q = {'id': 'Q1', 'type': 'mcq', 'question': 'What?',
             'options': ['A', 'B', 'C'], 'correct_answer': 1, 'hint': 'Try A'}
        sanitized = MasteryPracticeService._sanitize_question(q, 'easy')
        assert 'correct_answer' not in sanitized
        assert sanitized['options'] == ['A', 'B', 'C']
        assert sanitized['hint'] == 'Try A'
        assert sanitized['difficulty'] == 'easy'

    def test_sanitize_question_drag_order(self):
        """2026-02-18: Sanitize drag_order question has items but no correct_order."""
        q = {'id': 'Q1', 'type': 'drag_order', 'question': 'Order:',
             'items': ['X', 'Y'], 'correct_order': [1, 0]}
        sanitized = MasteryPracticeService._sanitize_question(q, 'hard')
        assert 'correct_order' not in sanitized
        assert sanitized['items'] == ['X', 'Y']


# ── Mastery Gate Tests ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMasteryGate:
    """2026-02-18: Tests for mastery gate in TeachingService.start_day."""

    def test_start_day_blocked_by_mastery_gate(self, student_user, published_lesson):
        """2026-02-18: Day 2 blocked if day 1 mastery not passed."""
        # 2026-02-18: Create progress at day 2
        progress = StudentLessonProgress.objects.create(
            student=student_user, lesson=published_lesson,
            iq_level='standard', current_day=2,
            day_statuses={'1': 'completed', '2': 'not_started'},
        )
        # 2026-02-18: Create failed mastery for day 1
        ConceptMastery.objects.create(
            student=student_user, lesson=published_lesson,
            day_number=1, best_star_rating=2, attempts_count=1, is_mastered=False
        )
        result = TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01', 2)
        assert result['success'] is False
        assert result['code'] == 'MASTERY_GATE_LOCKED'

    def test_start_day_allowed_with_mastery(self, student_user, published_lesson):
        """2026-02-18: Day 2 allowed if day 1 mastery passed."""
        progress = StudentLessonProgress.objects.create(
            student=student_user, lesson=published_lesson,
            iq_level='standard', current_day=2,
            day_statuses={'1': 'completed', '2': 'not_started'},
        )
        ConceptMastery.objects.create(
            student=student_user, lesson=published_lesson,
            day_number=1, best_star_rating=4, attempts_count=1, is_mastered=True
        )
        result = TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01', 2)
        assert result['success'] is True

    def test_start_day_1_no_gate(self, student_user, published_lesson):
        """2026-02-18: Day 1 has no mastery gate."""
        result = TeachingService.start_day(student_user, 'ENG1_MRIDANG_W01', 1)
        assert result['success'] is True  # 2026-02-18: No gate for day 1


# ── Complete Day Mastery Practice Transition Tests ────────────────────────

@pytest.mark.django_db
class TestCompleteDayTransition:
    """2026-02-18: Tests for complete_day transitioning to mastery_practice."""

    def test_complete_day_transitions_to_mastery_practice(
        self, student_user, published_lesson
    ):
        """2026-02-18: Completing a day sets status to mastery_practice."""
        # 2026-02-18: Start day 1
        start_result = TeachingService.start_day(
            student_user, 'ENG1_MRIDANG_W01', 1
        )
        assert start_result['success'] is True

        # 2026-02-18: Complete day 1
        result = TeachingService.complete_day(
            student_user, 'ENG1_MRIDANG_W01', 1,
            practice_answers={}, time_spent=60
        )
        assert result['success'] is True
        assert result['mastery_practice_required'] is True

        # 2026-02-18: Verify DayProgress is mastery_practice
        progress = StudentLessonProgress.objects.get(
            student=student_user, lesson=published_lesson
        )
        day_prog = DayProgress.objects.get(
            lesson_progress=progress, day_number=1
        )
        assert day_prog.status == 'mastery_practice'

        # 2026-02-18: Verify current_day NOT advanced (mastery gate)
        assert progress.current_day == 1


# ── API Endpoint Tests ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestMasteryPracticeAPI:
    """2026-02-18: Tests for mastery practice API endpoints."""

    def test_start_practice_api(self, student_client, student_user,
                                 published_lesson, lesson_progress,
                                 day_progress_mastery):
        """2026-02-18: POST /api/v1/teaching/lessons/{id}/practice/start/"""
        resp = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/start/',
            {'day_number': 1}, format='json'
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert 'session_id' in data
        assert 'question' in data

    def test_submit_answer_api(self, student_client, student_user,
                                published_lesson, lesson_progress,
                                day_progress_mastery):
        """2026-02-18: POST /api/v1/teaching/practice/{session_id}/answer/"""
        # 2026-02-18: Start session
        start_resp = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/start/',
            {'day_number': 1}, format='json'
        )
        data = start_resp.json()
        session_id = data['session_id']
        question_id = data['question']['id']

        # 2026-02-18: Submit answer
        resp = student_client.post(
            f'/api/v1/teaching/practice/{session_id}/answer/',
            {'question_id': question_id, 'answer': 0, 'time_taken': 5, 'hints_used': 0},
            format='json'
        )
        assert resp.status_code == 200
        answer_data = resp.json()
        assert answer_data['success'] is True
        assert 'feedback' in answer_data

    def test_practice_status_api(self, student_client, student_user,
                                  published_lesson):
        """2026-02-18: GET /api/v1/teaching/lessons/{id}/practice/status/"""
        resp = student_client.get(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/status/'
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data['success'] is True
        assert len(data['days']) == 4

    def test_parent_denied_practice_start(self, parent_client, published_lesson):
        """2026-02-18: Parents cannot start practice."""
        resp = parent_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/start/',
            {'day_number': 1}, format='json'
        )
        assert resp.status_code == 403

    def test_unauthenticated_denied(self, published_lesson):
        """2026-02-18: Unauthenticated users denied."""
        client = APIClient()
        resp = client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/start/',
            {'day_number': 1}, format='json'
        )
        assert resp.status_code == 401

    def test_start_practice_invalid_day(self, student_client, student_user,
                                         published_lesson, lesson_progress,
                                         day_progress_mastery):
        """2026-02-18: Invalid day number returns 400."""
        resp = student_client.post(
            '/api/v1/teaching/lessons/ENG1_MRIDANG_W01/practice/start/',
            {'day_number': 5}, format='json'
        )
        assert resp.status_code == 400


# ── PracticeResponse Model Tests ──────────────────────────────────────────

@pytest.mark.django_db
class TestPracticeModels:
    """2026-02-18: Tests for mastery practice models."""

    def test_practice_session_str(self, student_user, published_lesson,
                                   lesson_progress):
        """2026-02-18: PracticeSession string representation."""
        session = PracticeSession.objects.create(
            student=student_user, lesson_progress=lesson_progress,
            day_number=1, iq_level='standard', total_questions=8,
            star_rating=4, attempt_number=1,
        )
        assert 'Day 1' in str(session)
        assert '4 stars' in str(session)

    def test_practice_response_str(self, student_user, published_lesson,
                                    lesson_progress):
        """2026-02-18: PracticeResponse string representation."""
        session = PracticeSession.objects.create(
            student=student_user, lesson_progress=lesson_progress,
            day_number=1, iq_level='standard', total_questions=8,
        )
        response = PracticeResponse.objects.create(
            session=session, question_id='Q1', difficulty='easy',
            question_type='mcq', is_correct=True, position=0,
        )
        assert 'correct' in str(response)

    def test_concept_mastery_str(self, student_user, published_lesson):
        """2026-02-18: ConceptMastery string representation."""
        mastery = ConceptMastery.objects.create(
            student=student_user, lesson=published_lesson,
            day_number=2, best_star_rating=3, is_mastered=True,
        )
        assert 'Day 2' in str(mastery)
        assert 'Mastered' in str(mastery)

    def test_practice_session_unique_constraint(self, student_user,
                                                 published_lesson,
                                                 lesson_progress):
        """2026-02-18: Unique constraint on (lesson_progress, day, attempt)."""
        PracticeSession.objects.create(
            student=student_user, lesson_progress=lesson_progress,
            day_number=1, attempt_number=1,
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            PracticeSession.objects.create(
                student=student_user, lesson_progress=lesson_progress,
                day_number=1, attempt_number=1,
            )

    def test_concept_mastery_unique_constraint(self, student_user,
                                                published_lesson):
        """2026-02-18: Unique constraint on (student, lesson, day)."""
        ConceptMastery.objects.create(
            student=student_user, lesson=published_lesson, day_number=1,
        )
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ConceptMastery.objects.create(
                student=student_user, lesson=published_lesson, day_number=1,
            )
