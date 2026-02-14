# 2026-02-14: Tests for Student Dashboard API (BS-STU-001-F, BS-STU-002-F)
# Tests: DailyActivity model, streak logic, star map, dashboard API response

"""
Test suite for the Student Dashboard module:
- DailyActivity model CRUD and qualification logic
- Streak calculation and milestone detection
- Star map generation with lock logic
- Dashboard API response shape and data
"""

import pytest
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from services.learning_engine.models import (
    StudentLearningProfile,
    MicroLesson,
    MicroLessonProgress,
    DailyActivity,
    Lesson,
)

User = get_user_model()


@pytest.fixture
def student_user(db):
    """2026-02-14: Create a test student user."""
    user = User.objects.create_user(
        username='teststudent',
        password='testpass123',
    )
    return user


@pytest.fixture
def student_profile(student_user):
    """2026-02-14: Create a learning profile for the test student."""
    profile, _ = StudentLearningProfile.objects.get_or_create(
        user=student_user,
    )
    return profile


@pytest.fixture
def api_client_auth(student_user):
    """2026-02-14: Authenticated API client."""
    client = APIClient()
    client.force_authenticate(user=student_user)
    return client


@pytest.fixture
def sample_lesson(db):
    """2026-02-14: Create a sample lesson with micro-lessons."""
    lesson = Lesson.objects.create(
        lesson_id='MATH_C1_CH1',
        title='Addition Basics',
        subject='Mathematics',
        class_number=1,
        chapter_id='CH1',
        chapter_name='Numbers',
        status='published',
    )
    micro_lessons = []
    for i in range(1, 6):
        ml = MicroLesson.objects.create(
            lesson=lesson,
            sequence_in_lesson=i,
            micro_lesson_id=f'MATH_C1_CH1_ML{i}',
            title=f'Addition Part {i}',
            is_published=True,
            qa_status='passed',
        )
        micro_lessons.append(ml)
    return lesson, micro_lessons


# ===== DailyActivity Model Tests =====

class TestDailyActivityModel:
    """2026-02-14: Tests for DailyActivity model."""

    @pytest.mark.django_db
    def test_create_daily_activity(self, student_user):
        """2026-02-14: Test creating a daily activity record."""
        activity = DailyActivity.objects.create(
            student=student_user,
            activity_date=date.today(),
            concepts_completed=2,
            questions_answered=15,
            time_spent_minutes=20,
        )
        assert activity.id is not None
        assert activity.student == student_user
        assert activity.activity_date == date.today()
        assert activity.concepts_completed == 2

    @pytest.mark.django_db
    def test_unique_student_date(self, student_user):
        """2026-02-14: Test unique constraint on student + activity_date."""
        DailyActivity.objects.create(
            student=student_user,
            activity_date=date.today(),
        )
        with pytest.raises(Exception):
            DailyActivity.objects.create(
                student=student_user,
                activity_date=date.today(),
            )

    @pytest.mark.django_db
    def test_qualification_concepts(self, student_user):
        """2026-02-14: Test learning day qualification via concept completion."""
        activity = DailyActivity.objects.create(
            student=student_user,
            activity_date=date.today(),
            concepts_completed=1,
            questions_answered=0,
        )
        result = activity.update_qualification()
        assert result is True
        assert activity.qualifies_as_learning_day is True

    @pytest.mark.django_db
    def test_qualification_questions(self, student_user):
        """2026-02-14: Test learning day qualification via questions answered."""
        activity = DailyActivity.objects.create(
            student=student_user,
            activity_date=date.today(),
            concepts_completed=0,
            questions_answered=10,
        )
        result = activity.update_qualification()
        assert result is True
        assert activity.qualifies_as_learning_day is True

    @pytest.mark.django_db
    def test_no_qualification(self, student_user):
        """2026-02-14: Test non-qualifying day."""
        activity = DailyActivity.objects.create(
            student=student_user,
            activity_date=date.today(),
            concepts_completed=0,
            questions_answered=5,
        )
        result = activity.update_qualification()
        assert result is False
        assert activity.qualifies_as_learning_day is False

    @pytest.mark.django_db
    def test_str_representation(self, student_user):
        """2026-02-14: Test string representation."""
        activity = DailyActivity.objects.create(
            student=student_user,
            activity_date=date(2026, 2, 14),
        )
        assert 'teststudent' in str(activity)
        assert '2026-02-14' in str(activity)


# ===== Streak Logic Tests =====

