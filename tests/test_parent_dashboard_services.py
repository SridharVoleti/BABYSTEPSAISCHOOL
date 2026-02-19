"""
2026-02-19: Unit tests for ParentDashboardService.

Purpose:
    Test business logic in isolation: streak, stars aggregation,
    active minutes, today/week mastery, alerts, drill-down grouping,
    parental controls CRUD, and conversation log.
"""

import pytest  # 2026-02-19: Test framework
from datetime import date, timedelta  # 2026-02-19: Date arithmetic
from unittest.mock import patch, PropertyMock  # 2026-02-19: Mocking

from django.contrib.auth import get_user_model  # 2026-02-19: User model
from django.utils import timezone  # 2026-02-19: Timezone-aware now

from services.auth_service.models import Parent, Student  # 2026-02-19: Auth models
from services.teaching_engine.models import (  # 2026-02-19: Teaching models
    TeachingLesson, ConceptMastery, TutoringSession, StudentLessonProgress,
)
from services.learning_engine.models import (  # 2026-02-19: Learning models
    DailyActivity, StudentLearningProfile,
)
from services.parent_dashboard.models import ParentalControls  # 2026-02-19: Our model
from services.parent_dashboard.services import ParentDashboardService  # 2026-02-19: SUT

User = get_user_model()  # 2026-02-19: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-19: Create parent with Django user."""
    user = User.objects.create_user(username='par_svc_parent', password='pass')
    parent = Parent.objects.create(
        user=user, phone='+91900000001', full_name='Svc Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_with_user(parent_user, db):
    """2026-02-19: Create student with a linked Django user."""
    user = User.objects.create_user(username='par_svc_student', password='pass')
    student = Student.objects.create(
        parent=parent_user, user=user,
        full_name='Svc Student', dob=date(2018, 3, 10),
        age_group='6-12', grade=1, login_method='pin',
    )
    return student


@pytest.fixture
def student_no_user(parent_user, db):
    """2026-02-19: Create student WITHOUT a linked Django user."""
    student = Student.objects.create(
        parent=parent_user, user=None,
        full_name='No User Student', dob=date(2018, 3, 10),
        age_group='6-12', grade=2, login_method='pin',
    )
    return student


@pytest.fixture
def lesson(db):
    """2026-02-19: A published teaching lesson."""
    return TeachingLesson.objects.create(
        lesson_id='MATH1_W01_SVC', title='Math Week 1',
        subject='Math', class_number=1, week_number=1,
        content_json_path='json/teaching/class1/Math/week1.json',
        status='published',
    )


# ── Streak tests ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_streak_zero_when_no_learning_profile(parent_user, student_with_user):
    """2026-02-19: streak_days = 0 when student has no learning profile."""
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['streak_days'] == 0  # 2026-02-19: No profile exists


@pytest.mark.django_db
def test_streak_returns_correct_value(parent_user, student_with_user):
    """2026-02-19: streak_days comes from StudentLearningProfile."""
    StudentLearningProfile.objects.create(
        user=student_with_user.user,
        current_streak_days=7,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['streak_days'] == 7  # 2026-02-19: Profile streak


@pytest.mark.django_db
def test_streak_zero_when_no_user(parent_user, student_no_user):
    """2026-02-19: streak_days = 0 when student.user is None."""
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['streak_days'] == 0  # 2026-02-19: Guarded access


# ── Total stars tests ─────────────────────────────────────────────────────

@pytest.mark.django_db
def test_total_stars_zero_when_no_mastery(parent_user, student_with_user):
    """2026-02-19: total_stars = 0 when no ConceptMastery records."""
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['total_stars'] == 0  # 2026-02-19: No mastery


@pytest.mark.django_db
def test_total_stars_aggregation(parent_user, student_with_user, lesson):
    """2026-02-19: total_stars sums all best_star_rating values."""
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=5, is_mastered=True,
    )
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=2,
        best_star_rating=3, is_mastered=True,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['total_stars'] == 8  # 2026-02-19: 5 + 3


# ── Today active minutes tests ────────────────────────────────────────────

@pytest.mark.django_db
def test_today_active_minutes_zero_no_activity(parent_user, student_with_user):
    """2026-02-19: today_active_minutes = 0 when no DailyActivity today."""
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['today_active_minutes'] == 0  # 2026-02-19: No activity


@pytest.mark.django_db
def test_today_active_minutes_from_activity(parent_user, student_with_user):
    """2026-02-19: today_active_minutes matches today's DailyActivity record."""
    today = timezone.now().date()
    DailyActivity.objects.create(
        student=student_with_user.user,
        activity_date=today,
        time_spent_minutes=45,
        concepts_completed=2,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['today_active_minutes'] == 45  # 2026-02-19: From record


# ── Today mastered tests ──────────────────────────────────────────────────

@pytest.mark.django_db
def test_today_mastered_filters_by_date(parent_user, student_with_user, lesson):
    """2026-02-19: today_mastered only includes records updated today with is_mastered=True."""
    # 2026-02-19: One mastered today
    cm_today = ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=4, is_mastered=True,
    )
    # 2026-02-19: One NOT mastered (should be excluded)
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=2,
        best_star_rating=2, is_mastered=False,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert len(child['today_mastered']) == 1  # 2026-02-19: Only mastered one
    assert child['today_mastered'][0]['concept_name'] == 'Math Week 1 Day 1'


# ── Alerts tests ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_alerts_threshold_low_stars_multiple_attempts(parent_user, student_with_user, lesson):
    """2026-02-19: Alert fired when best_star_rating < 3 AND attempts_count >= 2."""
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=2, attempts_count=3, is_mastered=False,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert len(child['alerts']) == 1  # 2026-02-19: One alert
    alert = child['alerts'][0]
    assert alert['type'] == 'low_stars'
    assert alert['stars'] == 2
    assert alert['attempts'] == 3


@pytest.mark.django_db
def test_alerts_no_alert_below_attempt_threshold(parent_user, student_with_user, lesson):
    """2026-02-19: No alert when attempts_count < 2 (even with low stars)."""
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=1, attempts_count=1, is_mastered=False,
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert len(child['alerts']) == 0  # 2026-02-19: Not enough attempts yet


# ── Week concepts test ────────────────────────────────────────────────────

@pytest.mark.django_db
def test_week_concepts_counts_only_mastered(parent_user, student_with_user, lesson):
    """2026-02-19: week_concepts counts only is_mastered=True this week."""
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=5, is_mastered=True,
    )
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=2,
        best_star_rating=2, is_mastered=False,  # 2026-02-19: Not mastered
    )
    data = ParentDashboardService.get_dashboard(parent_user)
    child = data['children'][0]
    assert child['week_concepts'] == 1  # 2026-02-19: Only the mastered one


