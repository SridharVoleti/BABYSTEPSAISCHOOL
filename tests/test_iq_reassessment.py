"""
2026-02-27: Tests for IQ Reassessment service (BS-DIA-003).

Purpose:
    Test rolling 20-concept window evaluation: metric computation,
    outcome determination, level-change application, API endpoint,
    and integration with the mastery practice hook.
"""

import pytest  # 2026-02-27: Pytest framework
from datetime import date  # 2026-02-27: Date for DOB

from django.contrib.auth import get_user_model  # 2026-02-27: User model
from rest_framework.test import APIClient  # 2026-02-27: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-27: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-27: Auth models
from services.diagnostic_service.models import (  # 2026-02-27: Diagnostic models
    DiagnosticResult, DiagnosticSession,
    IQReassessmentWindow, IQReassessmentEvent,
)
from services.diagnostic_service.services import IQReassessmentService  # 2026-02-27: Service
from services.teaching_engine.models import (  # 2026-02-27: Teaching models
    TeachingLesson, StudentLessonProgress, DayProgress, ConceptMastery,
)

User = get_user_model()  # 2026-02-27: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-27: Create a parent user for IQ reassessment tests."""
    user = User.objects.create_user(
        username='parent_reassess', password='testpass123'
    )
    parent = Parent.objects.create(
        user=user,
        phone='+919876540099',
        full_name='Parent Reassess',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-27: Create a student for reassessment tests."""
    user = User.objects.create_user(
        username='student_reassess', password='testpass123'
    )
    return Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='Student Reassess',
        dob=date(2018, 6, 1),
        age_group='6-12',
        grade=3,
        login_method='pin',
    )


@pytest.fixture
def student_client(student):
    """2026-02-27: Authenticated API client for the student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def diagnostic_result(student, db):
    """2026-02-27: Completed diagnostic result placing student at 'standard'."""
    session = DiagnosticSession.objects.create(
        student=student,
        status='completed',
        theta_estimate=0.1,
        items_administered=25,
        total_items=25,
        result_level='standard',
    )
    return DiagnosticResult.objects.create(
        student=student,
        session=session,
        overall_level='standard',
        theta_final=0.1,
        domain_levels={'math': 'standard', 'language': 'standard'},
    )


@pytest.fixture
def lesson(db):
    """2026-02-27: A published teaching lesson for testing."""
    return TeachingLesson.objects.create(
        lesson_id='TEST_W01',
        title='Test Lesson Week 1',
        subject='English',
        class_number=3,
        week_number=1,
        content_json_path='json/teaching/class1/English/week1.json',
        status='published',
    )


def _make_mastery(student, lesson, day_number, stars=5, attempts=1, db=None):
    """2026-02-27: Helper to create a ConceptMastery record."""
    progress, _ = StudentLessonProgress.objects.get_or_create(
        student=student,
        lesson=lesson,
        defaults={'iq_level': 'standard', 'current_day': day_number},
    )
    day_prog, _ = DayProgress.objects.get_or_create(
        lesson_progress=progress,
        day_number=day_number,
        defaults={
            'mastery_star_rating': stars,
            'mastery_passed': True,
            'comprehension_score': 80.0,
        },
    )
    mastery, _ = ConceptMastery.objects.get_or_create(
        student=student,
        lesson=lesson,
        day_number=day_number,
        defaults={
            'best_star_rating': stars,
            'attempts_count': attempts,
            'is_mastered': True,
        },
    )
    return mastery


def _seed_masteries(student, count, stars=5, attempts=1, comprehension=80.0):
    """
    2026-02-27: Seed `count` mastered ConceptMastery records across synthetic lessons.

    Automatically offsets by the number of existing masteries so successive
    calls always create fresh concept-slot records, never duplicates.
    """
    # 2026-02-27: Compute offset from existing records to avoid duplicates across calls
    existing_count = ConceptMastery.objects.filter(student=student).count()
    created = []

    for i in range(count):
        idx = existing_count + i  # 2026-02-27: Global unique index
        lesson_idx = idx // 4 + 1  # 2026-02-27: One lesson per 4 days
        day_num = idx % 4 + 1  # 2026-02-27: Day within lesson (1-4)

        lesson_id = f'SEED_W{lesson_idx:02d}'
        lesson, _ = TeachingLesson.objects.get_or_create(
            lesson_id=lesson_id,
            defaults={
                'title': f'Seed Lesson {lesson_idx}',
                'subject': 'English',
                'class_number': 3,
                'week_number': lesson_idx,
                'content_json_path': 'json/teaching/class1/English/week1.json',
                'status': 'published',
            },
        )

        progress, _ = StudentLessonProgress.objects.get_or_create(
            student=student,
            lesson=lesson,
            defaults={'iq_level': 'standard', 'current_day': day_num},
        )
        DayProgress.objects.get_or_create(
            lesson_progress=progress,
            day_number=day_num,
            defaults={
                'mastery_star_rating': stars,
                'mastery_passed': True,
                'comprehension_score': comprehension,
            },
        )
        mastery, _ = ConceptMastery.objects.get_or_create(
            student=student,
            lesson=lesson,
            day_number=day_num,
            defaults={
                'best_star_rating': stars,
                'attempts_count': attempts,
                'is_mastered': True,
            },
        )
        created.append(mastery)

    return created


# ── Unit tests: _determine_outcome ────────────────────────────────────────

@pytest.mark.unit
class TestDetermineOutcome:
    """2026-02-27: Unit tests for IQReassessmentService._determine_outcome."""

    def test_upgrade_all_conditions_met(self):
        """2026-02-27: Should return 'upgrade' when all upgrade conditions are met."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=4.8, avg_reteaching=1.0, avg_comprehension=85.0,
            current_level='standard',
        )
        assert outcome == 'upgrade'

    def test_upgrade_blocked_at_advanced(self):
        """2026-02-27: Advanced student cannot upgrade further → 'maintain'."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=5.0, avg_reteaching=1.0, avg_comprehension=90.0,
            current_level='advanced',
        )
        assert outcome == 'maintain'

    def test_downgrade_conditions_met(self):
        """2026-02-27: Should return 'downgrade' when downgrade conditions are met."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=1.5, avg_reteaching=4.0, avg_comprehension=30.0,
            current_level='standard',
        )
        assert outcome == 'downgrade'

    def test_downgrade_blocked_at_foundation(self):
        """2026-02-27: Foundation student cannot downgrade → 'maintain'."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=1.0, avg_reteaching=5.0, avg_comprehension=20.0,
            current_level='foundation',
        )
        assert outcome == 'maintain'

    def test_maintain_middle_ground(self):
        """2026-02-27: Neither upgrade nor downgrade → 'maintain'."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=3.5, avg_reteaching=2.0, avg_comprehension=60.0,
            current_level='standard',
        )
        assert outcome == 'maintain'

    def test_upgrade_fails_low_comprehension(self):
        """2026-02-27: High stars but low comprehension → not an upgrade."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=4.8, avg_reteaching=1.0, avg_comprehension=50.0,
            current_level='standard',
        )
        assert outcome == 'maintain'

    def test_upgrade_fails_high_reteaching(self):
        """2026-02-27: High stars but too many reteaching attempts → not an upgrade."""
        outcome = IQReassessmentService._determine_outcome(
            avg_stars=4.9, avg_reteaching=2.5, avg_comprehension=85.0,
            current_level='standard',
        )
        assert outcome == 'maintain'


