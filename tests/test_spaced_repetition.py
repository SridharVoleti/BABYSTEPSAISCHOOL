"""
2026-02-27: Tests for the Spaced Repetition Engine (BS-SPC).

Purpose:
    Verify Leitner-box interval scheduling, review queue management,
    pacing service logic, and all API endpoints for the spaced repetition
    module. Covers first-review creation, box advancement, reset on fail,
    maintenance phase, and academic-year pacing calculations.
"""

import pytest  # 2026-02-27: Pytest framework
from datetime import date, timedelta  # 2026-02-27: Date arithmetic
from django.contrib.auth import get_user_model  # 2026-02-27: User model
from rest_framework.test import APIClient  # 2026-02-27: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-27: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-27: Auth models
from services.teaching_engine.models import (  # 2026-02-27: Teaching models
    TeachingLesson, ConceptMastery,
)
from services.spaced_repetition_service.models import (  # 2026-02-27: SPC models
    SpacedRepetitionRecord, PacingRecord, ReviewSession,
)
from services.spaced_repetition_service.services import (  # 2026-02-27: SPC services
    SpacedRepetitionService, PacingService, LEITNER_INTERVALS,
)

User = get_user_model()  # 2026-02-27: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-27: Create a parent user for spaced repetition tests."""
    user = User.objects.create_user(username='spc_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000000901', full_name='SPC Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-27: Create a grade-1 student for spaced repetition tests."""
    user = User.objects.create_user(username='spc_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='SPC Student',
        dob=date(2016, 3, 15), age_group='6-12', grade=1,
        login_method='pin', language_1='English', language_2='Telugu',
    )


@pytest.fixture
def student_client(student):
    """2026-02-27: Authenticated API client for the student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-27: Authenticated API client for the parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def lesson(db):
    """2026-02-27: Create a published TeachingLesson for mastery records."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_TEST_W01',
        title='Test Lesson',
        subject='English',
        class_number=1,
        week_number=1,
        status='published',
    )


@pytest.fixture
def mastery(student, lesson, db):
    """2026-02-27: Create a ConceptMastery record (day 1, 4 stars, mastered)."""
    return ConceptMastery.objects.create(
        student=student, lesson=lesson, day_number=1,
        best_star_rating=4, attempts_count=1, is_mastered=True,
    )


# ── TestLeitnerIntervals ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestLeitnerIntervals:
    """2026-02-27: Tests for Leitner-box scheduling: first-review creation,
    interval calculation per star rating, idempotency, box advancement,
    and box reset on failure."""

    def test_schedule_first_review_creates_record(self, student, mastery, db):
        """2026-02-27: schedule_first_review creates a SpacedRepetitionRecord with box=1."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        assert record.box == 1  # 2026-02-27: Always starts in box 1

    def test_schedule_3star_interval(self, student, mastery, db):
        """2026-02-27: 3-star mastery → next_review_date = today + LEITNER_INTERVALS[3][0] = today+3."""
        mastery.best_star_rating = 3
        mastery.save()
        SpacedRepetitionService.schedule_first_review(student, mastery)
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        expected = date.today() + timedelta(days=LEITNER_INTERVALS[3][0])
        assert record.next_review_date == expected  # 2026-02-27: 3-day interval

    def test_schedule_4star_interval(self, student, mastery, db):
        """2026-02-27: 4-star mastery → next_review_date = today + LEITNER_INTERVALS[4][0] = today+7."""
        mastery.best_star_rating = 4
        mastery.save()
        SpacedRepetitionService.schedule_first_review(student, mastery)
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        expected = date.today() + timedelta(days=LEITNER_INTERVALS[4][0])
        assert record.next_review_date == expected  # 2026-02-27: 7-day interval

    def test_schedule_5star_interval(self, student, mastery, db):
        """2026-02-27: 5-star mastery → next_review_date = today + LEITNER_INTERVALS[5][0] = today+14."""
        mastery.best_star_rating = 5
        mastery.save()
        SpacedRepetitionService.schedule_first_review(student, mastery)
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        expected = date.today() + timedelta(days=LEITNER_INTERVALS[5][0])
        assert record.next_review_date == expected  # 2026-02-27: 14-day interval

    def test_schedule_idempotent(self, student, mastery, db):
        """2026-02-27: Calling schedule_first_review twice does not create duplicate records."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        SpacedRepetitionService.schedule_first_review(student, mastery)
        count = SpacedRepetitionRecord.objects.filter(student=student, mastery=mastery).count()
        assert count == 1  # 2026-02-27: Still exactly one record

    def test_complete_review_advances_box(self, student, mastery, db):
        """2026-02-27: Completing a review with 3+ stars increments the Leitner box."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        initial_box = record.box
        SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=4, explanation_seconds=60
        )
        record.refresh_from_db()
        assert record.box > initial_box  # 2026-02-27: Box advanced on pass

    def test_complete_review_reset_on_fail(self, student, mastery, db):
        """2026-02-27: Stars < 3 → box resets to 1, next_review_date = today+3."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        # 2026-02-27: Manually bump box to 3 to confirm reset goes all the way back
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        record.box = 3
        record.save()
        SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=2, explanation_seconds=60
        )
        record.refresh_from_db()
        assert record.box == 1  # 2026-02-27: Reset to box 1
        assert record.next_review_date == date.today() + timedelta(days=3)  # 2026-02-27: 3-day retry


