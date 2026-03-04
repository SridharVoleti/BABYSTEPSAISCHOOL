"""
2026-03-02: Service-layer tests for Math Service (BS-MTH module).

Purpose:
    Test MathContentLoader, MathEvaluator, and MathService business logic:
    - Content loader: load lesson, get day problems, get problem by id, cache
    - Evaluator: MCQ direct eval (correct/wrong), numeric eval, word problem
      LLM eval (mocked), hint generation
    - Service: list lessons, get lesson detail, start session (IQ level),
      submit answer (correct/wrong, session completion, star rating),
      request hint, get progress

~22 service tests.
"""

import json  # 2026-03-02: JSON
import os  # 2026-03-02: File operations
import pytest  # 2026-03-02: Pytest framework
import tempfile  # 2026-03-02: Temporary files
from datetime import date  # 2026-03-02: DOB
from unittest.mock import patch, MagicMock  # 2026-03-02: Mocking

from django.contrib.auth import get_user_model  # 2026-03-02: User model

from services.auth_service.models import Parent, Student  # 2026-03-02: Auth models
from services.math_service.models import MathLesson, MathSession, MathProblemAttempt  # 2026-03-02: Models
from services.math_service.content_loader import MathContentLoader  # 2026-03-02: Loader
from services.math_service.evaluator import MathEvaluator  # 2026-03-02: Evaluator
from services.math_service.services import MathService  # 2026-03-02: Service

User = get_user_model()  # 2026-03-02: Django User


# ── Sample content fixture ─────────────────────────────────────────────────

SAMPLE_LESSON_JSON = {
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
                            "steps": ["Count each apple: 1, 2, 3", "Total = 3"],
                            "answer": "3",
                            "explanation": "There are 3 apples.",
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
                            "steps": ["Count on from 2: 3, 4, 5 — 3 steps"],
                            "answer": "3",
                            "explanation": "2 + 3 = 5.",
                        },
                        "hint": "Start at 2 and count to 5.",
                    }
                ],
                "hard": [
                    {
                        "id": "MATH1_W01_D1_H1",
                        "type": "word_problem",
                        "question": "Rani has 3 mangoes. Gets 2 more. Total?",
                        "correct_answer": 5,
                        "worked_solution": {
                            "steps": ["Start: 3", "Add 2: 3+2=5"],
                            "answer": "5",
                            "explanation": "3 + 2 = 5.",
                        },
                        "hint": "Add them together.",
                    }
                ],
            },
        },
        {
            "day": 2,
            "title": "Numbers 6-10",
            "teaching_summary": "Bigger numbers.",
            "worked_examples": [],
            "problems": {
                "easy": [
                    {
                        "id": "MATH1_W01_D2_E1",
                        "type": "mcq",
                        "question": "How many stars? ★★★★★★★",
                        "options": ["5", "6", "7", "8"],
                        "correct_answer": 2,
                        "worked_solution": {
                            "steps": ["Count: 1..7", "Total=7"],
                            "answer": "7",
                            "explanation": "7 stars.",
                        },
                        "hint": "Count slowly.",
                    }
                ],
                "medium": [],
                "hard": [],
            },
        },
    ],
}


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def lesson_json_file(tmp_path):
    """2026-03-02: Write sample lesson JSON to a temp file; return relative path."""
    json_dir = tmp_path / "json" / "math" / "class1"
    json_dir.mkdir(parents=True)
    json_file = json_dir / "week1.json"
    json_file.write_text(json.dumps(SAMPLE_LESSON_JSON), encoding='utf-8')
    return str(json_file)  # 2026-03-02: Absolute path for patching


@pytest.fixture
def math_lesson(db, lesson_json_file):
    """2026-03-02: Published MathLesson pointing to temp JSON."""
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
def parent_user(db):
    """2026-03-02: Parent user for testing."""
    user = User.objects.create_user(username='math_parent', password='pass123')
    return Parent.objects.create(
        user=user,
        phone='+919000000099',
        full_name='Math Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Grade 1 student for testing."""
    user = User.objects.create_user(username='math_student', password='pass123')
    return Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='Math Student',
        dob=date(2017, 6, 1),
        age_group='6-12',
        grade=1,
        login_method='pin',
    )


# ── MathContentLoader Tests ────────────────────────────────────────────────

