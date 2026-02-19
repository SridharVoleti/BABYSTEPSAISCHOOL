"""
2026-02-19: Integration tests for Parent Dashboard API endpoints.

Purpose:
    Test HTTP-level behaviour: auth, permissions, CRUD, cross-parent
    security, and response shapes for all four endpoints.
"""

import pytest  # 2026-02-19: Test framework
from datetime import date  # 2026-02-19: DOB

from django.contrib.auth import get_user_model  # 2026-02-19: User model
from django.utils import timezone  # 2026-02-19: Timezone-aware now
from rest_framework.test import APIClient  # 2026-02-19: DRF client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-19: JWT

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import (  # 2026-02-19: Teaching models
    TeachingLesson, ConceptMastery, TutoringSession,
)
from services.learning_engine.models import DailyActivity  # 2026-02-19: Learning
from services.parent_dashboard.models import ParentalControls  # 2026-02-19: Our model

User = get_user_model()  # 2026-02-19: Django User model


# ── URL helpers ────────────────────────────────────────────────────────────

DASHBOARD_URL = '/api/v1/parent/dashboard/'


def progress_url(student_id):
    """2026-02-19: Progress detail URL."""
    return f'/api/v1/parent/progress/{student_id}/'


def controls_url(student_id):
    """2026-02-19: Parental controls URL."""
    return f'/api/v1/parent/controls/{student_id}/'


def log_url(student_id):
    """2026-02-19: Conversation log URL."""
    return f'/api/v1/parent/conversation-log/{student_id}/'


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-19: Parent with Django user."""
    user = User.objects.create_user(username='api_parent', password='pass')
    parent = Parent.objects.create(
        user=user, phone='+91800000001', full_name='API Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def parent_client(parent_user):
    """2026-02-19: Authenticated API client for parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def student(parent_user, db):
    """2026-02-19: Active student linked to parent."""
    user = User.objects.create_user(username='api_student', password='pass')
    return Student.objects.create(
        parent=parent_user, user=user,
        full_name='API Student', dob=date(2018, 5, 10),
        age_group='6-12', grade=1, login_method='pin',
    )


@pytest.fixture
def student_client(student):
    """2026-02-19: Authenticated API client for student (should be 403 on parent endpoints)."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def other_parent(db):
    """2026-02-19: Separate parent (for cross-parent security tests)."""
    user = User.objects.create_user(username='other_api_parent', password='pass')
    parent = Parent.objects.create(
        user=user, phone='+91800000002', full_name='Other API Parent',
    )
    return parent


@pytest.fixture
def other_student(other_parent, db):
    """2026-02-19: Student belonging to other_parent."""
    return Student.objects.create(
        parent=other_parent, full_name='Other API Student',
        dob=date(2018, 1, 1), age_group='6-12', grade=2, login_method='pin',
    )


@pytest.fixture
def other_parent_client(other_parent):
    """2026-02-19: Client for other_parent."""
    client = APIClient()
    token = RefreshToken.for_user(other_parent.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
    return client


@pytest.fixture
def lesson(db):
    """2026-02-19: Published teaching lesson."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_W01_API', title='English Week 1 API',
        subject='English', class_number=1, week_number=1,
        content_json_path='json/teaching/class1/English/week1.json',
        status='published',
    )


# ── DashboardView tests ────────────────────────────────────────────────────