# ── Unit tests: _apply_outcome_to_level ───────────────────────────────────

@pytest.mark.unit
class TestApplyOutcomeToLevel:
    """2026-02-27: Unit tests for IQReassessmentService._apply_outcome_to_level."""

    def test_upgrade_foundation_to_standard(self):
        """2026-02-27: Foundation + upgrade → standard."""
        assert IQReassessmentService._apply_outcome_to_level('foundation', 'upgrade') == 'standard'

    def test_upgrade_standard_to_advanced(self):
        """2026-02-27: Standard + upgrade → advanced."""
        assert IQReassessmentService._apply_outcome_to_level('standard', 'upgrade') == 'advanced'

    def test_upgrade_advanced_stays_advanced(self):
        """2026-02-27: Advanced + upgrade → still advanced (ceiling)."""
        assert IQReassessmentService._apply_outcome_to_level('advanced', 'upgrade') == 'advanced'

    def test_downgrade_advanced_to_standard(self):
        """2026-02-27: Advanced + downgrade → standard."""
        assert IQReassessmentService._apply_outcome_to_level('advanced', 'downgrade') == 'standard'

    def test_downgrade_standard_to_foundation(self):
        """2026-02-27: Standard + downgrade → foundation."""
        assert IQReassessmentService._apply_outcome_to_level('standard', 'downgrade') == 'foundation'

    def test_downgrade_foundation_stays_foundation(self):
        """2026-02-27: Foundation + downgrade → still foundation (floor)."""
        assert IQReassessmentService._apply_outcome_to_level('foundation', 'downgrade') == 'foundation'

    def test_maintain_keeps_level(self):
        """2026-02-27: Maintain always returns the same level."""
        for lvl in ('foundation', 'standard', 'advanced'):
            assert IQReassessmentService._apply_outcome_to_level(lvl, 'maintain') == lvl