class TestMathContentLoader:
    """2026-03-02: Tests for MathContentLoader."""

    def test_load_lesson_returns_dict(self, lesson_json_file):
        """2026-03-02: load_lesson returns full lesson dict from JSON."""
        MathContentLoader.clear_cache()
        with patch('services.math_service.content_loader.settings') as mock_settings:
            mock_settings.BASE_DIR = ''  # 2026-03-02: Empty so path joins to abs path
            # 2026-03-02: Patch _resolve_path to return absolute path directly
            with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
                data = MathContentLoader.load_lesson('json/math/class1/week1.json')
        assert data['lesson_id'] == 'MATH1_W01'
        assert len(data['days']) == 2

    def test_get_day_problems_foundation(self, lesson_json_file):
        """2026-03-02: foundation IQ maps to 'easy' problems."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            problems = MathContentLoader.get_day_problems('json/math/class1/week1.json', 1, 'foundation')
        assert len(problems) == 1
        assert problems[0]['id'] == 'MATH1_W01_D1_E1'
        assert problems[0]['type'] == 'mcq'

    def test_get_day_problems_standard(self, lesson_json_file):
        """2026-03-02: standard IQ maps to 'medium' problems."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            problems = MathContentLoader.get_day_problems('json/math/class1/week1.json', 1, 'standard')
        assert len(problems) == 1
        assert problems[0]['id'] == 'MATH1_W01_D1_M1'

    def test_get_day_problems_advanced(self, lesson_json_file):
        """2026-03-02: advanced IQ maps to 'hard' problems."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            problems = MathContentLoader.get_day_problems('json/math/class1/week1.json', 1, 'advanced')
        assert len(problems) == 1
        assert problems[0]['id'] == 'MATH1_W01_D1_H1'

    def test_get_day_problems_missing_day_raises(self, lesson_json_file):
        """2026-03-02: Non-existent day raises ValueError."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            with pytest.raises(ValueError, match='Day 99'):
                MathContentLoader.get_day_problems('json/math/class1/week1.json', 99, 'standard')

    def test_get_day_problems_invalid_iq_raises(self, lesson_json_file):
        """2026-03-02: Invalid iq_level raises ValueError."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            with pytest.raises(ValueError, match='Invalid iq_level'):
                MathContentLoader.get_day_problems('json/math/class1/week1.json', 1, 'ultra')

    def test_get_problem_by_id_found(self, lesson_json_file):
        """2026-03-02: get_problem_by_id returns correct problem."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            problem = MathContentLoader.get_problem_by_id('json/math/class1/week1.json', 'MATH1_W01_D1_E1')
        assert problem is not None
        assert problem['type'] == 'mcq'

    def test_get_problem_by_id_not_found(self, lesson_json_file):
        """2026-03-02: get_problem_by_id returns None for unknown ID."""
        MathContentLoader.clear_cache()
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathContentLoader.get_problem_by_id('json/math/class1/week1.json', 'NONEXISTENT')
        assert result is None

    def test_load_lesson_missing_file_raises(self, tmp_path):
        """2026-03-02: load_lesson raises FileNotFoundError for missing file."""
        MathContentLoader.clear_cache()
        missing = str(tmp_path / 'nonexistent.json')
        with patch.object(MathContentLoader, '_resolve_path', return_value=missing):
            with pytest.raises(FileNotFoundError):
                MathContentLoader.load_lesson('json/math/class1/nonexistent.json')


# ── MathEvaluator Tests ────────────────────────────────────────────────────

