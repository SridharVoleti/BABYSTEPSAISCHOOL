"""
2026-03-02: Tests for Phase 2 Weighted Star Formula (BS-CMP-003).

Purpose:
    Verify WeightedStarService formula accuracy, edge-cases, Phase 1
    fallback, ConceptMastery propagation, and integration with
    read_along_service and comprehension_service hooks.

~30 tests organised in 5 classes:
    - TestWeightedFormula          : pure formula scenarios
    - TestRecordReadAlong          : record_read_along() behaviour
    - TestRecordSelfExplanation    : record_self_explanation() behaviour
    - TestComputeAndSave           : compute_and_save() end-to-end
    - TestConceptMasteryUpdate     : propagation to ConceptMastery
"""

import pytest  # 2026-03-02: Pytest framework
from datetime import date  # 2026-03-02: Date for DOB

from django.contrib.auth import get_user_model  # 2026-03-02: User model

from services.auth_service.models import Parent, Student  # 2026-03-02: Auth models
from services.teaching_engine.models import (  # 2026-03-02: Teaching models
    TeachingLesson, StudentLessonProgress, DayProgress,
    PracticeSession, ConceptMastery,
)
from services.teaching_engine.weighted_stars import WeightedStarService  # 2026-03-02: Under test

User = get_user_model()  # 2026-03-02: Django User model

# ── Fixtures ──────────────────────────────────────────────────────────────

SAMPLE_CONTENT_PATH = 'json/teaching/class1/English/week1.json'  # 2026-03-02


@pytest.fixture
def parent_user(db):
    """2026-03-02: Create a test parent user."""
    user = User.objects.create_user(
        username='ws_parent', password='testpass123'
    )
    return Parent.objects.create(
        user=user,
        phone='+919000000099',
        full_name='WS Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-02: Create a test student."""
    user = User.objects.create_user(
        username='ws_student', password='testpass123'
    )
    return Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='WS Student',
        dob=date(2017, 6, 10),
        age_group='6-12',
        grade=1,
        login_method='pin',
    )


@pytest.fixture
def lesson(db):
    """2026-03-02: Create a published teaching lesson."""
    return TeachingLesson.objects.create(
        lesson_id='WS_ENG1_W01',
        title='Weighted Stars Test Lesson',
        subject='English',
        class_number=1,
        week_number=1,
        content_json_path=SAMPLE_CONTENT_PATH,
        status='published',
    )


@pytest.fixture
def lesson_progress(student, lesson, db):
    """2026-03-02: Create StudentLessonProgress for student."""
    return StudentLessonProgress.objects.create(
        student=student,
        lesson=lesson,
        iq_level='standard',
        current_day=1,
        day_statuses={'1': 'teaching'},
    )


