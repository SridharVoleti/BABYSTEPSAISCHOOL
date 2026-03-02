"""
2026-02-20: Integration tests for Gamification Engine API endpoints (BS-GAM).

15 tests covering authentication, authorization, all 7 API endpoints.
"""

import pytest  # 2026-02-20: Pytest framework
from datetime import date  # 2026-02-20: Student DOB
from unittest.mock import patch  # 2026-02-20: Mock streak

from django.contrib.auth import get_user_model  # 2026-02-20: User model
from rest_framework.test import APIClient  # 2026-02-20: Test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-20: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-20: Auth models
from services.gamification_service.models import (  # 2026-02-20: Models
    StudentGameProfile, CoinLedger,
)
from services.gamification_service.coin_service import earn_coins  # 2026-02-20

User = get_user_model()  # 2026-02-20: Django User model

BASE_URL = '/api/v1/gamification'  # 2026-02-20: API prefix


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-20: Create parent user."""
    user = User.objects.create_user(username='gam_api_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000000401', full_name='Gam API Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-20: Grade 1 student for gamification API tests."""
    user = User.objects.create_user(username='gam_api_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Gam API Student',
        dob=date(2017, 6, 10), age_group='6-12', grade=1,
        login_method='pin',
        language_1='English', language_2='Hindi', language_3='Telugu',
    )