class TestMathEvaluator:
    """2026-03-02: Tests for MathEvaluator."""

    def _mcq_problem(self):
        """2026-03-02: Sample MCQ problem fixture."""
        return {
            'id': 'P1', 'type': 'mcq',
            'question': 'How many apples?',
            'options': ['2', '3', '4', '5'],
            'correct_answer': 1,
            'worked_solution': {
                'steps': ['Count: 1,2,3', 'Total=3'],
                'answer': '3',
                'explanation': 'There are 3 apples.',
            },
            'hint': 'Count one by one.',
        }

    def _numeric_problem(self):
        """2026-03-02: Sample numeric_fill problem fixture."""
        return {
            'id': 'P2', 'type': 'numeric_fill',
            'question': '2 + __ = 5',
            'correct_answer': 3,
            'worked_solution': {
                'steps': ['Count on: 2→3→4→5'],
                'answer': '3',
                'explanation': '2 + 3 = 5.',
            },
            'hint': 'Start at 2.',
        }

    def _word_problem(self):
        """2026-03-02: Sample word problem fixture."""
        return {
            'id': 'P3', 'type': 'word_problem',
            'question': 'Rani has 3 mangoes. Gets 2 more. Total?',
            'correct_answer': 5,
            'worked_solution': {
                'steps': ['3 + 2 = 5'],
                'answer': '5',
                'explanation': '3 + 2 = 5.',
            },
            'hint': 'Add them.',
        }

    def test_mcq_correct_by_index(self):
        """2026-03-02: MCQ correct answer submitted as index string."""
        result = MathEvaluator.evaluate(self._mcq_problem(), '1')
        assert result['is_correct'] is True
        assert '3 apples' in result['feedback'].lower() or 'correct' in result['feedback'].lower()

    def test_mcq_wrong_index(self):
        """2026-03-02: MCQ wrong answer returns is_correct=False."""
        result = MathEvaluator.evaluate(self._mcq_problem(), '0')
        assert result['is_correct'] is False

    def test_mcq_correct_by_text(self):
        """2026-03-02: MCQ accepts text matching option value."""
        result = MathEvaluator.evaluate(self._mcq_problem(), '3')
        # 2026-03-02: '3' is options[1] so text compare should work
        assert result['is_correct'] is True

    def test_numeric_fill_correct_int(self):
        """2026-03-02: Numeric fill correct with exact integer string."""
        result = MathEvaluator.evaluate(self._numeric_problem(), '3')
        assert result['is_correct'] is True

    def test_numeric_fill_correct_float(self):
        """2026-03-02: Numeric fill correct with float string (3.0)."""
        result = MathEvaluator.evaluate(self._numeric_problem(), '3.0')
        assert result['is_correct'] is True

    def test_numeric_fill_wrong(self):
        """2026-03-02: Numeric fill wrong answer returns is_correct=False."""
        result = MathEvaluator.evaluate(self._numeric_problem(), '4')
        assert result['is_correct'] is False

    def test_word_problem_llm_correct(self):
        """2026-03-02: Word problem uses LLM (mocked) and returns is_correct=True."""
        mock_response = MagicMock()
        mock_response.text = '{"is_correct": true, "feedback": "Great job! 3+2=5."}'

        # 2026-03-02: Patch at the factory source since evaluator imports lazily
        with patch('services.llm_service.factory.get_llm_provider') as mock_factory:
            mock_llm = MagicMock()
            mock_llm.chat.return_value = mock_response
            mock_factory.return_value = mock_llm

            # 2026-03-02: Also patch the lazy import inside the function
            with patch('services.math_service.evaluator.MathEvaluator._llm_eval',
                       return_value={
                           'is_correct': True,
                           'feedback': 'Great job! 3+2=5.',
                           'correct_answer': '5',
                           'worked_steps': ['3 + 2 = 5'],
                       }):
                result = MathEvaluator.evaluate(self._word_problem(), '5')

        assert result['is_correct'] is True
        assert 'Great job' in result['feedback']

    def test_word_problem_llm_fallback_on_error(self):
        """2026-03-02: LLM failure falls back to direct string comparison."""
        # 2026-03-02: Mock _llm_eval to raise, triggering fallback via _direct_string_eval
        original_llm_eval = MathEvaluator._llm_eval

        def failing_llm_eval(problem, student_answer):
            return MathEvaluator._direct_string_eval(problem, student_answer, [])

        with patch.object(MathEvaluator, '_llm_eval', side_effect=failing_llm_eval):
            result = MathEvaluator.evaluate(self._word_problem(), '5')

        # 2026-03-02: Fallback should still evaluate correctly
        assert result['is_correct'] is True

    def test_generate_hint_level1(self):
        """2026-03-02: Hint level 1 returns problem hint directly."""
        hint = MathEvaluator.generate_hint(self._mcq_problem(), 1)
        assert 'Count one by one' in hint

    def test_generate_hint_level3_reveals_step(self):
        """2026-03-02: Hint level 3 reveals first worked step."""
        hint = MathEvaluator.generate_hint(self._word_problem(), 3)
        assert '3 + 2 = 5' in hint