class TestStreakLogic:
    """2026-02-14: Tests for streak calculation."""

    @pytest.mark.django_db
    def test_first_activity_starts_streak(self, student_profile):
        """2026-02-14: First activity sets streak to 1."""
        student_profile.update_streak()
        assert student_profile.current_streak_days == 1
        assert student_profile.last_activity_date == timezone.now().date()

    @pytest.mark.django_db
    def test_consecutive_day_increments(self, student_profile):
        """2026-02-14: Consecutive day increments streak."""
        yesterday = timezone.now().date() - timedelta(days=1)
        student_profile.current_streak_days = 3
        student_profile.last_activity_date = yesterday
        student_profile.save()

        student_profile.update_streak()
        assert student_profile.current_streak_days == 4

    @pytest.mark.django_db
    def test_streak_broken_resets(self, student_profile):
        """2026-02-14: Missing a day resets streak to 1."""
        two_days_ago = timezone.now().date() - timedelta(days=2)
        student_profile.current_streak_days = 10
        student_profile.last_activity_date = two_days_ago
        student_profile.save()

        student_profile.update_streak()
        assert student_profile.current_streak_days == 1

    @pytest.mark.django_db
    def test_same_day_no_change(self, student_profile):
        """2026-02-14: Same day activity does not change streak."""
        student_profile.current_streak_days = 5
        student_profile.last_activity_date = timezone.now().date()
        student_profile.save()

        student_profile.update_streak()
        assert student_profile.current_streak_days == 5

    @pytest.mark.django_db
    def test_longest_streak_updated(self, student_profile):
        """2026-02-14: Longest streak updates when current exceeds it."""
        yesterday = timezone.now().date() - timedelta(days=1)
        student_profile.current_streak_days = 5
        student_profile.longest_streak_days = 5
        student_profile.last_activity_date = yesterday
        student_profile.save()

        student_profile.update_streak()
        assert student_profile.current_streak_days == 6
        assert student_profile.longest_streak_days == 6


# ===== Star Calculation Tests =====

class TestStarCalculation:
    """2026-02-14: Tests for mastery-to-stars conversion."""

    def test_mastery_ranges(self):
        """2026-02-14: Test all mastery score ranges map to correct stars."""
        from services.learning_engine.views import StudentDashboardView
        view = StudentDashboardView()

        assert view._mastery_to_stars(0) == 0
        assert view._mastery_to_stars(19) == 0
        assert view._mastery_to_stars(20) == 1
        assert view._mastery_to_stars(39) == 1
        assert view._mastery_to_stars(40) == 2
        assert view._mastery_to_stars(59) == 2
        assert view._mastery_to_stars(60) == 3
        assert view._mastery_to_stars(79) == 3
        assert view._mastery_to_stars(80) == 4
        assert view._mastery_to_stars(89) == 4
        assert view._mastery_to_stars(90) == 5
        assert view._mastery_to_stars(100) == 5

    def test_streak_milestones(self):
        """2026-02-14: Test milestone detection at correct thresholds."""
        from services.learning_engine.views import StudentDashboardView
        view = StudentDashboardView()

        assert view._get_streak_milestone(3) == 3
        assert view._get_streak_milestone(7) == 7
        assert view._get_streak_milestone(14) == 14
        assert view._get_streak_milestone(30) == 30
        assert view._get_streak_milestone(60) == 60
        assert view._get_streak_milestone(100) == 100
        assert view._get_streak_milestone(5) is None
        assert view._get_streak_milestone(0) is None


# ===== Dashboard API Tests =====