# ── Progress detail tests ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_get_progress_detail_groups_by_subject(parent_user, student_with_user, lesson):
    """2026-02-19: get_progress_detail groups ConceptMastery by subject."""
    ConceptMastery.objects.create(
        student=student_with_user, lesson=lesson, day_number=1,
        best_star_rating=4, is_mastered=True,
    )
    result = ParentDashboardService.get_progress_detail(parent_user, student_with_user.id)
    assert result is not None
    assert 'Math' in result['subjects']  # 2026-02-19: Grouped by subject
    assert len(result['subjects']['Math']) == 1  # 2026-02-19: One lesson
    assert result['subjects']['Math'][0]['days'][0]['day_number'] == 1


@pytest.mark.django_db
def test_get_progress_detail_cross_parent_blocked(parent_user, db):
    """2026-02-19: Returns None when student_id doesn't belong to this parent."""
    # 2026-02-19: Another parent and student
    other_user = User.objects.create_user(username='other_par_svc', password='pass')
    other_parent = Parent.objects.create(
        user=other_user, phone='+91900000099', full_name='Other Parent',
    )
    other_student = Student.objects.create(
        parent=other_parent, full_name='Other Student',
        dob=date(2018, 1, 1), age_group='6-12', grade=2, login_method='pin',
    )
    result = ParentDashboardService.get_progress_detail(parent_user, other_student.id)
    assert result is None  # 2026-02-19: Cross-parent blocked


@pytest.mark.django_db
def test_get_progress_detail_empty_subjects(parent_user, student_with_user):
    """2026-02-19: Returns empty subjects dict when student has no mastery records."""
    result = ParentDashboardService.get_progress_detail(parent_user, student_with_user.id)
    assert result is not None
    assert result['subjects'] == {}  # 2026-02-19: No mastery yet


# ── Parental controls tests ───────────────────────────────────────────────

@pytest.mark.django_db
def test_get_parental_controls_creates_defaults(parent_user, student_with_user):
    """2026-02-19: get_parental_controls creates default record when none exists."""
    assert not ParentalControls.objects.filter(student=student_with_user).exists()
    controls = ParentDashboardService.get_parental_controls(parent_user, student_with_user.id)
    assert controls is not None
    assert controls.daily_time_limit_minutes == 120  # 2026-02-19: Default
    assert controls.ai_log_enabled is True  # 2026-02-19: Default


