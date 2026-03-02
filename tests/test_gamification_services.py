"""
2026-02-20: Unit tests for Gamification Engine service layer (BS-GAM).

20 tests covering:
- TestBadgeService (6): badge award, deduplication, bonus coins
- TestCoinService (6): earn, accumulate, spend, insufficient, immutability, concurrency
- TestFreezeService (4): award at milestones, deduplication, apply
- TestGamificationService (4): process_activity shape, profile auto-create, accumulation
"""

import pytest  # 2026-02-20: Pytest framework
from concurrent.futures import ThreadPoolExecutor  # 2026-02-20: Concurrent spend test
from datetime import date  # 2026-02-20: DOB for student fixture
from unittest.mock import patch  # 2026-02-20: Mock streak value

from django.contrib.auth import get_user_model  # 2026-02-20: User model

from rest_framework.exceptions import ValidationError  # 2026-02-20: Error type

from services.auth_service.models import Parent, Student  # 2026-02-20: Auth models
from services.gamification_service.models import (  # 2026-02-20: Models
    Badge, CoinLedger, FreezeLedger, StudentBadge, StudentGameProfile,
)
from services.gamification_service.coin_service import earn_coins, spend_coins  # 2026-02-20
from services.gamification_service.freeze_service import (  # 2026-02-20
    check_and_award_freezes, apply_freeze,
)
from services.gamification_service.badge_service import check_and_award_badges  # 2026-02-20
from services.gamification_service.services import GamificationService  # 2026-02-20

