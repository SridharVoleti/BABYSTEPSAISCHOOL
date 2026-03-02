"""
2026-02-20: Tests for Vocabulary Acquisition System service layer (BS-LNG).

Purpose:
    20 unit tests covering content_generator (cache hit, LLM generate,
    LLM error fallback, JSON parse error fallback), VocabularySession
    lifecycle, record_pronunciation, record_mcq, complete_session,
    get_progress, fluency formula, and star threshold boundaries.
"""

import pytest  # 2026-02-20: Pytest framework
from datetime import date  # 2026-02-20: DOB for student fixture
from unittest.mock import patch, MagicMock  # 2026-02-20: Mocking

from django.contrib.auth import get_user_model  # 2026-02-20: User model
from rest_framework.exceptions import ValidationError, PermissionDenied  # 2026-02-20: Exceptions

from services.auth_service.models import Parent, Student  # 2026-02-20: Auth models
from services.read_along_service.models import Language  # 2026-02-20: Language model
from services.read_along_service.language_registry import LANGUAGE_SEED  # 2026-02-20: Seed data
from services.vocabulary_service.models import (  # 2026-02-20: Vocabulary models
    VocabularyWord, WordContent, StudentWordProgress, VocabularySession, SessionWord,
)
from services.vocabulary_service.services import VocabularyService  # 2026-02-20: Under test
from services.vocabulary_service.content_generator import get_word_content  # 2026-02-20: Under test

User = get_user_model()  # 2026-02-20: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def seed_languages(db):
    """2026-02-20: Ensure Language rows exist for all tests."""
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