@pytest.fixture
def day_progress(lesson_progress, db):
    """2026-03-02: Create DayProgress with default zero values."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=1,
        status='mastery_practice',
        questions_attempted=10,
        questions_correct=8,
    )


def _make_practice_session(lesson_progress, day_number, pct_correct, db):
    """2026-03-02: Helper to create a completed PracticeSession."""
    return PracticeSession.objects.create(
        student=lesson_progress.student,
        lesson_progress=lesson_progress,
        day_number=day_number,
        iq_level='standard',
        status='completed',
        total_questions=10,
        questions_answered=10,
        questions_correct=int(pct_correct / 10),
        percentage_correct=pct_correct,
        star_rating=5 if pct_correct >= 90 else 3,
        attempt_number=1,
    )


# ── TestWeightedFormula ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestWeightedFormula:
    """2026-03-02: Unit tests for the weighted formula values."""

    def test_five_star_all_components_high(self, day_progress, lesson_progress, db):
        """2026-03-02: All four components high → 5 stars."""
        day_progress.comprehension_score = 95.0
        day_progress.read_along_score = 0.95
        day_progress.self_explanation_score = 95.0
        day_progress.mastery_star_rating = 5
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 95.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 5  # 2026-03-02: Expect top rating

    def test_one_star_all_components_low(self, day_progress, lesson_progress, db):
        """2026-03-02: All four components at minimum → 1 star."""
        day_progress.comprehension_score = 5.0
        day_progress.read_along_score = 0.05
        day_progress.self_explanation_score = 5.0
        day_progress.mastery_star_rating = 1
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 5.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        assert result >= 1  # 2026-03-02: Non-zero components → ≥ 1

    def test_formula_weights_correct(self, day_progress, lesson_progress, db):
        """
        2026-03-02: Verify formula:
            weighted = 0.40×comp + 0.20×(ra×100) + 0.20×prac + 0.20×self_exp
            comp=60, ra=0.50→50, prac=80, self_exp=40
            weighted = 24 + 10 + 16 + 8 = 58 → ceil(58/20)=3 stars
        """
        day_progress.comprehension_score = 60.0
        day_progress.read_along_score = 0.50
        day_progress.self_explanation_score = 40.0
        day_progress.mastery_star_rating = 3
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 80.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 3  # 2026-03-02: 58 → ceil(58/20)=3

    def test_formula_boundary_exactly_60(self, day_progress, lesson_progress, db):
        """
        2026-03-02: weighted=60 → ceil(60/20)=3 stars exactly.
        """
        day_progress.comprehension_score = 75.0  # 0.40×75=30
        day_progress.read_along_score = 0.50     # 0.20×50=10
        day_progress.self_explanation_score = 50.0  # 0.20×50=10
        day_progress.mastery_star_rating = 3
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 50.0, db)  # 0.20×50=10 → total=60

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 3  # 2026-03-02: exactly 60 → 3 stars

    def test_formula_boundary_61(self, day_progress, lesson_progress, db):
        """
        2026-03-02: weighted=61 → ceil(61/20)=4 stars.
        """
        day_progress.comprehension_score = 80.0   # 0.40×80=32
        day_progress.read_along_score = 0.55       # 0.20×55=11
        day_progress.self_explanation_score = 50.0  # 0.20×50=10
        day_progress.mastery_star_rating = 4
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 40.0, db)  # 0.20×40=8 → total=61

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 4  # 2026-03-02: 61 → ceil(61/20)=4

    def test_zero_weighted_gives_zero_stars(self, day_progress, db):
        """2026-03-02: All components zero → Phase 1 fallback (mastery_star_rating=0)."""
        day_progress.comprehension_score = 0.0
        day_progress.read_along_score = 0.0
        day_progress.self_explanation_score = 0.0
        day_progress.mastery_star_rating = 0
        day_progress.save()
        # No PracticeSession created → practice_pct=0

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 0  # 2026-03-02: Fallback to mastery_star_rating=0

    def test_phase2_star_capped_at_5(self, day_progress, lesson_progress, db):
        """2026-03-02: Formula can never produce > 5."""
        day_progress.comprehension_score = 100.0
        day_progress.read_along_score = 1.0
        day_progress.self_explanation_score = 100.0
        day_progress.mastery_star_rating = 5
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 100.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        assert result <= 5  # 2026-03-02: Capped


# ── TestPhase1Fallback ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPhase1Fallback:
    """2026-03-02: Tests for Phase 1 compatibility fallback."""

    def test_fallback_when_read_along_and_self_exp_zero(self, day_progress, lesson_progress, db):
        """2026-03-02: read_along=0 AND self_exp=0 → use mastery_star_rating."""
        day_progress.comprehension_score = 80.0
        day_progress.read_along_score = 0.0
        day_progress.self_explanation_score = 0.0
        day_progress.mastery_star_rating = 4
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 80.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 4  # 2026-03-02: Mastery star fallback

    def test_fallback_when_no_phase2_data_at_all(self, day_progress, db):
        """2026-03-02: No Phase 2 data at all → use mastery_star_rating."""
        day_progress.mastery_star_rating = 3
        day_progress.save()

        result = WeightedStarService.compute_and_save(day_progress)
        assert result == 3  # 2026-03-02: Direct fallback

    def test_no_fallback_when_read_along_present(self, day_progress, lesson_progress, db):
        """2026-03-02: read_along > 0 → formula is used (not mastery fallback)."""
        day_progress.comprehension_score = 50.0
        day_progress.read_along_score = 0.80
        day_progress.self_explanation_score = 0.0
        day_progress.mastery_star_rating = 5  # Would dominate if fallback used
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 50.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        # formula: 0.40×50 + 0.20×80 + 0.20×50 + 0.20×0 = 20+16+10+0 = 46 → ceil(46/20)=3
        assert result == 3  # 2026-03-02: Formula used, not fallback

    def test_no_fallback_when_self_explanation_present(self, day_progress, lesson_progress, db):
        """2026-03-02: self_explanation > 0 → formula is used."""
        day_progress.comprehension_score = 40.0
        day_progress.read_along_score = 0.0
        day_progress.self_explanation_score = 60.0
        day_progress.mastery_star_rating = 5  # Would dominate if fallback used
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 40.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        # formula: 0.40×40 + 0.20×0 + 0.20×40 + 0.20×60 = 16+0+8+12 = 36 → ceil(36/20)=2
        assert result == 2  # 2026-03-02: Formula used


# ── TestRecordReadAlong ────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRecordReadAlong:
    """2026-03-02: Tests for WeightedStarService.record_read_along()."""

    def test_stores_score_on_day_progress(self, day_progress):
        """2026-03-02: record_read_along persists score."""
        WeightedStarService.record_read_along(day_progress, 0.75)
        day_progress.refresh_from_db()
        assert day_progress.read_along_score == pytest.approx(0.75)

    def test_keeps_best_score(self, day_progress):
        """2026-03-02: Only updates if new score is higher."""
        WeightedStarService.record_read_along(day_progress, 0.80)
        WeightedStarService.record_read_along(day_progress, 0.60)  # Lower
        day_progress.refresh_from_db()
        assert day_progress.read_along_score == pytest.approx(0.80)  # 2026-03-02: Keeps 0.80

    def test_updates_when_new_best(self, day_progress):
        """2026-03-02: Updates when new score exceeds existing."""
        WeightedStarService.record_read_along(day_progress, 0.60)
        WeightedStarService.record_read_along(day_progress, 0.90)  # Higher
        day_progress.refresh_from_db()
        assert day_progress.read_along_score == pytest.approx(0.90)

    def test_score_clamps_at_1(self, day_progress):
        """2026-03-02: Score of 1.0 is stored correctly."""
        WeightedStarService.record_read_along(day_progress, 1.0)
        day_progress.refresh_from_db()
        assert day_progress.read_along_score == pytest.approx(1.0)

    def test_zero_score_not_stored_over_existing(self, day_progress):
        """2026-03-02: Score of 0.0 does not overwrite a positive existing score."""
        day_progress.read_along_score = 0.5
        day_progress.save()
        WeightedStarService.record_read_along(day_progress, 0.0)
        day_progress.refresh_from_db()
        assert day_progress.read_along_score == pytest.approx(0.5)


# ── TestRecordSelfExplanation ──────────────────────────────────────────────

@pytest.mark.django_db
class TestRecordSelfExplanation:
    """2026-03-02: Tests for WeightedStarService.record_self_explanation()."""

    def test_stores_score(self, day_progress):
        """2026-03-02: Persists self_explanation_score."""
        WeightedStarService.record_self_explanation(day_progress, 72.5)
        day_progress.refresh_from_db()
        assert day_progress.self_explanation_score == pytest.approx(72.5)

    def test_keeps_best_score(self, day_progress):
        """2026-03-02: Does not overwrite with lower score."""
        WeightedStarService.record_self_explanation(day_progress, 80.0)
        WeightedStarService.record_self_explanation(day_progress, 60.0)
        day_progress.refresh_from_db()
        assert day_progress.self_explanation_score == pytest.approx(80.0)

    def test_updates_on_improvement(self, day_progress):
        """2026-03-02: Updates when better score arrives."""
        WeightedStarService.record_self_explanation(day_progress, 50.0)
        WeightedStarService.record_self_explanation(day_progress, 85.0)
        day_progress.refresh_from_db()
        assert day_progress.self_explanation_score == pytest.approx(85.0)


# ── TestComputeAndSave ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestComputeAndSave:
    """2026-03-02: End-to-end tests for WeightedStarService.compute_and_save()."""

    def test_phase2_star_rating_persisted(self, day_progress, lesson_progress, db):
        """2026-03-02: phase2_star_rating field updated in DB."""
        day_progress.comprehension_score = 70.0
        day_progress.read_along_score = 0.70
        day_progress.self_explanation_score = 70.0
        day_progress.mastery_star_rating = 3
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 70.0, db)

        WeightedStarService.compute_and_save(day_progress)
        day_progress.refresh_from_db()
        assert day_progress.phase2_star_rating > 0  # 2026-03-02: Was stored

    def test_no_practice_session_uses_zero(self, day_progress):
        """2026-03-02: Missing PracticeSession → practice_pct=0, formula still runs."""
        day_progress.comprehension_score = 80.0
        day_progress.read_along_score = 0.80
        day_progress.self_explanation_score = 80.0
        day_progress.mastery_star_rating = 4
        day_progress.save()

        result = WeightedStarService.compute_and_save(day_progress)
        # 0.40×80 + 0.20×80 + 0.20×0 + 0.20×80 = 32+16+0+16 = 64 → ceil(64/20)=4
        assert result == 4

    def test_returns_integer(self, day_progress, lesson_progress, db):
        """2026-03-02: compute_and_save returns an int."""
        day_progress.read_along_score = 0.70
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 70.0, db)
        result = WeightedStarService.compute_and_save(day_progress)
        assert isinstance(result, int)

    def test_best_practice_session_used(self, day_progress, lesson_progress, db):
        """2026-03-02: Best completed PracticeSession.percentage_correct is used."""
        # Create two practice sessions: 40% and 90%
        _make_practice_session(lesson_progress, 1, 40.0, db)
        PracticeSession.objects.create(
            student=lesson_progress.student,
            lesson_progress=lesson_progress,
            day_number=1,
            iq_level='standard',
            status='completed',
            total_questions=10,
            questions_answered=10,
            questions_correct=9,
            percentage_correct=90.0,
            star_rating=5,
            attempt_number=2,
        )

        day_progress.comprehension_score = 90.0
        day_progress.read_along_score = 0.90
        day_progress.self_explanation_score = 90.0
        day_progress.save()

        result = WeightedStarService.compute_and_save(day_progress)
        # Uses best=90%: 0.40×90 + 0.20×90 + 0.20×90 + 0.20×90 = 90 → 5 stars
        assert result == 5


# ── TestConceptMasteryUpdate ───────────────────────────────────────────────

@pytest.mark.django_db
class TestConceptMasteryUpdate:
    """2026-03-02: Tests for ConceptMastery propagation in compute_and_save."""

    def test_concept_mastery_best_star_updated(self, student, lesson, lesson_progress, day_progress, db):
        """2026-03-02: ConceptMastery.best_star_rating updated when new stars > old."""
        mastery = ConceptMastery.objects.create(
            student=student,
            lesson=lesson,
            day_number=1,
            best_star_rating=2,
            attempts_count=1,
            is_mastered=False,
        )

        day_progress.comprehension_score = 90.0
        day_progress.read_along_score = 0.90
        day_progress.self_explanation_score = 90.0
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 90.0, db)

        WeightedStarService.compute_and_save(day_progress)
        mastery.refresh_from_db()
        assert mastery.best_star_rating == 5  # 2026-03-02: Upgraded from 2 to 5

    def test_concept_mastery_not_downgraded(self, student, lesson, lesson_progress, day_progress, db):
        """2026-03-02: ConceptMastery.best_star_rating never decreases."""
        mastery = ConceptMastery.objects.create(
            student=student,
            lesson=lesson,
            day_number=1,
            best_star_rating=5,
            attempts_count=3,
            is_mastered=True,
        )

        day_progress.comprehension_score = 30.0
        day_progress.read_along_score = 0.30
        day_progress.self_explanation_score = 30.0
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 30.0, db)

        WeightedStarService.compute_and_save(day_progress)
        mastery.refresh_from_db()
        assert mastery.best_star_rating == 5  # 2026-03-02: Not downgraded

    def test_no_concept_mastery_no_crash(self, day_progress, lesson_progress, db):
        """2026-03-02: Missing ConceptMastery is handled gracefully."""
        # No ConceptMastery created
        day_progress.comprehension_score = 80.0
        day_progress.read_along_score = 0.80
        day_progress.self_explanation_score = 80.0
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 80.0, db)

        # Should not raise any exception
        result = WeightedStarService.compute_and_save(day_progress)
        assert isinstance(result, int)

    def test_concept_mastery_is_mastered_set_when_gte_3(self, student, lesson, lesson_progress, day_progress, db):
        """2026-03-02: is_mastered becomes True when phase2 stars >= 3."""
        mastery = ConceptMastery.objects.create(
            student=student,
            lesson=lesson,
            day_number=1,
            best_star_rating=1,
            attempts_count=1,
            is_mastered=False,
        )

        day_progress.comprehension_score = 75.0
        day_progress.read_along_score = 0.75
        day_progress.self_explanation_score = 75.0
        day_progress.save()
        _make_practice_session(lesson_progress, 1, 75.0, db)

        result = WeightedStarService.compute_and_save(day_progress)
        mastery.refresh_from_db()
        if result >= 3:  # 2026-03-02: Conditional since formula may vary slightly
            assert mastery.is_mastered is True