@pytest.mark.django_db
def test_update_parental_controls_full(parent_user, student_with_user):
    """2026-02-19: Full update of all controls fields."""
    controls = ParentDashboardService.update_parental_controls(
        parent_user, student_with_user.id,
        {
            'daily_time_limit_minutes': 60,
            'schedule_enabled': True,
            'schedule_start_time': '09:00',
            'schedule_end_time': '17:00',
            'ai_log_enabled': False,
        }
    )
    assert controls.daily_time_limit_minutes == 60
    assert controls.schedule_enabled is True
    assert controls.ai_log_enabled is False


@pytest.mark.django_db
def test_update_parental_controls_partial(parent_user, student_with_user):
    """2026-02-19: Partial update only changes specified fields."""
    # 2026-02-19: Set initial state
    ParentDashboardService.update_parental_controls(
        parent_user, student_with_user.id,
        {'daily_time_limit_minutes': 90, 'ai_log_enabled': False}
    )
    # 2026-02-19: Partial update - only change one field
    controls = ParentDashboardService.update_parental_controls(
        parent_user, student_with_user.id,
        {'daily_time_limit_minutes': 120}
    )
    assert controls.daily_time_limit_minutes == 120  # 2026-02-19: Updated
    assert controls.ai_log_enabled is False  # 2026-02-19: Unchanged


@pytest.mark.django_db
def test_get_controls_cross_parent_blocked(parent_user, db):
    """2026-02-19: Returns None when student belongs to different parent."""
    other_user = User.objects.create_user(username='other_par_ctrl', password='pass')
    other_parent = Parent.objects.create(
        user=other_user, phone='+91900000098', full_name='Other Parent Ctrl',
    )
    other_student = Student.objects.create(
        parent=other_parent, full_name='Other Student Ctrl',
        dob=date(2018, 1, 1), age_group='6-12', grade=2, login_method='pin',
    )
    result = ParentDashboardService.get_parental_controls(parent_user, other_student.id)
    assert result is None  # 2026-02-19: Cross-parent blocked


# ── Conversation log tests ────────────────────────────────────────────────

@pytest.mark.django_db
def test_conversation_log_empty(parent_user, student_with_user):
    """2026-02-19: Empty sessions list when no TutoringSessions exist."""
    result = ParentDashboardService.get_conversation_log(parent_user, student_with_user.id)
    assert result is not None
    assert result['sessions'] == []  # 2026-02-19: No sessions


@pytest.mark.django_db
def test_conversation_log_with_messages(parent_user, student_with_user, lesson, db):
    """2026-02-19: Returns messages from TutoringSession."""
    # 2026-02-19: Create a session with messages (no lesson_progress for simplicity)
    TutoringSession.objects.create(
        student=student_with_user,
        day_number=1,
        messages=[
            {'role': 'student', 'text': 'What is 2+2?', 'ts': '2026-02-19T10:00:00'},
            {'role': 'mentor', 'text': 'It is 4!', 'ts': '2026-02-19T10:00:05'},
        ],
    )
    result = ParentDashboardService.get_conversation_log(parent_user, student_with_user.id)
    assert len(result['sessions']) == 1  # 2026-02-19: One session
    assert len(result['sessions'][0]['messages']) == 2  # 2026-02-19: Two messages


@pytest.mark.django_db
def test_conversation_log_cross_parent_blocked(parent_user, db):
    """2026-02-19: Returns None for student belonging to different parent."""
    other_user = User.objects.create_user(username='other_par_log', password='pass')
    other_parent = Parent.objects.create(
        user=other_user, phone='+91900000097', full_name='Other Parent Log',
    )
    other_student = Student.objects.create(
        parent=other_parent, full_name='Other Student Log',
        dob=date(2018, 1, 1), age_group='6-12', grade=2, login_method='pin',
    )
    result = ParentDashboardService.get_conversation_log(parent_user, other_student.id)
    assert result is None  # 2026-02-19: Cross-parent blocked


# ── No children test ──────────────────────────────────────────────────────

@pytest.mark.django_db
def test_dashboard_no_children_returns_empty(db):
    """2026-02-19: Parent with no active children returns empty children list."""
    user = User.objects.create_user(username='empty_par_svc', password='pass')
    parent = Parent.objects.create(
        user=user, phone='+91900000002', full_name='Empty Parent',
    )
    data = ParentDashboardService.get_dashboard(parent)
    assert data['children'] == []  # 2026-02-19: No children