# ── Integration tests: check_and_evaluate ─────────────────────────────────

@pytest.mark.django_db
class TestCheckAndEvaluate:
    """2026-02-27: Integration tests for IQReassessmentService.check_and_evaluate."""

    def test_no_window_below_20(self, student, diagnostic_result, db):
        """2026-02-27: Fewer than 20 masteries → no window evaluated."""
        _seed_masteries(student, 19, stars=5, attempts=1, comprehension=90.0)
        result = IQReassessmentService.check_and_evaluate(student)
        assert result is None
        assert IQReassessmentWindow.objects.filter(student=student).count() == 0

    def test_window_created_at_exactly_20(self, student, diagnostic_result, db):
        """2026-02-27: Exactly 20 masteries → window #1 created."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        result = IQReassessmentService.check_and_evaluate(student)
        assert result is not None
        assert result['window_number'] == 1
        assert IQReassessmentWindow.objects.filter(student=student).count() == 1

    def test_window_not_duplicated(self, student, diagnostic_result, db):
        """2026-02-27: Calling check_and_evaluate twice at 20 → only one window."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)
        IQReassessmentService.check_and_evaluate(student)
        assert IQReassessmentWindow.objects.filter(student=student).count() == 1

    def test_no_window_without_diagnostic_result(self, student, db):
        """2026-02-27: No DiagnosticResult → check skipped silently."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        result = IQReassessmentService.check_and_evaluate(student)
        assert result is None

    def test_upgrade_outcome_recorded(self, student, diagnostic_result, db):
        """2026-02-27: Excellent metrics → window outcome is 'upgrade'."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        result = IQReassessmentService.check_and_evaluate(student)
        assert result['outcome'] == 'upgrade'
        window = IQReassessmentWindow.objects.get(student=student, window_number=1)
        assert window.outcome == 'upgrade'
        assert window.level_before == 'standard'
        assert window.level_after == 'advanced'

    def test_downgrade_outcome_recorded(self, student, diagnostic_result, db):
        """2026-02-27: Struggling metrics → window outcome is 'downgrade'."""
        _seed_masteries(student, 20, stars=1, attempts=5, comprehension=20.0)
        result = IQReassessmentService.check_and_evaluate(student)
        assert result['outcome'] == 'downgrade'
        window = IQReassessmentWindow.objects.get(student=student, window_number=1)
        assert window.level_after == 'foundation'

    def test_single_window_no_level_change(self, student, diagnostic_result, db):
        """2026-02-27: One upgrade window alone → level NOT changed yet."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)
        # 2026-02-27: No event should have been created
        assert IQReassessmentEvent.objects.filter(student=student).count() == 0
        # 2026-02-27: DiagnosticResult level unchanged
        diagnostic_result.refresh_from_db()
        assert diagnostic_result.overall_level == 'standard'

    def test_two_consecutive_upgrade_windows_change_level(
        self, student, diagnostic_result, db
    ):
        """2026-02-27: Two consecutive upgrade windows → level updated to 'advanced'."""
        # 2026-02-27: Window 1 (upgrade)
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        # 2026-02-27: Window 2 (upgrade again) — add 20 more masteries
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        # 2026-02-27: Now level change should have been applied
        diagnostic_result.refresh_from_db()
        assert diagnostic_result.overall_level == 'advanced'
        assert IQReassessmentEvent.objects.filter(
            student=student, direction='upgrade'
        ).count() == 1

    def test_two_consecutive_downgrade_windows_change_level(
        self, student, diagnostic_result, db
    ):
        """2026-02-27: Two consecutive downgrade windows → level updated to 'foundation'."""
        # 2026-02-27: Window 1 (downgrade)
        _seed_masteries(student, 20, stars=1, attempts=5, comprehension=20.0)
        IQReassessmentService.check_and_evaluate(student)

        # 2026-02-27: Window 2 (downgrade again)
        _seed_masteries(student, 20, stars=1, attempts=5, comprehension=20.0)
        IQReassessmentService.check_and_evaluate(student)

        diagnostic_result.refresh_from_db()
        assert diagnostic_result.overall_level == 'foundation'
        assert IQReassessmentEvent.objects.filter(
            student=student, direction='downgrade'
        ).count() == 1

    def test_mixed_windows_no_level_change(self, student, diagnostic_result, db):
        """2026-02-27: Upgrade then downgrade windows → no level change (non-consecutive)."""
        # 2026-02-27: Window 1: upgrade
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        # 2026-02-27: Window 2: downgrade
        _seed_masteries(student, 20, stars=1, attempts=5, comprehension=20.0)
        IQReassessmentService.check_and_evaluate(student)

        assert IQReassessmentEvent.objects.filter(student=student).count() == 0
        diagnostic_result.refresh_from_db()
        assert diagnostic_result.overall_level == 'standard'

    def test_event_has_parent_notified(self, student, diagnostic_result, db):
        """2026-02-27: Confirmed level change marks parent as notified (mock)."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        event = IQReassessmentEvent.objects.get(student=student)
        assert event.parent_notified is True
        assert event.parent_notified_at is not None

    def test_40_masteries_creates_two_windows(self, student, diagnostic_result, db):
        """2026-02-27: 40 masteries evaluated as two separate calls → 2 windows."""
        _seed_masteries(student, 20, stars=3, attempts=2, comprehension=60.0)
        IQReassessmentService.check_and_evaluate(student)
        _seed_masteries(student, 20, stars=3, attempts=2, comprehension=60.0)
        IQReassessmentService.check_and_evaluate(student)
        assert IQReassessmentWindow.objects.filter(student=student).count() == 2