class TestDashboardAPI:
    """2026-02-14: Tests for /api/learning/dashboard/ endpoint."""

    @pytest.mark.django_db
    def test_dashboard_returns_200(self, api_client_auth):
        """2026-02-14: Dashboard endpoint returns 200 for authenticated user."""
        response = api_client_auth.get('/api/learning/dashboard/')
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_dashboard_response_shape(self, api_client_auth):
        """2026-02-14: Dashboard response contains required fields."""
        response = api_client_auth.get('/api/learning/dashboard/')
        data = response.json()

        assert 'student_name' in data
        assert 'avatar_id' in data
        assert 'grade' in data
        assert 'current_streak' in data
        assert 'longest_streak' in data
        assert 'total_stars' in data
        assert 'todays_learning' in data
        assert 'star_map' in data
        assert 'streak_milestone' in data
        assert 'daily_activity' in data

    @pytest.mark.django_db
    def test_dashboard_daily_activity_shape(self, api_client_auth):
        """2026-02-14: Daily activity has correct fields."""
        response = api_client_auth.get('/api/learning/dashboard/')
        activity = response.json()['daily_activity']

        assert 'concepts_completed' in activity
        assert 'questions_answered' in activity
        assert 'time_spent_minutes' in activity

    @pytest.mark.django_db
    def test_dashboard_unauthenticated(self):
        """2026-02-14: Dashboard returns 401 for unauthenticated request."""
        client = APIClient()
        response = client.get('/api/learning/dashboard/')
        assert response.status_code in [401, 403]

    @pytest.mark.django_db
    def test_star_map_with_lessons(self, api_client_auth, sample_lesson, student_user):
        """2026-02-14: Star map includes published lessons grouped by subject."""
        response = api_client_auth.get('/api/learning/dashboard/')
        data = response.json()
        star_map = data['star_map']

        assert 'Mathematics' in star_map
        assert len(star_map['Mathematics']) == 5

    @pytest.mark.django_db
    def test_star_map_lock_logic(self, api_client_auth, sample_lesson, student_user):
        """2026-02-14: Second concept is locked if first has < 3 stars."""
        response = api_client_auth.get('/api/learning/dashboard/')
        data = response.json()
        math_concepts = data['star_map']['Mathematics']

        # 2026-02-14: First concept never locked, second locked if first has 0 stars
        assert math_concepts[0]['locked'] is False
        assert math_concepts[1]['locked'] is True  # prev has 0 stars < 3

    @pytest.mark.django_db
    def test_star_map_unlock_with_mastery(self, api_client_auth, sample_lesson, student_user):
        """2026-02-14: Concepts unlock when previous has >= 3 stars (60%+ mastery)."""
        _, micro_lessons = sample_lesson
        # 2026-02-14: Complete first micro-lesson with 65% mastery (3 stars)
        MicroLessonProgress.objects.create(
            student=student_user,
            micro_lesson=micro_lessons[0],
            status='completed',
            mastery_score=65,
        )

        response = api_client_auth.get('/api/learning/dashboard/')
        math_concepts = response.json()['star_map']['Mathematics']

        assert math_concepts[0]['locked'] is False
        assert math_concepts[0]['stars'] == 3
        assert math_concepts[1]['locked'] is False  # unlocked by 3-star prev

    @pytest.mark.django_db
    def test_total_stars_calculation(self, api_client_auth, sample_lesson, student_user):
        """2026-02-14: Total stars sums across all concepts."""
        _, micro_lessons = sample_lesson
        MicroLessonProgress.objects.create(
            student=student_user,
            micro_lesson=micro_lessons[0],
            status='completed',
            mastery_score=95,  # 5 stars
        )
        MicroLessonProgress.objects.create(
            student=student_user,
            micro_lesson=micro_lessons[1],
            status='completed',
            mastery_score=45,  # 2 stars
        )

        response = api_client_auth.get('/api/learning/dashboard/')
        assert response.json()['total_stars'] == 7  # 5 + 2

    @pytest.mark.django_db
    def test_todays_learning_in_progress(self, api_client_auth, sample_lesson, student_user):
        """2026-02-14: In-progress lessons appear in today's learning."""
        _, micro_lessons = sample_lesson
        MicroLessonProgress.objects.create(
            student=student_user,
            micro_lesson=micro_lessons[0],
            status='in_progress',
            mastery_score=0,
        )

        response = api_client_auth.get('/api/learning/dashboard/')
        todays = response.json()['todays_learning']
        assert any(t['status'] == 'continue' for t in todays)


# ===== Daily Activity API Tests =====

class TestDailyActivityAPI:
    """2026-02-14: Tests for /api/learning/daily-activity/ endpoint."""

    @pytest.mark.django_db
    def test_get_daily_activity(self, api_client_auth):
        """2026-02-14: GET returns today's activity."""
        response = api_client_auth.get('/api/learning/daily-activity/')
        assert response.status_code == 200
        data = response.json()
        assert data['concepts_completed'] == 0
        assert data['questions_answered'] == 0

    @pytest.mark.django_db
    def test_patch_daily_activity(self, api_client_auth):
        """2026-02-14: PATCH increments activity counters."""
        response = api_client_auth.patch(
            '/api/learning/daily-activity/',
            {'concepts_completed': 1, 'questions_answered': 5},
            format='json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['concepts_completed'] == 1
        assert data['questions_answered'] == 5

    @pytest.mark.django_db
    def test_patch_increments(self, api_client_auth):
        """2026-02-14: Multiple PATCH calls increment, not replace."""
        api_client_auth.patch(
            '/api/learning/daily-activity/',
            {'questions_answered': 5},
            format='json',
        )
        response = api_client_auth.patch(
            '/api/learning/daily-activity/',
            {'questions_answered': 3},
            format='json',
        )
        data = response.json()
        assert data['questions_answered'] == 8

    @pytest.mark.django_db
    def test_qualification_triggers_streak(self, api_client_auth, student_user):
        """2026-02-14: Qualifying activity updates streak."""
        response = api_client_auth.patch(
            '/api/learning/daily-activity/',
            {'concepts_completed': 1},
            format='json',
        )
        assert response.json()['qualifies_as_learning_day'] is True

        profile = StudentLearningProfile.objects.get(user=student_user)
        assert profile.current_streak_days >= 1