@pytest.fixture
def student_client(student):
    """2026-02-20: Authenticated API client for student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-20: Authenticated API client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def anon_client():
    """2026-02-20: Unauthenticated API client."""
    return APIClient()


# ── Auth tests ────────────────────────────────────────────────────────────────

class TestAuth:
    """2026-02-20: Authentication and authorization checks."""

    def test_unauthenticated_returns_401(self, anon_client, db):
        """2026-02-20: Unauthenticated requests → 401."""
        response = anon_client.get(f'{BASE_URL}/profile/')
        assert response.status_code == 401

    def test_parent_role_returns_403(self, parent_client, db):
        """2026-02-20: Parent users → 403 (student-only endpoints)."""
        response = parent_client.get(f'{BASE_URL}/profile/')
        assert response.status_code == 403


# ── Profile tests ─────────────────────────────────────────────────────────────

class TestProfileView:
    """2026-02-20: GET /profile/ endpoint tests."""

    def test_initial_profile_all_zeros(self, student_client, student, db):
        """2026-02-20: Fresh student has zeroed profile."""
        response = student_client.get(f'{BASE_URL}/profile/')
        assert response.status_code == 200
        data = response.json()
        assert data['coin_balance'] == 0
        assert data['total_stars_earned'] == 0
        assert data['freezes_available'] == 0
        assert data['total_badges_earned'] == 0
        assert data['recent_badges'] == []

    def test_profile_after_activity(self, student_client, student, db):
        """2026-02-20: After earning coins profile shows updated balance."""
        earn_coins(student, 25, 'practice_stars', 'Setup earn')
        response = student_client.get(f'{BASE_URL}/profile/')
        assert response.status_code == 200
        assert response.json()['coin_balance'] == 25


# ── Activity tests ────────────────────────────────────────────────────────────

class TestActivityView:
    """2026-02-20: POST /activity/ endpoint tests."""

    def test_earn_coins_via_activity(self, student_client, student, db):
        """2026-02-20: 4-star activity returns coins_earned=20."""
        response = student_client.post(
            f'{BASE_URL}/activity/',
            {'stars': 4, 'activity_type': 'practice_stars'},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['coins_earned'] == 20
        assert data['new_coin_balance'] >= 20

    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_badge_earned_in_activity(self, mock_streak, student_client, student, db):
        """2026-02-20: streak=7 on activity call → week_warrior in badges_earned."""
        response = student_client.post(
            f'{BASE_URL}/activity/',
            {'stars': 5, 'activity_type': 'practice_stars'},
            format='json',
        )
        assert response.status_code == 200
        badge_ids = [b['badge_id'] for b in response.json()['badges_earned']]
        assert 'week_warrior' in badge_ids

    @patch('services.gamification_service.freeze_service._get_streak', return_value=7)
    @patch('services.gamification_service.badge_service._get_streak', return_value=7)
    def test_freeze_awarded_at_milestone(self, mock_badge_streak, mock_freeze_streak, student_client, student, db):
        """2026-02-20: streak=7 activity → freezes_awarded≥1."""
        response = student_client.post(
            f'{BASE_URL}/activity/',
            {'stars': 3, 'activity_type': 'lesson_complete'},
            format='json',
        )
        assert response.status_code == 200
        assert response.json()['freezes_awarded'] >= 1


# ── Badges tests ──────────────────────────────────────────────────────────────

class TestBadgesView:
    """2026-02-20: GET /badges/ endpoint tests."""

    def test_badges_list_structure(self, student_client, student, db):
        """2026-02-20: Badge list has 'earned' and 'available' keys."""
        response = student_client.get(f'{BASE_URL}/badges/')
        assert response.status_code == 200
        data = response.json()
        assert 'earned' in data
        assert 'available' in data
        assert isinstance(data['earned'], list)
        assert isinstance(data['available'], list)
        assert len(data['available']) == 20  # 2026-02-20: All 20 badges available initially

    def test_earned_badge_in_earned_list(self, student_client, student, db):
        """2026-02-20: After manually earning week_warrior, it appears in 'earned' list."""
        from services.gamification_service.models import Badge, StudentBadge
        badge = Badge.objects.get(badge_id='week_warrior')
        StudentBadge.objects.create(student=student, badge=badge)
        response = student_client.get(f'{BASE_URL}/badges/')
        assert response.status_code == 200
        earned_ids = [b['badge_id'] for b in response.json()['earned']]
        assert 'week_warrior' in earned_ids


# ── CoinLedger tests ──────────────────────────────────────────────────────────

class TestCoinLedgerView:
    """2026-02-20: GET /coins/ledger/ endpoint tests."""

    def test_coin_ledger_200_with_entries(self, student_client, student, db):
        """2026-02-20: Ledger returns 200 with entries list."""
        earn_coins(student, 15, 'practice_stars', 'Test entry')
        response = student_client.get(f'{BASE_URL}/coins/ledger/')
        assert response.status_code == 200
        data = response.json()
        assert 'entries' in data
        assert len(data['entries']) == 1
        assert data['entries'][0]['amount'] == 15

    def test_coin_ledger_max_20(self, student_client, student, db):
        """2026-02-20: Ledger returns at most 20 entries."""
        for i in range(25):
            earn_coins(student, 1, 'other', f'Entry {i}')
        response = student_client.get(f'{BASE_URL}/coins/ledger/')
        assert response.status_code == 200
        assert len(response.json()['entries']) == 20


# ── SpendCoins tests ──────────────────────────────────────────────────────────

class TestSpendCoinsView:
    """2026-02-20: POST /coins/spend/ endpoint tests."""

    def test_spend_coins_success(self, student_client, student, db):
        """2026-02-20: Spending on a valid item with sufficient balance → 200."""
        earn_coins(student, 100, 'practice_stars', 'Spend setup')
        response = student_client.post(
            f'{BASE_URL}/coins/spend/',
            {'item_id': 'avatar_star'},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['new_coin_balance'] == 50  # 100 - 50
        assert 'Star Explorer Frame' in data['item_name']

    def test_spend_coins_insufficient_balance(self, student_client, student, db):
        """2026-02-20: Spending with insufficient coins → 400."""
        earn_coins(student, 10, 'practice_stars', 'Small earn')
        response = student_client.post(
            f'{BASE_URL}/coins/spend/',
            {'item_id': 'avatar_star'},  # costs 50
            format='json',
        )
        assert response.status_code == 400


# ── Freezes tests ─────────────────────────────────────────────────────────────

class TestFreezesView:
    """2026-02-20: GET /freezes/ endpoint tests."""

    def test_freezes_status_with_streak_and_next_milestone(self, student_client, student, db):
        """2026-02-20: Freeze status returns streak, freezes_available, next_milestone."""
        response = student_client.get(f'{BASE_URL}/freezes/')
        assert response.status_code == 200
        data = response.json()
        assert 'freezes_available' in data
        assert 'max_freezes' in data
        assert data['max_freezes'] == 5
        assert 'streak' in data
        assert 'next_milestone' in data

    @patch('services.gamification_service.views._get_streak', return_value=3)
    def test_freezes_next_milestone_is_7(self, mock_streak, student_client, student, db):
        """2026-02-20: streak=3, next milestone should be 7."""
        response = student_client.get(f'{BASE_URL}/freezes/')
        assert response.status_code == 200
        data = response.json()
        assert data['next_milestone'] == 7