# ── Integration tests: get_history ────────────────────────────────────────

@pytest.mark.django_db
class TestGetHistory:
    """2026-02-27: Tests for IQReassessmentService.get_history."""

    def test_empty_history(self, student, db):
        """2026-02-27: No masteries → empty windows and events lists."""
        history = IQReassessmentService.get_history(student)
        assert history['success'] is True
        assert history['windows'] == []
        assert history['events'] == []
        assert history['total_mastered_concepts'] == 0

    def test_history_reflects_windows(self, student, diagnostic_result, db):
        """2026-02-27: After a window is created, history contains it."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        history = IQReassessmentService.get_history(student)
        assert len(history['windows']) == 1
        assert history['windows'][0]['window_number'] == 1
        assert history['windows'][0]['outcome'] == 'upgrade'

    def test_next_window_at_calculation(self, student, diagnostic_result, db):
        """2026-02-27: next_window_at reflects how many more masteries are needed."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        history = IQReassessmentService.get_history(student)
        assert history['next_window_at'] == 40  # 2026-02-27: Next window at 40

    def test_history_contains_events_after_two_windows(
        self, student, diagnostic_result, db
    ):
        """2026-02-27: After confirmed level change, history contains event."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        history = IQReassessmentService.get_history(student)
        assert len(history['events']) == 1
        assert history['events'][0]['direction'] == 'upgrade'
        assert history['events'][0]['old_level'] == 'standard'
        assert history['events'][0]['new_level'] == 'advanced'


# ── API tests: GET /api/v1/diagnostic/reassessment/history/ ───────────────

@pytest.mark.django_db
class TestIQReassessmentHistoryAPI:
    """2026-02-27: API tests for GET /api/v1/diagnostic/reassessment/history/."""

    def test_unauthenticated_denied(self):
        """2026-02-27: Unauthenticated request → 401."""
        client = APIClient()
        response = client.get('/api/v1/diagnostic/reassessment/history/')
        assert response.status_code == 401

    def test_parent_denied(self, parent_user):
        """2026-02-27: Parent user → 403."""
        client = APIClient()
        token = RefreshToken.for_user(parent_user.user)
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        response = client.get('/api/v1/diagnostic/reassessment/history/')
        assert response.status_code == 403

    def test_student_empty_history(self, student_client):
        """2026-02-27: Student with no masteries → empty history with 200."""
        response = student_client.get('/api/v1/diagnostic/reassessment/history/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['windows'] == []
        assert data['events'] == []
        assert data['total_mastered_concepts'] == 0

    def test_student_history_after_window(self, student, student_client, diagnostic_result, db):
        """2026-02-27: Student with 20 masteries → API returns the window."""
        _seed_masteries(student, 20, stars=5, attempts=1, comprehension=90.0)
        IQReassessmentService.check_and_evaluate(student)

        response = student_client.get('/api/v1/diagnostic/reassessment/history/')
        assert response.status_code == 200
        data = response.json()
        assert len(data['windows']) == 1
        w = data['windows'][0]
        assert w['window_number'] == 1
        assert w['outcome'] == 'upgrade'
        assert 'avg_stars' in w
        assert 'avg_reteaching' in w
        assert 'avg_comprehension' in w
        assert 'created_at' in w

    def test_next_window_at_in_response(self, student_client):
        """2026-02-27: Response includes next_window_at field."""
        response = student_client.get('/api/v1/diagnostic/reassessment/history/')
        assert 'next_window_at' in response.json()