# ── TestReviewQueue ───────────────────────────────────────────────────────

@pytest.mark.django_db
class TestReviewQueue:
    """2026-02-27: Tests for the daily review queue: empty queue, due items,
    future exclusion, cap at 10, explanation length validation,
    outcome return shape, maintenance phase, and consecutive-5-star reset."""

    def test_empty_queue_when_nothing_due(self, student, db):
        """2026-02-27: No records due → get_review_queue returns an empty list."""
        result = SpacedRepetitionService.get_review_queue(student)
        assert result == []  # 2026-02-27: Nothing scheduled

    def test_queue_returns_due_items(self, student, lesson, db):
        """2026-02-27: Two records with next_review_date=today → both appear in queue."""
        for day_num in (1, 2):
            m = ConceptMastery.objects.create(
                student=student, lesson=lesson, day_number=day_num,
                best_star_rating=4, attempts_count=1, is_mastered=True,
            )
            SpacedRepetitionRecord.objects.create(
                student=student, mastery=m, box=1,
                next_review_date=date.today(),
            )
        result = SpacedRepetitionService.get_review_queue(student)
        assert len(result) == 2  # 2026-02-27: Both due today

    def test_queue_excludes_future(self, student, lesson, db):
        """2026-02-27: Record with next_review_date=tomorrow is not returned today."""
        m = ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=1,
            best_star_rating=4, attempts_count=1, is_mastered=True,
        )
        SpacedRepetitionRecord.objects.create(
            student=student, mastery=m, box=1,
            next_review_date=date.today() + timedelta(days=1),
        )
        result = SpacedRepetitionService.get_review_queue(student)
        assert result == []  # 2026-02-27: Tomorrow's item excluded

    def test_queue_capped_at_10(self, student, lesson, db):
        """2026-02-27: 15 due records → queue is capped at 10 items."""
        for day_num in range(1, 6):
            # 2026-02-27: Create a lesson per group to keep lesson_id unique
            extra_lesson = TeachingLesson.objects.create(
                lesson_id=f'ENG1_SPC_CAP_W{day_num:02d}',
                title=f'Cap Lesson {day_num}',
                subject='English',
                class_number=1,
                week_number=day_num,
                status='published',
            )
            for inner in range(1, 4):
                m = ConceptMastery.objects.create(
                    student=student, lesson=extra_lesson, day_number=inner,
                    best_star_rating=3, attempts_count=1, is_mastered=True,
                )
                SpacedRepetitionRecord.objects.create(
                    student=student, mastery=m, box=1,
                    next_review_date=date.today(),
                )
        result = SpacedRepetitionService.get_review_queue(student)
        assert len(result) <= 10  # 2026-02-27: Hard cap enforced

    def test_explanation_seconds_minimum(self, student, mastery, db):
        """2026-02-27: explanation_seconds=20 (below minimum) → error code EXPLANATION_TOO_SHORT."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        result = SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=4, explanation_seconds=20
        )
        assert result.get('success') is False  # 2026-02-27: Rejected
        assert result.get('code') == 'EXPLANATION_TOO_SHORT'  # 2026-02-27: Correct error code

    def test_complete_review_returns_outcome(self, student, mastery, db):
        """2026-02-27: Valid review completion returns success=True and outcome='advanced'."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        result = SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=4, explanation_seconds=60
        )
        assert result.get('success') is True  # 2026-02-27: Accepted
        assert result.get('outcome') == 'advanced'  # 2026-02-27: Box moved forward

    def test_complete_review_maintenance_after_3_consecutive_5star(self, student, mastery, db):
        """2026-02-27: Three consecutive 5-star reviews → record phase becomes 'maintenance'."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        for _ in range(3):
            SpacedRepetitionService.complete_review(
                student=student, mastery_id=str(mastery.id), stars=5, explanation_seconds=60
            )
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        assert record.phase == 'maintenance'  # 2026-02-27: Graduated to maintenance

    def test_complete_review_resets_consecutive_on_non5star(self, student, mastery, db):
        """2026-02-27: Two 5-star reviews then a 4-star review → consecutive_5star_reviews resets to 0."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=5, explanation_seconds=60
        )
        SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=5, explanation_seconds=60
        )
        SpacedRepetitionService.complete_review(
            student=student, mastery_id=str(mastery.id), stars=4, explanation_seconds=60
        )
        record = SpacedRepetitionRecord.objects.get(student=student, mastery=mastery)
        assert record.consecutive_5star_reviews == 0  # 2026-02-27: Reset on non-5-star


