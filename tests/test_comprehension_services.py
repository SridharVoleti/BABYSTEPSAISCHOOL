"""
2026-02-19: Tests for the Comprehension Capture Engine service layer (BS-CMP).

Purpose:
    Verify parroting detection, LLM evaluation, weighted formula, and
    ComprehensionService business logic including DayProgress updates.
"""

import math  # 2026-02-19: math.ceil
import pytest  # 2026-02-19: Pytest framework
from datetime import date  # 2026-02-19: Date for DOB
from unittest.mock import patch, MagicMock  # 2026-02-19: Mocking

from django.contrib.auth import get_user_model  # 2026-02-19: User model

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import (  # 2026-02-19: Teaching models
    TeachingLesson, StudentLessonProgress, DayProgress,
)
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-02-19: Loader
from services.comprehension_service.parroting import extract_nouns, is_parroting  # 2026-02-19: Parroting
from services.comprehension_service.services import ComprehensionService  # 2026-02-19: Service
from services.comprehension_service import evaluator as evaluator_module  # 2026-02-21: Evaluator module

User = get_user_model()  # 2026-02-19: Django User model

SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'  # 2026-02-19: Test content path

# 2026-02-19: Mock LLM scores used across multiple tests
MOCK_EVAL_SCORES = {
    'understanding': 85,
    'accuracy': 80,
    'own_words': 75,
    'depth': 70,
    'clarity': 80,
    'feedback': 'Great explanation!',
    'llm_error': False,
}

# 2026-02-19: Patch target for evaluate_explanation
EVAL_PATCH = 'services.comprehension_service.services.evaluate_explanation'
CONTENT_PATCH = 'services.comprehension_service.services.TeachingContentLoader.get_day_content'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-19: Create a parent user."""
    user = User.objects.create_user(username='cmp_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user,
        phone='+919876543210',
        full_name='CMP Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-19: Create a student user."""
    user = User.objects.create_user(username='cmp_student', password='testpass123')
    student = Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='CMP Student',
        dob=date(2019, 5, 15),
        age_group='6-12',
        grade=1,
        login_method='pin',
    )
    return student


@pytest.fixture
def published_lesson(db):
    """2026-02-19: Create a published teaching lesson."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_CMP_W01',
        title='The Wise Owl - CMP Test',
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
    """2026-02-19: Create lesson progress in comprehension_check status."""
    progress = StudentLessonProgress.objects.create(
        student=student_user,
        lesson=published_lesson,
        iq_level='standard',
        current_day=1,
        day_statuses={
            '1': 'comprehension_check',
            '2': 'not_started',
            '3': 'not_started',
            '4': 'not_started',
            '5': 'not_started',
        },
    )
    return progress


@pytest.fixture
def day_progress_comprehension(lesson_progress, db):
    """2026-02-19: Create DayProgress in comprehension_check status."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=1,
        status='comprehension_check',
        mastery_star_rating=4,
        mastery_passed=True,
        practice_score=80,
    )


@pytest.fixture(autouse=True)
def clear_cache():
    """2026-02-19: Clear content cache before/after each test."""
    TeachingContentLoader.clear_cache()
    yield
    TeachingContentLoader.clear_cache()


# ── Parroting Tests ────────────────────────────────────────────────────────