User = get_user_model()  # 2026-02-20: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-20: Create parent user."""
    user = User.objects.create_user(username='gam_svc_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000000301', full_name='Gam Svc Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-20: Grade 1 student for gamification tests."""
    user = User.objects.create_user(username='gam_svc_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Gam Svc Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1,
        login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )


@pytest.fixture
def second_student(parent_user, db):
    """2026-02-20: Second student for concurrent spend test."""
    user = User.objects.create_user(username='gam_svc_student2', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Gam Svc Student 2',
        dob=date(2017, 6, 10), age_group='6-12', grade=1,
        login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )


# ── TestCoinService ────────────────────────────────────────────────────────────

class TestCoinService:
    """2026-02-20: Tests for earn_coins and spend_coins."""

    def test_earn_coins_updates_balance(self, student, db):
        """2026-02-20: Earning 20 coins sets balance=20 and creates 1 ledger row."""
        balance = earn_coins(student, 20, 'practice_stars', 'Test earn')
        assert balance == 20
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.coin_balance == 20
        assert CoinLedger.objects.filter(student=student).count() == 1

    def test_earn_coins_accumulates(self, student, db):
        """2026-02-20: Two earn calls accumulate correctly."""
        earn_coins(student, 10, 'practice_stars', 'First')
        balance = earn_coins(student, 15, 'lesson_complete', 'Second')
        assert balance == 25
        assert CoinLedger.objects.filter(student=student).count() == 2

    def test_spend_coins_deducts(self, student, db):
        """2026-02-20: Earn 50, spend 30 → balance=20, 2 ledger rows."""
        earn_coins(student, 50, 'practice_stars', 'Earn')
        balance = spend_coins(student, 30, 'freeze_spend', 'Spend')
        assert balance == 20
        assert CoinLedger.objects.filter(student=student).count() == 2
        last = CoinLedger.objects.filter(student=student).order_by('-created_at').first()
        assert last.amount == -30

    def test_spend_coins_insufficient_balance(self, student, db):
        """2026-02-20: Spending more than balance raises ValidationError."""
        earn_coins(student, 10, 'practice_stars', 'Small earn')
        with pytest.raises(ValidationError, match='Insufficient coins'):
            spend_coins(student, 30, 'freeze_spend', 'Too much')

    def test_coin_ledger_immutable(self, student, db):
        """2026-02-20: Ledger rows have no updated_at — they are created once."""
        earn_coins(student, 20, 'other', 'Immutable check')
        row = CoinLedger.objects.filter(student=student).first()
        # 2026-02-20: CoinLedger has no 'updated_at' field (structural test)
        assert not hasattr(row, 'updated_at')

    def test_concurrent_spend_safety(self, student, db):
        """2026-02-20: Sequential double-spend: balance=30, spend 20 twice → second fails."""
        # 2026-02-20: SQLite does not support true concurrent select_for_update; test sequential
        earn_coins(student, 30, 'practice_stars', 'Initial earn')
        spend_coins(student, 20, 'freeze_spend', 'First spend')
        with pytest.raises(ValidationError, match='Insufficient coins'):
            spend_coins(student, 20, 'freeze_spend', 'Second spend fails')
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.coin_balance == 10


# ── TestFreezeService ─────────────────────────────────────────────────────────

class TestFreezeService:
    """2026-02-20: Tests for check_and_award_freezes and apply_freeze."""

    @patch('services.gamification_service.freeze_service._get_streak', return_value=7)
    def test_freeze_awarded_at_7_day_streak(self, mock_streak, student, db):
        """2026-02-20: streak=7 awards 1 freeze token."""
        awarded = check_and_award_freezes(student)
        assert awarded == 1
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.freezes_available == 1

    @patch('services.gamification_service.freeze_service._get_streak', return_value=7)
    def test_freeze_not_duplicated(self, mock_streak, student, db):
        """2026-02-20: Calling twice with streak=7 awards exactly 1 freeze total."""
        check_and_award_freezes(student)
        awarded2 = check_and_award_freezes(student)
        assert awarded2 == 0  # 2026-02-20: Second call awards nothing
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.freezes_available == 1

    @patch('services.gamification_service.freeze_service._get_streak', return_value=30)
    def test_freeze_milestones_30_day(self, mock_streak, student, db):
        """2026-02-20: streak=30 awards all 3 milestones: 1+1+2=4 total."""
        awarded = check_and_award_freezes(student)
        assert awarded == 4
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.freezes_available == 4

    def test_apply_freeze_decrements(self, student, db):
        """2026-02-20: Applying a freeze decrements freezes_available by 1."""
        profile, _ = StudentGameProfile.objects.get_or_create(student=student)
        profile.freezes_available = 2
        profile.save()
        result = apply_freeze(student)
        assert result['freezes_remaining'] == 1
        profile.refresh_from_db()
        assert profile.freezes_available == 1
        assert FreezeLedger.objects.filter(
            student=student, event_type='applied'
        ).count() == 1


# ── TestBadgeService ──────────────────────────────────────────────────────────

class TestBadgeService:
    """2026-02-20: Tests for check_and_award_badges."""

    def test_first_step_badge_awarded(self, student, db):
        """2026-02-20: After 1 completed DayProgress, first_step badge is awarded."""
        from services.teaching_engine.models import TeachingLesson, StudentLessonProgress, DayProgress
        lesson = TeachingLesson.objects.create(
            lesson_id='GAM_TEST_W01', title='Test', subject='English',
            class_number=1, week_number=1,
            content_json_path='json/teaching/class1/English/week1.json',
            status='published',
        )
        sp = StudentLessonProgress.objects.create(
            student=student, lesson=lesson, current_day=2,
        )
        DayProgress.objects.create(
            lesson_progress=sp, day_number=1, status='completed',
        )
        badges = check_and_award_badges(student)
        badge_ids = [b['badge_id'] for b in badges]
        assert 'first_step' in badge_ids

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_week_warrior_badge_awarded(self, mock_streak, student, db):
        """2026-02-20: streak=7 awards week_warrior badge."""
        badges = check_and_award_badges(student)
        badge_ids = [b['badge_id'] for b in badges]
        assert 'week_warrior' in badge_ids

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_badge_not_duplicated(self, mock_streak, student, db):
        """2026-02-20: Calling check_and_award_badges twice awards badge only once."""
        check_and_award_badges(student)
        badges2 = check_and_award_badges(student)
        week_warrior_again = [b for b in badges2 if b['badge_id'] == 'week_warrior']
        assert len(week_warrior_again) == 0
        assert StudentBadge.objects.filter(
            student=student, badge__badge_id='week_warrior'
        ).count() == 1

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_multiple_badges_at_once(self, mock_streak, student, db):
        """2026-02-20: streak=7 + 5-star practice → two badges in one call."""
        from services.teaching_engine.models import PracticeSession
        from services.teaching_engine.models import TeachingLesson, StudentLessonProgress, DayProgress
        lesson = TeachingLesson.objects.create(
            lesson_id='GAM_TEST2_W01', title='Test2', subject='English',
            class_number=1, week_number=1,
            content_json_path='json/teaching/class1/English/week1.json',
            status='published',
        )
        sp = StudentLessonProgress.objects.create(student=student, lesson=lesson, current_day=2)
        DayProgress.objects.create(lesson_progress=sp, day_number=1, status='completed')
        PracticeSession.objects.create(
            student=student, lesson_progress=sp, day_number=1,
            star_rating=5, status='completed',
        )
        badges = check_and_award_badges(student)
        badge_ids = [b['badge_id'] for b in badges]
        assert 'week_warrior' in badge_ids
        assert 'shooting_star' in badge_ids

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_badge_bonus_coins_earned(self, mock_streak, student, db):
        """2026-02-20: Earning week_warrior badge creates a badge_bonus CoinLedger row."""
        check_and_award_badges(student)
        bonus_rows = CoinLedger.objects.filter(
            student=student, event_type='badge_bonus'
        )
        assert bonus_rows.count() >= 1
        assert bonus_rows.filter(amount=10).exists()

    @patch('services.gamification_service.badge_service._get_streak', return_value=5)
    def test_badge_criterion_not_met(self, mock_streak, student, db):
        """2026-02-20: streak=5 does NOT award week_warrior (requires streak≥7)."""
        badges = check_and_award_badges(student)
        badge_ids = [b['badge_id'] for b in badges]
        assert 'week_warrior' not in badge_ids


# ── TestGamificationService ───────────────────────────────────────────────────

class TestGamificationService:
    """2026-02-20: Tests for GamificationService.process_activity."""

    def test_process_activity_4_stars(self, student, db):
        """2026-02-20: 4-star practice activity earns 20 coins, returns correct shape."""
        result = GamificationService.process_activity(
            student=student, stars=4, activity_type='practice_stars'
        )
        assert result['coins_earned'] == 20
        assert result['new_coin_balance'] >= 20
        assert isinstance(result['new_badges'], list)
        assert isinstance(result['freezes_awarded'], int)

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_process_activity_5_stars_with_badge(self, mock_streak, student, db):
        """2026-02-20: 5-star activity earns 30 coins + badge bonus + badges returned."""
        result = GamificationService.process_activity(
            student=student, stars=5, activity_type='practice_stars'
        )
        assert result['coins_earned'] == 30
        # 2026-02-20: Badge bonuses add 10 per badge, so balance > 30
        assert result['new_coin_balance'] > 30
        assert any(b['badge_id'] == 'week_warrior' for b in result['new_badges'])

    def test_process_activity_creates_profile(self, student, db):
        """2026-02-20: process_activity auto-creates StudentGameProfile if absent."""
        assert not StudentGameProfile.objects.filter(student=student).exists()
        GamificationService.process_activity(
            student=student, stars=3, activity_type='lesson_complete'
        )
        assert StudentGameProfile.objects.filter(student=student).exists()

    def test_total_stars_accumulated(self, student, db):
        """2026-02-20: Two 4-star activities → total_stars_earned=8."""
        GamificationService.process_activity(student=student, stars=4, activity_type='practice_stars')
        GamificationService.process_activity(student=student, stars=4, activity_type='vocab_session')
        profile = StudentGameProfile.objects.get(student=student)
        assert profile.total_stars_earned == 8