# ── TestPacingService ─────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPacingService:
    """2026-02-27: Tests for PacingService: record creation, academic-year
    start date, intensive period, IQ factor, status dict shape, pace
    status labels, and weekly velocity counting."""

    def test_pacing_record_created(self, student, db):
        """2026-02-27: get_or_create_pacing creates a PacingRecord for the student."""
        PacingService.get_or_create_pacing(student)
        assert PacingRecord.objects.filter(student=student).exists()  # 2026-02-27: Record created

    def test_pacing_academic_year_start_june(self, student, db):
        """2026-02-27: academic_year_start is June 1 of the appropriate year."""
        pacing = PacingService.get_or_create_pacing(student)
        assert pacing.academic_year_start.month == 6  # 2026-02-27: June
        assert pacing.academic_year_start.day == 1  # 2026-02-27: First of June

    def test_intensive_end_date_112_days(self, student, db):
        """2026-02-27: intensive_end_date = academic_year_start + 112 days."""
        pacing = PacingService.get_or_create_pacing(student)
        expected = pacing.academic_year_start + timedelta(days=112)
        assert pacing.intensive_end_date == expected  # 2026-02-27: 16-week intensive period

    def test_iq_standard_factor_1(self, student, db):
        """2026-02-27: Standard IQ (no override) → iq_adjustment_factor = 1.0."""
        pacing = PacingService.get_or_create_pacing(student)
        assert pacing.iq_adjustment_factor == 1.0  # 2026-02-27: Neutral factor

    def test_pacing_status_returns_dict(self, student, db):
        """2026-02-27: get_pacing_status returns a dict containing all required keys."""
        status = PacingService.get_pacing_status(student)
        required_keys = {
            'completed_concepts', 'expected_concepts', 'pace_status',
            'weekly_velocity', 'iq_adjustment_factor',
        }
        assert required_keys.issubset(status.keys())  # 2026-02-27: All keys present

    def test_pace_status_on_track(self, student, lesson, db):
        """2026-02-27: completed_concepts ≈ expected → pace_status = 'on_track'."""
        pacing = PacingService.get_or_create_pacing(student)
        # 2026-02-27: Set completed equal to expected so pace is on track
        pacing.completed_concepts = pacing.expected_concepts_to_date
        pacing.save()
        status = PacingService.get_pacing_status(student)
        assert status['pace_status'] == 'on_track'  # 2026-02-27: Matched expected

    def test_pace_status_ahead(self, student, lesson, db):
        """2026-02-27: completed_concepts >> expected → pace_status = 'ahead'."""
        pacing = PacingService.get_or_create_pacing(student)
        # 2026-02-27: Dramatically exceed expected count
        pacing.completed_concepts = (pacing.expected_concepts_to_date or 0) + 20
        pacing.save()
        status = PacingService.get_pacing_status(student)
        assert status['pace_status'] == 'ahead'  # 2026-02-27: Well ahead of schedule

    def test_weekly_velocity_counts_last_7_days(self, student, lesson, db):
        """2026-02-27: 3 ConceptMastery records created today → weekly_velocity = 3."""
        for day_num in (1, 2, 3):
            ConceptMastery.objects.create(
                student=student, lesson=lesson, day_number=day_num,
                best_star_rating=4, attempts_count=1, is_mastered=True,
            )
        status = PacingService.get_pacing_status(student)
        assert status['weekly_velocity'] == 3  # 2026-02-27: All 3 within last 7 days