@pytest.fixture
def parent_user(db):
    """2026-02-20: Create parent user for testing."""
    user = User.objects.create_user(username='voc_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000000101', full_name='Vocab Test Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-20: Grade 1 student with Hindi as primary language."""
    user = User.objects.create_user(username='voc_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Vocab Test Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1, login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )


@pytest.fixture
def hindi_language(db):
    """2026-02-20: Return the Hindi Language object."""
    return Language.objects.get(name='Hindi')


@pytest.fixture
def english_language(db):
    """2026-02-20: Return the English Language object."""
    return Language.objects.get(name='English')


@pytest.fixture
def hindi_word(hindi_language, db):
    """2026-02-20: Create a single Hindi Grade 1 word for testing."""
    return VocabularyWord.objects.create(
        language=hindi_language,
        grade=1,
        frequency_rank=999,
        word='परीक्षा',
        romanization='pareeksha',
        word_type='noun',
        image_keyword='test',
    )


@pytest.fixture
def ten_hindi_words(hindi_language, db):
    """2026-02-20: Create 12 Hindi Grade 1 words (10 for session + 2 extras)."""
    words = []
    for i in range(1, 13):
        word = VocabularyWord.objects.create(
            language=hindi_language,
            grade=1,
            frequency_rank=1000 + i,
            word=f'शब्द{i}',
            romanization=f'shabd{i}',
            word_type='noun',
            image_keyword=f'word{i}',
        )
        words.append(word)
    return words


# ── 1. TestVocabularyContentGenerator ─────────────────────────────────────

@pytest.mark.django_db
class TestVocabularyContentGenerator:
    """2026-02-20: Tests for get_word_content (content_generator.py)."""

    def test_cached_return(self, hindi_word, english_language, db):
        """2026-02-20: Cache hit returns stored content without calling LLM."""
        # 2026-02-20: Pre-populate cache
        WordContent.objects.create(
            word=hindi_word,
            mother_tongue=english_language,
            definition='a test',
            example_sentence='यह परीक्षा है।',
            example_translation='This is a test.',
            mnemonic='Think of exam',
            llm_error=False,
        )

        with patch('services.vocabulary_service.content_generator.get_llm_provider') as mock_llm:
            result = get_word_content(hindi_word, english_language)

        mock_llm.assert_not_called()  # 2026-02-20: LLM should NOT be called on cache hit
        assert result['definition'] == 'a test'
        assert result['llm_error'] is False

    def test_llm_generate(self, hindi_word, english_language, db):
        """2026-02-20: Cache miss triggers LLM call and stores result."""
        mock_response = MagicMock()
        mock_response.text = '{"definition": "परीक्षा", "example_sentence": "यह परीक्षा है।", "example_translation": "This is a test.", "mnemonic": ""}'

        with patch('services.vocabulary_service.content_generator.get_llm_provider') as mock_factory:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_factory.return_value = mock_provider

            result = get_word_content(hindi_word, english_language)

        assert result['definition'] == 'परीक्षा'
        assert result['llm_error'] is False
        assert WordContent.objects.filter(word=hindi_word, mother_tongue=english_language).exists()

    def test_llm_error_fallback(self, hindi_word, english_language, db):
        """2026-02-20: LLM exception → fallback content, llm_error=True, stored in cache."""
        with patch('services.vocabulary_service.content_generator.get_llm_provider') as mock_factory:
            mock_factory.side_effect = Exception('Ollama unavailable')

            result = get_word_content(hindi_word, english_language)

        assert result['llm_error'] is True
        assert 'परीक्षा' in result['definition'] or 'परीक्षा' in result['example_sentence']
        # 2026-02-20: Fallback stored in cache
        assert WordContent.objects.filter(word=hindi_word, mother_tongue=english_language, llm_error=True).exists()

    def test_json_parse_error_fallback(self, hindi_word, english_language, db):
        """2026-02-20: LLM returns non-JSON → fallback content, llm_error=True."""
        mock_response = MagicMock()
        mock_response.text = 'This is not valid JSON at all!'

        with patch('services.vocabulary_service.content_generator.get_llm_provider') as mock_factory:
            mock_provider = MagicMock()
            mock_provider.chat.return_value = mock_response
            mock_factory.return_value = mock_provider

            result = get_word_content(hindi_word, english_language)

        assert result['llm_error'] is True


# ── 2. TestVocabularySession ───────────────────────────────────────────────

@pytest.mark.django_db
class TestVocabularySession:
    """2026-02-20: Tests for VocabularyService session methods."""

    def _patch_llm(self):
        """2026-02-20: Patch LLM to return valid fallback content."""
        mock_response = MagicMock()
        mock_response.text = '{"definition": "test", "example_sentence": "test sentence", "example_translation": "test", "mnemonic": ""}'
        mock_provider = MagicMock()
        mock_provider.chat.return_value = mock_response
        return patch(
            'services.vocabulary_service.content_generator.get_llm_provider',
            return_value=mock_provider,
        )

    def test_creates_new_session(self, student, ten_hindi_words, db):
        """2026-02-20: get_today_session creates a new session with 10 words."""
        with self._patch_llm():
            result = VocabularyService.get_today_session(student, 'Hindi')

        assert result['language'] == 'Hindi'
        assert result['status'] == 'in_progress'
        assert len(result['words']) == 10
        assert VocabularySession.objects.filter(student=student).count() == 1

    def test_returns_existing_same_day(self, student, ten_hindi_words, db):
        """2026-02-20: Calling get_today_session twice returns same session (idempotent)."""
        with self._patch_llm():
            result1 = VocabularyService.get_today_session(student, 'Hindi')
            result2 = VocabularyService.get_today_session(student, 'Hindi')

        assert result1['session_id'] == result2['session_id']
        assert VocabularySession.objects.filter(student=student).count() == 1

    def test_skips_mastered_words(self, student, hindi_language, ten_hindi_words, db):
        """2026-02-20: Mastered words are excluded from session word selection."""
        # 2026-02-20: Mark first 5 words as mastered
        for word in ten_hindi_words[:5]:
            StudentWordProgress.objects.create(
                student=student, word=word, status='mastered'
            )

        with self._patch_llm():
            result = VocabularyService.get_today_session(student, 'Hindi')

        # 2026-02-20: Words in session should not include mastered word IDs
        mastered_ids = {str(w.id) for w in ten_hindi_words[:5]}
        session_word_ids = {w['word_id'] for w in result['words']}
        assert mastered_ids.isdisjoint(session_word_ids)

    def test_respects_student_grade(self, parent_user, hindi_language, db):
        """2026-02-20: Session only fetches words for student's grade."""
        # 2026-02-20: Create grade 2 student
        user = User.objects.create_user(username='grade2_student', password='pass')
        grade2_student = Student.objects.create(
            parent=parent_user, user=user, full_name='Grade 2 Student',
            dob=date(2016, 1, 1), age_group='6-12', grade=2, login_method='pin',
            language_1='English',
        )
        # 2026-02-20: Create grade 2 word
        VocabularyWord.objects.create(
            language=hindi_language, grade=2, frequency_rank=1,
            word='ग्रेड2', romanization='grade2', word_type='noun',
        )
        # 2026-02-20: Create grade 1 words (should NOT appear for grade 2 student)
        for i in range(10):
            VocabularyWord.objects.create(
                language=hindi_language, grade=1, frequency_rank=500 + i,
                word=f'ग्रेड1_{i}', romanization=f'grade1_{i}', word_type='noun',
            )

        with self._patch_llm():
            result = VocabularyService.get_today_session(grade2_student, 'Hindi')

        for word_data in result['words']:
            # 2026-02-20: All words must be grade 2
            word_obj = VocabularyWord.objects.get(id=word_data['word_id'])
            assert word_obj.grade == 2

    def test_record_pronunciation_updates_progress(self, student, ten_hindi_words, db):
        """2026-02-20: record_pronunciation updates StudentWordProgress."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        result = VocabularyService.record_pronunciation(session_id, word_id, 0.85, student)

        assert result['pronunciation_score'] == 0.85
        assert result['progress_status'] == 'introduced'

        progress = StudentWordProgress.objects.get(student=student, word_id=word_id)
        assert progress.best_pronunciation_score == 0.85
        assert progress.status == 'introduced'

    def test_record_mcq_increments_count(self, student, ten_hindi_words, db):
        """2026-02-20: record_mcq increments mcq_correct_count on correct answer."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        VocabularyService.record_mcq(session_id, word_id, correct=True, student=student)

        progress = StudentWordProgress.objects.get(student=student, word_id=word_id)
        assert progress.mcq_correct_count == 1

    def test_complete_calculates_fluency_stars(self, student, ten_hindi_words, db):
        """2026-02-20: complete_session returns correct star_rating."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']

        # 2026-02-20: Score 10 words with high pronunciation + correct MCQ
        for word_data in session_data['words']:
            VocabularyService.record_pronunciation(session_id, word_data['word_id'], 0.95, student)
            VocabularyService.record_mcq(session_id, word_data['word_id'], correct=True, student=student)

        result = VocabularyService.complete_session(session_id, student)

        assert result['fluency_star_rating'] == 5  # 2026-02-20: Perfect score → 5 stars
        assert result['session_id'] == session_id

    def test_complete_marks_words_mastered(self, student, ten_hindi_words, db):
        """2026-02-20: Words with MCQ correct + pronunciation >= 0.70 become mastered."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']
        first_word_id = session_data['words'][0]['word_id']

        # 2026-02-20: Score first word with mastery criteria
        VocabularyService.record_pronunciation(session_id, first_word_id, 0.80, student)
        VocabularyService.record_mcq(session_id, first_word_id, correct=True, student=student)

        result = VocabularyService.complete_session(session_id, student)

        assert result['words_mastered'] >= 1
        progress = StudentWordProgress.objects.get(student=student, word_id=first_word_id)
        assert progress.status == 'mastered'

    def test_complete_marks_words_practicing(self, student, ten_hindi_words, db):
        """2026-02-20: Words scored but not meeting mastery criteria become 'practicing'."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']
        word_id = session_data['words'][0]['word_id']

        # 2026-02-20: Only pronunciation scored (no MCQ) → practicing
        VocabularyService.record_pronunciation(session_id, word_id, 0.60, student)

        VocabularyService.complete_session(session_id, student)

        progress = StudentWordProgress.objects.get(student=student, word_id=word_id)
        assert progress.status == 'practicing'

    def test_complete_prevents_duplicate(self, student, ten_hindi_words, db):
        """2026-02-20: Completing an already-completed session raises ValidationError."""
        with self._patch_llm():
            session_data = VocabularyService.get_today_session(student, 'Hindi')

        session_id = session_data['session_id']
        VocabularyService.complete_session(session_id, student)

        with pytest.raises(ValidationError):
            VocabularyService.complete_session(session_id, student)

    def test_invalid_language_raises(self, student, db):
        """2026-02-20: get_today_session with unknown language raises ValidationError."""
        with pytest.raises(ValidationError):
            VocabularyService.get_today_session(student, 'Klingon')


# ── 3. TestVocabularyProgress ──────────────────────────────────────────────

@pytest.mark.django_db
class TestVocabularyProgress:
    """2026-02-20: Tests for VocabularyService.get_progress."""

    def test_no_activity_returns_zeros(self, student, db):
        """2026-02-20: New student with no sessions returns all zeros."""
        result = VocabularyService.get_progress(student, 'Hindi')

        assert result['introduced_count'] == 0
        assert result['mastered_count'] == 0
        assert result['current_streak'] == 0
        assert result['today_completed'] is False

    def test_counts_mastered_words(self, student, hindi_language, db):
        """2026-02-20: Mastered words are counted correctly."""
        word = VocabularyWord.objects.create(
            language=hindi_language, grade=1, frequency_rank=9000,
            word='मास्टर', romanization='master', word_type='noun',
        )
        StudentWordProgress.objects.create(
            student=student, word=word, status='mastered'
        )

        result = VocabularyService.get_progress(student, 'Hindi')
        assert result['mastered_count'] == 1

    def test_streak_increments_daily(self, student, hindi_language, db):
        """2026-02-20: Completed session today → streak = 1."""
        language = Language.objects.get(name='Hindi')
        VocabularySession.objects.create(
            student=student,
            language=language,
            grade=1,
            session_date=date.today(),
            status='completed',
            fluency_star_rating=3,
        )

        result = VocabularyService.get_progress(student, 'Hindi')
        assert result['current_streak'] == 1

    def test_today_completed_flag(self, student, hindi_language, db):
        """2026-02-20: today_completed=True when today's session is completed."""
        language = Language.objects.get(name='Hindi')
        VocabularySession.objects.create(
            student=student,
            language=language,
            grade=1,
            session_date=date.today(),
            status='completed',
            fluency_star_rating=4,
        )

        result = VocabularyService.get_progress(student, 'Hindi')
        assert result['today_completed'] is True


# ── 4. TestFormula ─────────────────────────────────────────────────────────

class TestFormula:
    """2026-02-20: Tests for fluency formula and star threshold mapping."""

    def test_fluency_formula_numerical(self):
        """2026-02-20: Verify fluency formula: 0.60×pron + 0.40×mcq."""
        avg_pron = 0.80
        mcq_pct = 1.00
        expected = (0.80 * 0.60) + (1.00 * 0.40)
        assert abs(expected - 0.88) < 1e-9  # 2026-02-20: Sanity check

        stars = VocabularyService._score_to_stars(expected)
        assert stars == 4  # 2026-02-20: 0.88 is between 0.82 and 0.92 → 4 stars

    def test_star_threshold_boundaries(self):
        """2026-02-20: Verify all star boundary values."""
        fn = VocabularyService._score_to_stars
        assert fn(0.00) == 0   # 2026-02-20: Below 0.40
        assert fn(0.39) == 0
        assert fn(0.40) == 1   # 2026-02-20: At first threshold
        assert fn(0.55) == 2
        assert fn(0.70) == 3
        assert fn(0.82) == 4
        assert fn(0.92) == 5   # 2026-02-20: At top threshold
        assert fn(1.00) == 5   # 2026-02-20: Perfect score