class TestParentDashboardOverview:
    """2026-02-19: Tests for GET /api/v1/parent/dashboard/"""

    def test_unauthenticated_returns_401(self, db):
        """2026-02-19: Unauthenticated request is rejected."""
        client = APIClient()
        response = client.get(DASHBOARD_URL)
        assert response.status_code == 401  # 2026-02-19: No credentials

    def test_student_returns_403(self, student_client):
        """2026-02-19: Student cannot access parent dashboard."""
        response = student_client.get(DASHBOARD_URL)
        assert response.status_code == 403  # 2026-02-19: Wrong role

    def test_no_children_returns_empty_list(self, parent_client):
        """2026-02-19: Parent with no students returns empty children array."""
        response = parent_client.get(DASHBOARD_URL)
        assert response.status_code == 200
        assert response.data['children'] == []  # 2026-02-19: No children

    def test_single_child_response_shape(self, parent_client, student, db):
        """2026-02-19: Response contains expected fields per child."""
        response = parent_client.get(DASHBOARD_URL)
        assert response.status_code == 200
        children = response.data['children']
        assert len(children) == 1
        child = children[0]
        assert 'student_id' in child
        assert 'display_name' in child
        assert 'grade' in child
        assert 'streak_days' in child
        assert 'total_stars' in child
        assert 'today_active_minutes' in child
        assert 'today_mastered' in child
        assert 'week_stars' in child
        assert 'week_concepts' in child
        assert 'alerts' in child

    def test_single_child_with_mastery_data(self, parent_client, student, lesson, db):
        """2026-02-19: Mastery data aggregated correctly for single child."""
        ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=1,
            best_star_rating=5, is_mastered=True, attempts_count=1,
        )
        response = parent_client.get(DASHBOARD_URL)
        assert response.status_code == 200
        child = response.data['children'][0]
        assert child['total_stars'] == 5  # 2026-02-19: One mastery record

    def test_multiple_children(self, parent_client, parent_user, student, db):
        """2026-02-19: Multiple active children all appear."""
        # 2026-02-19: Add second child
        Student.objects.create(
            parent=parent_user, full_name='Second Child',
            dob=date(2020, 6, 1), age_group='6-12', grade=2, login_method='pin',
        )
        response = parent_client.get(DASHBOARD_URL)
        assert response.status_code == 200
        assert len(response.data['children']) == 2  # 2026-02-19: Both children


# ── ProgressDetailView tests ───────────────────────────────────────────────

class TestParentProgressDetail:
    """2026-02-19: Tests for GET /api/v1/parent/progress/{student_id}/"""

    def test_unauthenticated_returns_401(self, student, db):
        """2026-02-19: Unauthenticated request is rejected."""
        client = APIClient()
        response = client.get(progress_url(student.id))
        assert response.status_code == 401

    def test_basic_drill_down(self, parent_client, student, lesson, db):
        """2026-02-19: Returns subject-grouped drill-down."""
        ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=1,
            best_star_rating=4, is_mastered=True,
        )
        response = parent_client.get(progress_url(student.id))
        assert response.status_code == 200
        assert 'subjects' in response.data
        assert 'English' in response.data['subjects']

    def test_correct_subject_grouping(self, parent_client, student, lesson, db):
        """2026-02-19: Days grouped under correct lesson within subject."""
        ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=1,
            best_star_rating=3, is_mastered=True,
        )
        ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=2,
            best_star_rating=4, is_mastered=True,
        )
        response = parent_client.get(progress_url(student.id))
        assert response.status_code == 200
        lessons = response.data['subjects']['English']
        assert len(lessons) == 1  # 2026-02-19: One lesson
        assert len(lessons[0]['days']) == 2  # 2026-02-19: Two days

    def test_cross_parent_access_blocked(self, parent_client, other_student, db):
        """2026-02-19: Parent cannot view another parent's student progress."""
        response = parent_client.get(progress_url(other_student.id))
        assert response.status_code == 404  # 2026-02-19: Not found / access denied

    def test_no_progress_returns_empty_subjects(self, parent_client, student, db):
        """2026-02-19: No mastery records → empty subjects dict."""
        response = parent_client.get(progress_url(student.id))
        assert response.status_code == 200
        assert response.data['subjects'] == {}  # 2026-02-19: Empty

    def test_unauthenticated_progress_returns_401(self, student, db):
        """2026-02-19: Unauthenticated progress request rejected."""
        client = APIClient()
        response = client.get(progress_url(student.id))
        assert response.status_code == 401


# ── ParentalControlsView tests ─────────────────────────────────────────────