# ── TestAPI ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAPI:
    """2026-02-27: Integration tests for all Spaced Repetition API endpoints.
    Covers pacing GET, review queue GET, review complete POST, validation
    errors, and auth/authz enforcement."""

    def test_pacing_get_200(self, student_client, student, db):
        """2026-02-27: GET /api/v1/spaced-repetition/pacing/ → 200 OK."""
        response = student_client.get('/api/v1/spaced-repetition/pacing/')
        assert response.status_code == 200  # 2026-02-27: Successful response

    def test_review_queue_get_200(self, student_client, student, db):
        """2026-02-27: GET /api/v1/spaced-repetition/reviews/today/ → 200 with 'reviews' key."""
        response = student_client.get('/api/v1/spaced-repetition/reviews/today/')
        assert response.status_code == 200  # 2026-02-27: Successful response
        assert 'reviews' in response.json()  # 2026-02-27: Required shape key

    def test_review_complete_post_200(self, student_client, student, lesson, mastery, db):
        """2026-02-27: POST complete with valid mastery_id, stars=4, explanation_seconds=60 → 200."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        response = student_client.post(
            '/api/v1/spaced-repetition/reviews/complete/',
            {
                'mastery_id': str(mastery.id),
                'stars': 4,
                'explanation_seconds': 60,
            },
            format='json',
        )
        assert response.status_code == 200  # 2026-02-27: Accepted

    def test_review_complete_missing_fields_400(self, student_client, student, db):
        """2026-02-27: POST /reviews/complete/ without mastery_id → 400 Bad Request."""
        response = student_client.post(
            '/api/v1/spaced-repetition/reviews/complete/',
            {'stars': 4, 'explanation_seconds': 60},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-27: Validation error

    def test_unauthenticated_401(self, db):
        """2026-02-27: GET pacing without auth token → 401 Unauthorized."""
        client = APIClient()
        response = client.get('/api/v1/spaced-repetition/pacing/')
        assert response.status_code == 401  # 2026-02-27: Auth required

    def test_parent_gets_403(self, parent_client, db):
        """2026-02-27: Parent user accessing student-only pacing endpoint → 403 Forbidden."""
        response = parent_client.get('/api/v1/spaced-repetition/pacing/')
        assert response.status_code == 403  # 2026-02-27: Students only

    def test_review_complete_short_explanation_400(self, student_client, student, lesson, mastery, db):
        """2026-02-27: POST complete with explanation_seconds=10 (too short) → 400."""
        SpacedRepetitionService.schedule_first_review(student, mastery)
        response = student_client.post(
            '/api/v1/spaced-repetition/reviews/complete/',
            {
                'mastery_id': str(mastery.id),
                'stars': 4,
                'explanation_seconds': 10,
            },
            format='json',
        )
        assert response.status_code == 400  # 2026-02-27: Explanation too short