class TestParrotingDetector:
    """2026-02-19: Tests for the anti-parroting detector."""

    def test_parroting_detects_high_overlap(self):
        """2026-02-19: ≥70% noun overlap should return True."""
        lesson_text = (
            'Ollie the owl lives in a forest and watches animals from a high branch '
            'every night. Ollie is wise because Ollie thinks carefully before speaking.'
        )
        # 2026-02-19: Near-verbatim copy including thinks, carefully, speaking, before
        student_text = (
            'Ollie the owl lives in a forest and watches animals from a high branch '
            'every night. Ollie thinks carefully before speaking and is very wise.'
        )
        assert is_parroting(student_text, lesson_text) is True

    def test_parroting_allows_own_words(self):
        """2026-02-19: <70% overlap should return False."""
        lesson_text = (
            'Ollie the owl lives in a forest and watches animals from a high branch '
            'every night. Ollie is wise because Ollie thinks carefully before speaking.'
        )
        # 2026-02-19: Different vocabulary — owl lives alone, sleeps during day
        student_text = 'Owls sleep during daytime and hunt mice at night using silent wings.'
        assert is_parroting(student_text, lesson_text) is False

    def test_parroting_empty_lesson_text(self):
        """2026-02-19: Empty lesson text should never flag as parroting."""
        assert is_parroting('some student text here', '') is False
        assert is_parroting('some student text here', '   ') is False

    def test_parroting_lesson_only_stopwords(self):
        """2026-02-19: Lesson with only stopwords should return False."""
        lesson_text = 'the a an is are was were has have had'
        student_text = 'the owl is very wise and has big eyes'
        assert is_parroting(student_text, lesson_text) is False

    def test_extract_nouns_basic(self):
        """2026-02-19: extract_nouns returns 4+ char non-stopword words."""
        result = extract_nouns('Owls hunt mice with their sharp talons every night')
        assert 'owls' in result  # 2026-02-19: Content word
        assert 'hunt' in result
        assert 'mice' in result
        assert 'with' not in result  # 2026-02-19: Stopword excluded
        assert 'their' not in result  # 2026-02-19: Stopword excluded
        # 'mic' < 4 chars so won't be there but 'mice' is 4 chars — check
        assert len(result) >= 3


# ── Weighted Formula Tests ─────────────────────────────────────────────────

class TestWeightedFormula:
    """2026-02-19: Tests for the weighted score and star rating formula."""

    def test_score_weighted_formula(self):
        """2026-02-19: Verify numerical formula for a known input."""
        # practice=4 stars → (4/5*100)*0.30 = 24
        # comprehension=78 → 78*0.40 = 31.2
        # application=50   → 50*0.20 = 10
        # retention=50     → 50*0.10 = 5
        # total = 70.2
        score = ComprehensionService._compute_weighted_score(
            practice_stars=4,
            comprehension_score=78.0,
        )
        assert abs(score - 70.2) < 0.01  # 2026-02-19: Numerical precision

    def test_score_to_weighted_stars_low(self):
        """2026-02-19: Low weighted score → low star rating."""
        # weighted_score = 0 → 0 stars
        stars = ComprehensionService._weighted_to_stars(0.0)
        assert stars == 0

    def test_score_to_weighted_stars_perfect(self):
        """2026-02-19: Max stars when all components are at maximum."""
        # practice=5 stars: (5/5*100)*0.30 = 30
        # comprehension=100: 100*0.40 = 40
        # application=50: 50*0.20 = 10
        # retention=50: 50*0.10 = 5
        # total = 85 → ceil(85/20) = ceil(4.25) = 5 stars
        score = ComprehensionService._compute_weighted_score(
            practice_stars=5,
            comprehension_score=100.0,
        )
        stars = ComprehensionService._weighted_to_stars(score)
        assert stars == 5

    def test_score_to_weighted_stars_boundary(self):
        """2026-02-19: Stars calculation uses ceil(score/20)."""
        # weighted_score=60.01 → ceil(60.01/20) = ceil(3.0005) = 4
        stars = ComprehensionService._weighted_to_stars(60.01)
        assert stars == 4

    def test_score_to_weighted_stars_exactly_60(self):
        """2026-02-19: Exactly 60 → ceil(60/20)=3 stars."""
        stars = ComprehensionService._weighted_to_stars(60.0)
        assert stars == 3


# ── Service Integration Tests ──────────────────────────────────────────────