class TestParentalControls:
    """2026-02-19: Tests for GET/PUT /api/v1/parent/controls/{student_id}/"""

    def test_get_creates_defaults(self, parent_client, student, db):
        """2026-02-19: GET creates default controls if none exist."""
        assert not ParentalControls.objects.filter(student=student).exists()
        response = parent_client.get(controls_url(student.id))
        assert response.status_code == 200
        assert response.data['daily_time_limit_minutes'] == 120  # 2026-02-19: Default
        assert response.data['ai_log_enabled'] is True  # 2026-02-19: Default

    def test_full_update(self, parent_client, student, db):
        """2026-02-19: PUT with all fields updates completely."""
        payload = {
            'daily_time_limit_minutes': 60,
            'schedule_enabled': True,
            'schedule_start_time': '09:00',
            'schedule_end_time': '18:00',
            'ai_log_enabled': False,
        }
        response = parent_client.put(controls_url(student.id), payload, format='json')
        assert response.status_code == 200
        assert response.data['daily_time_limit_minutes'] == 60
        assert response.data['schedule_enabled'] is True
        assert response.data['ai_log_enabled'] is False

    def test_partial_update(self, parent_client, student, db):
        """2026-02-19: PUT with subset of fields updates only those fields."""
        # 2026-02-19: Set up initial state
        parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 30, 'ai_log_enabled': False},
            format='json',
        )
        # 2026-02-19: Partial update
        response = parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 90},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['daily_time_limit_minutes'] == 90
        assert response.data['ai_log_enabled'] is False  # 2026-02-19: Unchanged

    def test_invalid_time_limit_below_minimum(self, parent_client, student, db):
        """2026-02-19: daily_time_limit_minutes < 15 is rejected."""
        response = parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 10},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Validation error

    def test_invalid_time_limit_above_maximum(self, parent_client, student, db):
        """2026-02-19: daily_time_limit_minutes > 480 is rejected."""
        response = parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 500},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-19: Validation error

    def test_cross_parent_blocked(self, parent_client, other_student, db):
        """2026-02-19: Cannot update controls for another parent's student."""
        response = parent_client.put(
            controls_url(other_student.id),
            {'daily_time_limit_minutes': 60},
            format='json',
        )
        assert response.status_code == 404  # 2026-02-19: Access denied

    def test_unauthenticated_returns_401(self, student, db):
        """2026-02-19: Unauthenticated request rejected."""
        client = APIClient()
        response = client.get(controls_url(student.id))
        assert response.status_code == 401

    def test_time_limit_boundary_minimum(self, parent_client, student, db):
        """2026-02-19: daily_time_limit_minutes = 15 is accepted (lower boundary)."""
        response = parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 15},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['daily_time_limit_minutes'] == 15

    def test_time_limit_boundary_maximum(self, parent_client, student, db):
        """2026-02-19: daily_time_limit_minutes = 480 is accepted (upper boundary)."""
        response = parent_client.put(
            controls_url(student.id),
            {'daily_time_limit_minutes': 480},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['daily_time_limit_minutes'] == 480


# ── ConversationLogView tests ──────────────────────────────────────────────

class TestConversationLog:
    """2026-02-19: Tests for GET /api/v1/parent/conversation-log/{student_id}/"""

    def test_empty_log_returns_empty_list(self, parent_client, student, db):
        """2026-02-19: No tutoring sessions → empty sessions array."""
        response = parent_client.get(log_url(student.id))
        assert response.status_code == 200
        assert response.data['sessions'] == []  # 2026-02-19: No sessions

    def test_with_messages(self, parent_client, student, db):
        """2026-02-19: Returns messages from tutoring sessions."""
        TutoringSession.objects.create(
            student=student, day_number=1,
            messages=[
                {'role': 'student', 'text': 'Help me!', 'ts': '2026-02-19T09:00:00'},
                {'role': 'mentor', 'text': 'Sure!', 'ts': '2026-02-19T09:00:05'},
            ],
        )
        response = parent_client.get(log_url(student.id))
        assert response.status_code == 200
        assert len(response.data['sessions']) == 1
        assert len(response.data['sessions'][0]['messages']) == 2

    def test_cross_parent_blocked(self, parent_client, other_student, db):
        """2026-02-19: Cannot access conversation log of another parent's student."""
        response = parent_client.get(log_url(other_student.id))
        assert response.status_code == 404  # 2026-02-19: Access denied

    def test_disabled_log_still_returns(self, parent_client, student, db):
        """2026-02-19: Parents can always see conversation log regardless of ai_log_enabled."""
        # 2026-02-19: Disable log via controls
        ParentalControls.objects.create(student=student, ai_log_enabled=False)
        TutoringSession.objects.create(
            student=student, day_number=2,
            messages=[{'role': 'student', 'text': 'Q?', 'ts': '2026-02-19T10:00:00'}],
        )
        # 2026-02-19: Parent can still access it
        response = parent_client.get(log_url(student.id))
        assert response.status_code == 200
        assert len(response.data['sessions']) == 1  # 2026-02-19: Visible regardless

    def test_unauthenticated_returns_401(self, student, db):
        """2026-02-19: Unauthenticated request rejected."""
        client = APIClient()
        response = client.get(log_url(student.id))
        assert response.status_code == 401