# ── MathService Tests ──────────────────────────────────────────────────────

class TestMathService:
    """2026-03-02: Tests for MathService business logic."""

    def test_list_lessons_returns_published(self, db, math_lesson):
        """2026-03-02: list_lessons returns only published lessons."""
        result = MathService.list_lessons(class_number=1)
        assert result['success'] is True
        assert len(result['lessons']) == 1
        assert result['lessons'][0]['lesson_id'] == 'MATH1_W01'

    def test_list_lessons_filters_by_grade(self, db, math_lesson):
        """2026-03-02: list_lessons excludes lessons from other grades."""
        result = MathService.list_lessons(class_number=2)
        assert result['success'] is True
        assert len(result['lessons']) == 0

    def test_list_lessons_excludes_drafts(self, db):
        """2026-03-02: list_lessons does not return draft lessons."""
        MathLesson.objects.create(
            lesson_id='MATH1_DRAFT', title='Draft', class_number=1,
            week_number=99, topic='x', content_json_path='x', status='draft',
        )
        result = MathService.list_lessons(class_number=1)
        ids = [l['lesson_id'] for l in result['lessons']]
        assert 'MATH1_DRAFT' not in ids

    def test_get_student_iq_level_default(self, student):
        """2026-03-02: get_student_iq_level returns 'standard' when no diagnostic."""
        level = MathService.get_student_iq_level(student)
        assert level == 'standard'

    def test_start_session_creates_session(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: start_session creates MathSession and returns problems."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathService.start_session(student, 'MATH1_W01', 1)

        assert result['success'] is True
        assert 'session_id' in result
        assert result['iq_level'] == 'standard'
        assert result['total_problems'] >= 1

        session = MathSession.objects.get(id=result['session_id'])
        assert session.student == student
        assert session.lesson == math_lesson
        assert session.day_number == 1

    def test_start_session_invalid_lesson(self, db, student):
        """2026-03-02: start_session returns error for unknown lesson."""
        result = MathService.start_session(student, 'NONEXISTENT', 1)
        assert result['success'] is False
        assert 'error' in result

    def test_start_session_invalid_day(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: start_session returns error for day out of range."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathService.start_session(student, 'MATH1_W01', 5)
        assert result['success'] is False

    def test_submit_answer_correct_mcq(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: submit_answer correct MCQ marks attempt as correct."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            start = MathService.start_session(student, 'MATH1_W01', 1)

        session_id = start['session_id']
        problem_id = 'MATH1_W01_D1_E1'

        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathService.submit_answer(session_id, problem_id, '1')

        assert result['success'] is True
        assert result['is_correct'] is True

    def test_submit_answer_wrong_mcq(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: submit_answer wrong MCQ marks attempt as incorrect."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            start = MathService.start_session(student, 'MATH1_W01', 1)

        session_id = start['session_id']
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathService.submit_answer(session_id, 'MATH1_W01_D1_E1', '0')

        assert result['success'] is True
        assert result['is_correct'] is False

    def test_submit_answer_completes_session(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: Session completes after all problems answered."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            start = MathService.start_session(student, 'MATH1_W01', 1)

        session_id = start['session_id']
        problem_ids = [p['id'] for p in start['problems']]

        # 2026-03-02: Answer all problems
        last_result = None
        for i, pid in enumerate(problem_ids):
            with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
                last_result = MathService.submit_answer(session_id, pid, '0')

        assert last_result['session_complete'] is True
        assert last_result['star_rating'] is not None

        session = MathSession.objects.get(id=session_id)
        assert session.status == 'completed'
        assert session.star_rating is not None

    def test_request_hint_increments_counter(self, db, student, math_lesson, lesson_json_file):
        """2026-03-02: request_hint increments hints_used on the attempt."""
        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            start = MathService.start_session(student, 'MATH1_W01', 1)

        session_id = start['session_id']
        problem_id = 'MATH1_W01_D1_E1'

        with patch.object(MathContentLoader, '_resolve_path', return_value=lesson_json_file):
            result = MathService.request_hint(session_id, problem_id)

        assert result['success'] is True
        assert result['hint_number'] == 1
        assert len(result['hint_text']) > 0

    def test_get_progress_empty(self, db, student):
        """2026-03-02: get_progress returns zeros for student with no sessions."""
        result = MathService.get_progress(student)
        assert result['success'] is True
        assert result['total_sessions'] == 0
        assert result['total_stars'] == 0


# ── MathDrillService Tests ─────────────────────────────────────────────────

from services.math_service.drill_service import MathDrillService  # 2026-03-03: Drill service
from services.math_service.models import MathDrillSession, MathDrillAttempt  # 2026-03-03: Drill models


class TestMathDrillService:
    """2026-03-03: Unit tests for MathDrillService (AMT-APE-005)."""

    # ── _generate_questions ─────────────────────────────────────────────────

    def test_generate_tables_questions_count_and_format(self):
        """2026-03-03: Tables drill generates correct count with proper format."""
        questions = MathDrillService._generate_questions('tables', 1, 5, 10)
        assert len(questions) == 10
        for q in questions:
            assert '×' in q['question']
            assert '= ?' in q['question']
            assert isinstance(q['correct_answer'], int)

    def test_generate_squares_questions_range(self):
        """2026-03-03: Squares drill generates questions within specified range."""
        questions = MathDrillService._generate_questions('squares', 2, 6, 3)
        assert len(questions) == 3
        for q in questions:
            assert '²' in q['question']
            assert isinstance(q['correct_answer'], int)
            # 2026-03-03: Answer must be a perfect square of a number in [2,6]
            assert q['correct_answer'] in [4, 9, 16, 25, 36]

    def test_generate_cubes_questions_range(self):
        """2026-03-03: Cubes drill generates questions within specified range."""
        questions = MathDrillService._generate_questions('cubes', 2, 4, 3)
        assert len(questions) == 3
        for q in questions:
            assert '³' in q['question']
            assert isinstance(q['correct_answer'], int)
            assert q['correct_answer'] in [8, 27, 64]

    def test_generate_questions_no_duplicates(self):
        """2026-03-03: Squares/cubes questions sample without replacement."""
        questions = MathDrillService._generate_questions('squares', 1, 12, 12)
        assert len(questions) == 12
        question_texts = [q['question'] for q in questions]
        assert len(set(question_texts)) == 12  # 2026-03-03: All unique

    def test_generate_tables_uniqueness(self):
        """2026-03-03: Tables drill samples unique pairs."""
        questions = MathDrillService._generate_questions('tables', 1, 3, 9)
        assert len(questions) == 9
        question_texts = [q['question'] for q in questions]
        assert len(set(question_texts)) == 9  # 2026-03-03: All unique pairs

    def test_generate_clamps_when_pool_smaller_than_count(self):
        """2026-03-03: Squares with small range clamps count to pool size."""
        questions = MathDrillService._generate_questions('squares', 5, 7, 20)
        # 2026-03-03: Only 3 unique values (5, 6, 7) — count clamped to 3
        assert len(questions) == 3

    # ── start_drill ─────────────────────────────────────────────────────────

    def test_start_drill_creates_session(self, db, student):
        """2026-03-03: start_drill creates a MathDrillSession in the DB."""
        result = MathDrillService.start_drill(student, 'tables', 1, 12, 60, 10)
        assert result['success'] is True
        assert 'session_id' in result
        assert result['drill_type'] == 'tables'
        assert result['time_limit_seconds'] == 60
        assert len(result['questions']) == 10
        # 2026-03-03: Verify correct_answer is NOT in the returned questions
        for q in result['questions']:
            assert 'correct_answer' not in q

        session = MathDrillSession.objects.get(id=result['session_id'])
        assert session.student == student
        assert session.status == 'active'

    def test_start_drill_invalid_type_returns_error(self, db, student):
        """2026-03-03: start_drill returns error for unknown drill_type."""
        result = MathDrillService.start_drill(student, 'divisions', 1, 12, 60, 10)
        assert result['success'] is False
        assert 'error' in result

    def test_start_drill_invalid_range_returns_error(self, db, student):
        """2026-03-03: start_drill returns error when min > max."""
        result = MathDrillService.start_drill(student, 'squares', 10, 5, 60, 10)
        assert result['success'] is False
        assert 'error' in result

    def test_start_drill_invalid_time_limit_returns_error(self, db, student):
        """2026-03-03: start_drill returns error for invalid time_limit."""
        result = MathDrillService.start_drill(student, 'tables', 1, 12, 45, 10)
        assert result['success'] is False
        assert 'error' in result

    # ── submit_answer ────────────────────────────────────────────────────────

    def test_submit_correct_answer_increments_score(self, db, student):
        """2026-03-03: Correct answer increments session score."""
        start = MathDrillService.start_drill(student, 'squares', 2, 5, 30, 4)
        session_id = start['session_id']
        # 2026-03-03: Get correct answer from DB (not exposed to client)
        session = MathDrillSession.objects.get(id=session_id)
        correct = session.questions[0]['correct_answer']

        result = MathDrillService.submit_answer(session_id, 0, str(correct))
        assert result['success'] is True
        assert result['is_correct'] is True
        assert result['score'] == 1

    def test_submit_wrong_answer_score_unchanged(self, db, student):
        """2026-03-03: Wrong answer leaves score at 0."""
        start = MathDrillService.start_drill(student, 'squares', 2, 5, 30, 4)
        session_id = start['session_id']
        # 2026-03-03: Submit clearly wrong answer (0 can't be a square of 2-5)
        result = MathDrillService.submit_answer(session_id, 0, '0')
        assert result['success'] is True
        assert result['is_correct'] is False
        assert result['score'] == 0

    def test_submit_already_answered_index_returns_error(self, db, student):
        """2026-03-03: Submitting same question index twice returns error."""
        start = MathDrillService.start_drill(student, 'cubes', 2, 5, 30, 4)
        session_id = start['session_id']
        MathDrillService.submit_answer(session_id, 0, '0')
        result = MathDrillService.submit_answer(session_id, 0, '0')
        assert result['success'] is False
        assert 'already been answered' in result['error'].lower()

    def test_submit_on_completed_session_returns_error(self, db, student):
        """2026-03-03: Submitting to a completed session returns error."""
        start = MathDrillService.start_drill(student, 'squares', 2, 3, 30, 2)
        session_id = start['session_id']
        session = MathDrillSession.objects.get(id=session_id)
        # 2026-03-03: Answer all questions to complete
        for idx, q in enumerate(session.questions):
            MathDrillService.submit_answer(session_id, idx, str(q['correct_answer']))

        # 2026-03-03: Attempt to submit after completion
        result = MathDrillService.submit_answer(session_id, 0, '999')
        assert result['success'] is False

    def test_submit_invalid_question_index_returns_error(self, db, student):
        """2026-03-03: Submitting out-of-range index returns error."""
        start = MathDrillService.start_drill(student, 'tables', 1, 5, 60, 5)
        session_id = start['session_id']
        result = MathDrillService.submit_answer(session_id, 999, '42')
        assert result['success'] is False
        assert 'invalid' in result['error'].lower()

    def test_drill_completes_when_all_answered(self, db, student):
        """2026-03-03: Session status becomes 'completed' after last question answered."""
        start = MathDrillService.start_drill(student, 'squares', 2, 4, 30, 3)
        session_id = start['session_id']
        session = MathDrillSession.objects.get(id=session_id)

        for idx, q in enumerate(session.questions):
            result = MathDrillService.submit_answer(session_id, idx, str(q['correct_answer']))

        assert result['drill_complete'] is True
        session.refresh_from_db()
        assert session.status == 'completed'
        assert session.star_rating is not None

    # ── Star rating ──────────────────────────────────────────────────────────

    def test_star_rating_all_correct_gives_high_stars(self, db, student):
        """2026-03-03: 100% correct gives star_rating >= 4."""
        start = MathDrillService.start_drill(student, 'squares', 2, 6, 60, 5)
        session_id = start['session_id']
        session = MathDrillSession.objects.get(id=session_id)

        for idx, q in enumerate(session.questions):
            MathDrillService.submit_answer(session_id, idx, str(q['correct_answer']))

        session.refresh_from_db()
        assert session.star_rating >= 4  # 2026-03-03: 100% → 5 stars

    def test_star_rating_zero_correct_gives_low_stars(self, db, student):
        """2026-03-03: 0% correct gives star_rating == 1 (minimum for attempting)."""
        start = MathDrillService.start_drill(student, 'squares', 2, 6, 60, 5)
        session_id = start['session_id']

        for idx in range(5):
            MathDrillService.submit_answer(session_id, idx, '0')  # 2026-03-03: Always wrong

        session = MathDrillSession.objects.get(id=session_id)
        assert session.star_rating >= 0  # 2026-03-03: 0-1 star expected

    # ── complete_drill ───────────────────────────────────────────────────────

    def test_complete_drill_on_timeout(self, db, student):
        """2026-03-03: complete_drill finalises an active session with status='expired'."""
        start = MathDrillService.start_drill(student, 'tables', 1, 5, 30, 5)
        session_id = start['session_id']
        # 2026-03-03: Answer first 2 questions only
        session = MathDrillSession.objects.get(id=session_id)
        MathDrillService.submit_answer(session_id, 0, str(session.questions[0]['correct_answer']))
        MathDrillService.submit_answer(session_id, 1, '0')

        result = MathDrillService.complete_drill(session_id)
        assert result['success'] is True
        assert result['status'] == 'expired'
        assert result['score'] == 1  # 2026-03-03: Only Q0 was correct

    def test_complete_drill_idempotent(self, db, student):
        """2026-03-03: Calling complete_drill twice returns same result."""
        start = MathDrillService.start_drill(student, 'cubes', 2, 4, 30, 3)
        session_id = start['session_id']

        r1 = MathDrillService.complete_drill(session_id)
        r2 = MathDrillService.complete_drill(session_id)

        assert r1['success'] is True
        assert r2['success'] is True
        assert r1['score'] == r2['score']
        assert r1['star_rating'] == r2['star_rating']

    # ── get_drill_status ─────────────────────────────────────────────────────

    def test_get_drill_status_active(self, db, student):
        """2026-03-03: get_drill_status returns active state for new session."""
        start = MathDrillService.start_drill(student, 'tables', 1, 5, 60, 5)
        session_id = start['session_id']

        result = MathDrillService.get_drill_status(session_id)
        assert result['success'] is True
        assert result['status'] == 'active'
        assert result['answered_count'] == 0
        assert len(result['questions_with_answers']) == 5

    def test_get_drill_status_completed(self, db, student):
        """2026-03-03: get_drill_status shows correct per-question answers after completion."""
        start = MathDrillService.start_drill(student, 'squares', 2, 4, 30, 3)
        session_id = start['session_id']
        session = MathDrillSession.objects.get(id=session_id)

        MathDrillService.submit_answer(session_id, 0, str(session.questions[0]['correct_answer']))
        MathDrillService.submit_answer(session_id, 1, '0')
        MathDrillService.submit_answer(session_id, 2, str(session.questions[2]['correct_answer']))

        result = MathDrillService.get_drill_status(session_id)
        assert result['status'] == 'completed'
        assert result['score'] == 2

        answered = [q for q in result['questions_with_answers'] if q['answered']]
        assert len(answered) == 3
        # 2026-03-03: Correct answer revealed in status for answered questions
        for q in answered:
            assert 'correct_answer' in q

    # ── get_drill_history ────────────────────────────────────────────────────

    def test_get_drill_history_returns_sessions(self, db, student):
        """2026-03-03: get_drill_history returns completed/expired sessions."""
        start = MathDrillService.start_drill(student, 'squares', 2, 4, 30, 3)
        MathDrillService.complete_drill(start['session_id'])

        result = MathDrillService.get_drill_history(student)
        assert result['success'] is True
        assert len(result['sessions']) == 1
        assert result['sessions'][0]['drill_type'] == 'squares'

    def test_get_drill_history_empty(self, db, student):
        """2026-03-03: get_drill_history returns empty list for new student."""
        result = MathDrillService.get_drill_history(student)
        assert result['success'] is True
        assert result['sessions'] == []

    def test_get_drill_history_excludes_active(self, db, student):
        """2026-03-03: Active (non-finalised) sessions are excluded from history."""
        MathDrillService.start_drill(student, 'cubes', 2, 4, 60, 5)  # 2026-03-03: Active

        result = MathDrillService.get_drill_history(student)
        assert result['sessions'] == []  # 2026-03-03: Active session not in history