@pytest.mark.django_db
class TestComprehensionServiceSubmit:
    """2026-02-19: Integration tests for ComprehensionService.submit_explanation."""

    def test_submit_parroting_rejected(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Parroting submission returns is_parroting=True, no DB record."""
        from services.comprehension_service.models import ComprehensionEvaluation

        lesson_summary = (
            'Ollie the owl lives in a dark forest watching animals every night wisely '
            'from high branch thinking carefully before speaking wise words.'
        )
        student_text = (
            'Ollie owl lives forest watching animals night wisely high branch thinking '
            'carefully speaking wise.'  # 2026-02-19: Near-copy of lesson
        )

        with patch(CONTENT_PATCH) as mock_content:
            mock_content.return_value = {
                'title': 'Day 1',
                'teaching_content': {'concept_text': lesson_summary},
            }
            result = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text=student_text,
                practice_stars=4,
            )

        assert result['is_parroting'] is True  # 2026-02-19: Flagged
        assert 'message' in result  # 2026-02-19: Feedback message
        # 2026-02-19: No DB record should be created
        assert ComprehensionEvaluation.objects.filter(student=student_user).count() == 0

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_creates_evaluation_record(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Non-parroting submission creates a ComprehensionEvaluation."""
        from services.comprehension_service.models import ComprehensionEvaluation

        with patch(CONTENT_PATCH, return_value={
            'title': 'Meeting Ollie',
            'teaching_content': {'concept_text': 'Short lesson text.'},
        }):
            result = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text='Owls hunt mice and use big eyes to see in darkness.',
                practice_stars=4,
            )

        assert result['is_parroting'] is False  # 2026-02-19: Not parroting
        assert ComprehensionEvaluation.objects.filter(student=student_user).count() == 1

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_comprehension_score_mean(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: comprehension_score stored is the mean of 5 dimensions."""
        from services.comprehension_service.models import ComprehensionEvaluation

        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            result = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text='Owls hunt mice using sharp talons in the darkness.',
                practice_stars=4,
            )

        expected_mean = (85 + 80 + 75 + 70 + 80) / 5.0  # 2026-02-19: = 78.0
        eval_record = ComprehensionEvaluation.objects.get(student=student_user)
        assert abs(eval_record.comprehension_score - expected_mean) < 0.01
        assert abs(result['comprehension_score'] - expected_mean) < 0.01

    def test_submit_llm_error_uses_fallback(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: LLM error → evaluator falls back to 50s, llm_error=True, record created."""
        from services.comprehension_service.models import ComprehensionEvaluation

        # 2026-02-19: Patch LLM provider at module level so evaluator catches exception
        with patch('services.comprehension_service.evaluator.get_llm_provider') as mock_llm:
            mock_llm.side_effect = Exception('Ollama is down')
            with patch(CONTENT_PATCH, return_value={
                'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
            }):
                result = ComprehensionService.submit_explanation(
                    student=student_user,
                    lesson_id=str(published_lesson.id),
                    day_number=1,
                    student_text='Owls use their large round eyes to see in total darkness.',
                    practice_stars=3,
                )

        # 2026-02-19: Evaluator falls back to 50s — service continues and stores record
        assert result['is_parroting'] is False  # 2026-02-19: Not parroting
        assert result['llm_error'] is True  # 2026-02-19: LLM failed flag
        assert result['scores']['understanding'] == 50  # 2026-02-19: Default fallback
        assert ComprehensionEvaluation.objects.filter(student=student_user).count() == 1

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_updates_dayprogress_status(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Submit updates DayProgress status to 'day_complete'."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text='Owls use their large round eyes to hunt and navigate.',
                practice_stars=4,
            )

        day_progress_comprehension.refresh_from_db()
        assert day_progress_comprehension.status == 'day_complete'

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_attempt_number_increments(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Second submission has attempt_number=2."""
        from services.comprehension_service.models import ComprehensionEvaluation

        own_words_text = 'Owls hunt mice and use their large round silent wings.'

        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            result1 = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text=own_words_text,
                practice_stars=4,
            )
            result2 = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text=own_words_text + ' extra words here.',
                practice_stars=4,
            )

        assert result1['attempt_number'] == 1  # 2026-02-19: First attempt
        assert result2['attempt_number'] == 2  # 2026-02-19: Second attempt
        assert ComprehensionEvaluation.objects.filter(student=student_user).count() == 2

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_is_new_best_flag(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: First submission is always is_new_best=True."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            result = ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text='Owls use large eyes to see in complete darkness at night.',
                practice_stars=4,
            )

        assert result['is_new_best'] is True  # 2026-02-19: First submission

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_submit_day1_advances_current_day(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Day 1 completion advances current_day to 2."""
        with patch(CONTENT_PATCH, return_value={
            'title': 'Day 1', 'teaching_content': {'concept_text': 'Short.'},
        }):
            ComprehensionService.submit_explanation(
                student=student_user,
                lesson_id=str(published_lesson.id),
                day_number=1,
                student_text='Owls navigate using echolocation and sharp night vision.',
                practice_stars=4,
            )

        lesson_progress.refresh_from_db()
        assert lesson_progress.current_day == 2  # 2026-02-19: Day advanced


# ── Best Evaluation Tests ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestGetBestEvaluation:
    """2026-02-19: Tests for ComprehensionService.get_best_evaluation."""

    def test_get_best_evaluation_none(self, student_user, published_lesson):
        """2026-02-19: Returns None when no evaluations exist."""
        result = ComprehensionService.get_best_evaluation(
            student=student_user,
            lesson_id=str(published_lesson.id),
            day_number=1,
        )
        assert result is None  # 2026-02-19: No evaluations

    @patch(EVAL_PATCH, return_value=dict(MOCK_EVAL_SCORES))
    def test_get_best_evaluation_returns_highest_stars(
        self, mock_eval, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-19: Returns the evaluation with highest weighted_star_rating."""
        from services.comprehension_service.models import ComprehensionEvaluation

        # 2026-02-19: Create two evaluations with different stars
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
            student_text='Second attempt, better',
            weighted_star_rating=4,
            attempt_number=2,
        )

        result = ComprehensionService.get_best_evaluation(
            student=student_user,
            lesson_id=str(published_lesson.id),
            day_number=1,
        )

        assert result is not None  # 2026-02-19: Has result
        assert result['weighted_star_rating'] == 4  # 2026-02-19: Best rating


# ── Evaluator Fallback Test ────────────────────────────────────────────────

class TestEvaluatorFallback:
    """2026-02-19: Tests for the LLM evaluator fallback behaviour."""

    def test_evaluator_returns_fallback_on_llm_exception(self):
        """2026-02-19: evaluate_explanation catches LLM errors and returns fallback 50s."""
        from services.comprehension_service import evaluator

        # 2026-02-19: Patch get_llm_provider on the evaluator module (module-level import)
        with patch.object(evaluator, 'get_llm_provider') as mock_llm:
            mock_llm.side_effect = Exception('Ollama not running')

            result = evaluator.evaluate_explanation(
                student_text='Owls use large round eyes to see at night.',
                lesson_summary='Owls are nocturnal birds.',
                topic='The Wise Owl',
            )

        assert result['llm_error'] is True  # 2026-02-19: Fallback flagged
        assert result['understanding'] == 50  # 2026-02-19: Default score
        assert result['feedback']  # 2026-02-19: Has some feedback

    def test_evaluator_returns_fallback_on_json_parse_error(self):
        """2026-02-19: evaluate_explanation handles non-JSON LLM response gracefully."""
        from services.comprehension_service import evaluator

        mock_response = MagicMock()  # 2026-02-19: Mock response
        mock_response.text = 'This is not JSON at all!'

        # 2026-02-19: Patch get_llm_provider on the evaluator module
        with patch.object(evaluator, 'get_llm_provider') as mock_llm:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_llm.return_value = mock_provider

            result = evaluator.evaluate_explanation(
                student_text='Owls hunt at night.',
                lesson_summary='Owls are nocturnal.',
                topic='Owls',
            )

        assert result['llm_error'] is True  # 2026-02-19: Fallback
        assert result['accuracy'] == 50  # 2026-02-19: Default


# ── Key-Point Evaluator Tests (BS-CMP v2) ─────────────────────────────────

class TestKeyPointEvaluator:
    """2026-02-21: Tests for evaluate_key_points() — marks-based LLM evaluator."""

    def test_evaluate_key_points_all_covered(self):
        """2026-02-21: LLM returns all True → marks_awarded equals marks_available."""
        mock_response = MagicMock()
        mock_response.text = '{"covered": [true, true], "feedback": "Excellent work!"}'

        with patch.object(evaluator_module, 'get_llm_provider') as mock_llm:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_llm.return_value = mock_provider

            result = evaluator_module.evaluate_key_points(
                student_text='Science is systematic and uses evidence.',
                key_points=[
                    'Science is a systematic way of studying the natural world',
                    'Science uses observation and evidence rather than guessing',
                ],
                question='Explain what science is.',
            )

        assert result['llm_error'] is False  # 2026-02-21: Success
        assert result['covered'] == [True, True]  # 2026-02-21: All covered
        assert result['feedback'] == 'Excellent work!'  # 2026-02-21: LLM feedback

    def test_evaluate_key_points_partial(self):
        """2026-02-21: LLM returns mixed booleans → partial coverage."""
        mock_response = MagicMock()
        mock_response.text = '{"covered": [true, false, true], "feedback": "Good start!"}'

        with patch.object(evaluator_module, 'get_llm_provider') as mock_llm:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_llm.return_value = mock_provider

            result = evaluator_module.evaluate_key_points(
                student_text='Scientists ask questions and test ideas.',
                key_points=[
                    'Scientific thinking starts with asking questions',
                    'Scientists test ideas through experiments',
                    'Scientific knowledge changes when new evidence appears',
                ],
                question='Describe three features of scientific thinking.',
            )

        assert result['llm_error'] is False  # 2026-02-21: Success
        assert result['covered'] == [True, False, True]  # 2026-02-21: Partial
        assert sum(result['covered']) == 2  # 2026-02-21: Two covered

    def test_evaluate_key_points_llm_fallback(self):
        """2026-02-21: LLM exception → all False covered list, llm_error=True."""
        with patch.object(evaluator_module, 'get_llm_provider') as mock_llm:
            mock_llm.side_effect = Exception('LLM unavailable')

            result = evaluator_module.evaluate_key_points(
                student_text='Science is good.',
                key_points=['Point A', 'Point B'],
                question='Explain science.',
            )

        assert result['llm_error'] is True  # 2026-02-21: Error flagged
        assert result['covered'] == [False, False]  # 2026-02-21: All False fallback
        assert result['feedback']  # 2026-02-21: Has fallback feedback


# ── Submit Question Answer Tests (BS-CMP v2) ──────────────────────────────

# 2026-02-21: Sample comprehension questions for service tests
SAMPLE_CQ = [
    {
        'id': 'D1_CQ1',
        'marks': 2,
        'question': 'Explain what science is.',
        'key_points': [
            'Science is a systematic way of studying the natural world',
            'Science uses observation and evidence rather than guessing',
        ],
        'model_answer': 'Science systematically studies the world using evidence.',
    },
    {
        'id': 'D1_CQ2',
        'marks': 3,
        'question': 'Describe three features of scientific thinking.',
        'key_points': [
            'Scientific thinking starts with asking questions',
            'Scientists test ideas through experiments',
            'Scientific knowledge changes when new evidence appears',
        ],
        'model_answer': 'Three features: curiosity, experimentation, and self-correction.',
    },
]

# 2026-02-21: Patch targets for new service tests
CONTENT_PATCH_NEW = 'services.comprehension_service.services.TeachingContentLoader.get_day_content'
KP_EVAL_PATCH = 'services.comprehension_service.services.evaluate_key_points'


@pytest.mark.django_db
class TestSubmitQuestionAnswer:
    """2026-02-21: Tests for ComprehensionService.submit_question_answer (BS-CMP v2)."""

    def _mock_content(self, questions=None):
        """2026-02-21: Return a mock day_content dict with comprehension_questions."""
        return {
            'title': 'Day 1',
            'teaching_content': {'concept_text': 'Short lesson.'},
            'comprehension_questions': questions if questions is not None else SAMPLE_CQ,
        }

    def _submit(
        self, student_user, published_lesson, lesson_progress,
        day_progress_comprehension, question_id='D1_CQ1',
        student_text='Science uses evidence and observation.',
        eval_result=None,
    ):
        """2026-02-21: Helper to call submit_question_answer with mocks."""
        if eval_result is None:
            eval_result = {'covered': [True, True], 'feedback': 'Good!', 'llm_error': False}

        with patch(CONTENT_PATCH_NEW, return_value=self._mock_content()):
            with patch(KP_EVAL_PATCH, return_value=eval_result):
                return ComprehensionService.submit_question_answer(
                    student=student_user,
                    lesson_id=str(published_lesson.id),
                    day_number=1,
                    question_id=question_id,
                    student_text=student_text,
                    input_method='typed',
                )

    def test_submit_creates_question_response_record(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-21: Submission creates a ComprehensionQuestionResponse DB record."""
        from services.comprehension_service.models import ComprehensionQuestionResponse

        self._submit(student_user, published_lesson, lesson_progress, day_progress_comprehension)

        assert ComprehensionQuestionResponse.objects.filter(
            student=student_user, question_id='D1_CQ1'
        ).count() == 1  # 2026-02-21: One record created

    def test_submit_attempt_number_increments(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-21: Second submission has attempt_number=2."""
        result1 = self._submit(
            student_user, published_lesson, lesson_progress, day_progress_comprehension
        )
        result2 = self._submit(
            student_user, published_lesson, lesson_progress, day_progress_comprehension
        )

        assert result1['attempt_number'] == 1  # 2026-02-21: First attempt
        assert result2['attempt_number'] == 2  # 2026-02-21: Second attempt

    def test_submit_is_new_best_first_attempt(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-21: First submission is always is_new_best=True."""
        result = self._submit(
            student_user, published_lesson, lesson_progress, day_progress_comprehension
        )

        assert result['is_new_best'] is True  # 2026-02-21: First attempt always best

    def test_submit_all_questions_completes_day(
        self, student_user, published_lesson, lesson_progress, day_progress_comprehension
    ):
        """2026-02-21: After answering all questions, DayProgress.status='day_complete'."""
        # 2026-02-21: Answer both questions
        self._submit(
            student_user, published_lesson, lesson_progress, day_progress_comprehension,
            question_id='D1_CQ1',
        )
        self._submit(
            student_user, published_lesson, lesson_progress, day_progress_comprehension,
            question_id='D1_CQ2',
            eval_result={'covered': [True, False, True], 'feedback': 'Keep going!', 'llm_error': False},
        )

        day_progress_comprehension.refresh_from_db()
        assert day_progress_comprehension.status == 'day_complete'  # 2026-02-21: Day done

    def test_get_day_questions_returns_list(
        self, student_user, published_lesson, lesson_progress
    ):
        """2026-02-21: get_day_questions returns comprehension_questions list from content."""
        with patch(CONTENT_PATCH_NEW, return_value=self._mock_content()):
            questions = ComprehensionService.get_day_questions(
                lesson_id=str(published_lesson.id),
                day_number=1,
            )

        assert isinstance(questions, list)  # 2026-02-21: Returns list
        assert len(questions) == 2  # 2026-02-21: Two questions from mock
        assert questions[0]['id'] == 'D1_CQ1'  # 2026-02-21: First question ID
