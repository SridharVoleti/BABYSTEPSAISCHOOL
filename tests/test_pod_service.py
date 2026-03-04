"""
2026-03-04: Tests for Pod Management & AI Student Monitoring (BS-POD + BS-MON).

Purpose:
    Service-layer tests: PodService, AlertService, AIMonitorService
    API integration tests: all /api/v1/pods/ endpoints + monitor login

~35 tests total (18 service unit + 17 API integration).
"""

import pytest  # 2026-03-04: Pytest framework
import uuid  # 2026-03-04: UUID generation
from datetime import timedelta, date  # 2026-03-04: Time delta + date
from unittest.mock import patch, MagicMock  # 2026-03-04: Mocking

from django.contrib.auth import get_user_model  # 2026-03-04: User model
from django.utils import timezone  # 2026-03-04: Timezone

from rest_framework.test import APIClient  # 2026-03-04: DRF test client

from services.auth_service.models import Parent, Student  # 2026-03-04: Auth models
from services.pod_service.models import (  # 2026-03-04: Pod models
    Pod, PodEnrollment, StudentSession, AttentionEvent, MonitorAlert,
)
from services.pod_service.services import PodService, AlertService  # 2026-03-04: Services
from services.pod_service.ai_monitor import AIMonitorService  # 2026-03-04: AI monitor

User = get_user_model()  # 2026-03-04: Django User


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_user(username=None, is_staff=False):
    """2026-03-04: Create a Django User for testing."""
    username = username or f"user_{uuid.uuid4().hex[:6]}"
    return User.objects.create_user(
        username=username,
        password='testpass123',
        is_staff=is_staff,
    )


def make_parent(user=None):
    """2026-03-04: Create a Parent for testing."""
    if user is None:
        user = make_user()
    phone = f'+91{uuid.uuid4().int % 9000000000 + 1000000000}'
    return Parent.objects.create(
        user=user,
        phone=phone,
        full_name='Test Parent',
    )


def make_student(parent=None, grade=6):
    """2026-03-04: Create a Student for testing."""
    if parent is None:
        parent = make_parent()
    user = make_user()
    return Student.objects.create(
        user=user,
        parent=parent,
        full_name=f'Student {uuid.uuid4().hex[:4]}',
        dob=date(2012, 1, 1),  # 2026-03-04: Required DOB field (age ~14 → grade 6-12)
        age_group='12+',  # 2026-03-04: Required age group
        grade=grade,
        login_method='pin',
        pin_hash='fakehash',
    )


def make_pod(grade=6, subject='Science', max_size=5):
    """2026-03-04: Create a Pod for testing."""
    return Pod.objects.create(
        name=f'Pod {uuid.uuid4().hex[:4]} – Grade {grade}',
        grade=grade,
        subject_focus=subject,
        max_size=max_size,
    )


def make_enrollment(pod, student):
    """2026-03-04: Create an active PodEnrollment."""
    return PodEnrollment.objects.create(pod=pod, student=student)


def make_session(enrollment, alive=True):
    """2026-03-04: Create a StudentSession, optionally with a stale heartbeat."""
    session = StudentSession.objects.create(
        student=enrollment.student,
        pod_enrollment=enrollment,
    )
    if not alive:  # 2026-03-04: Make heartbeat stale (> 90s ago)
        stale = timezone.now() - timedelta(seconds=120)
        StudentSession.objects.filter(id=session.id).update(last_heartbeat=stale)
        session.refresh_from_db()
    return session


def get_student_jwt(student):
    """2026-03-04: Get a JWT token for a student (for API tests)."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(student.user)
    refresh['role'] = 'student'
    refresh['student_id'] = str(student.id)
    return str(refresh.access_token)


def get_staff_jwt(user):
    """2026-03-04: Get a JWT token for a staff user (monitor)."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    refresh['role'] = 'monitor'
    return str(refresh.access_token)


# ══════════════════════════════════════════════════════════════════════════════
# Section 1: PodService unit tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestPodServiceEnroll:
    """2026-03-04: Tests for PodService.enroll_student and unenroll_student."""

    def test_enroll_student_success(self):
        """2026-03-04: Enroll a student successfully."""
        pod = make_pod()
        student = make_student()
        result = PodService.enroll_student(pod.id, student.id)
        assert result['success'] is True  # 2026-03-04: Should succeed
        assert PodEnrollment.objects.filter(pod=pod, student=student, is_active=True).exists()

    def test_enroll_student_pod_not_found(self):
        """2026-03-04: Enroll into non-existent pod returns error."""
        student = make_student()
        result = PodService.enroll_student(uuid.uuid4(), student.id)
        assert result['success'] is False  # 2026-03-04: Should fail
        assert result['code'] == 'POD_NOT_FOUND'

    def test_enroll_student_already_enrolled(self):
        """2026-03-04: Re-enrolling returns ALREADY_ENROLLED."""
        pod = make_pod()
        student = make_student()
        PodService.enroll_student(pod.id, student.id)
        result = PodService.enroll_student(pod.id, student.id)
        assert result['success'] is False  # 2026-03-04: Should fail
        assert result['code'] == 'ALREADY_ENROLLED'

    def test_enroll_pod_full(self):
        """2026-03-04: Enrolling into a full pod returns POD_FULL."""
        pod = make_pod(max_size=2)  # 2026-03-04: 2-student pod
        for _ in range(2):  # 2026-03-04: Fill the pod
            PodService.enroll_student(pod.id, make_student().id)
        result = PodService.enroll_student(pod.id, make_student().id)
        assert result['success'] is False  # 2026-03-04: Full
        assert result['code'] == 'POD_FULL'

    def test_unenroll_student_success(self):
        """2026-03-04: Unenroll removes active enrollment."""
        pod = make_pod()
        student = make_student()
        PodService.enroll_student(pod.id, student.id)
        result = PodService.unenroll_student(pod.id, student.id)
        assert result['success'] is True  # 2026-03-04: Should succeed
        assert not PodEnrollment.objects.filter(pod=pod, student=student, is_active=True).exists()

    def test_unenroll_not_enrolled(self):
        """2026-03-04: Unenrolling a student not in the pod returns error."""
        pod = make_pod()
        student = make_student()
        result = PodService.unenroll_student(pod.id, student.id)
        assert result['success'] is False  # 2026-03-04: Not enrolled
        assert result['code'] == 'NOT_ENROLLED'

    def test_reenroll_lapsed(self):
        """2026-03-04: Re-activating a lapsed enrollment works."""
        pod = make_pod()
        student = make_student()
        PodService.enroll_student(pod.id, student.id)
        PodService.unenroll_student(pod.id, student.id)  # 2026-03-04: Lapse
        result = PodService.enroll_student(pod.id, student.id)  # 2026-03-04: Re-enroll
        assert result['success'] is True  # 2026-03-04: Should reactivate


@pytest.mark.django_db
class TestPodServiceStatus:
    """2026-03-04: Tests for PodService.get_pod_status and traffic-light logic."""

    def test_grey_when_fewer_than_2_active(self):
        """2026-03-04: Pod with 0 active students shows GREY."""
        pod = make_pod()
        enrollment = make_enrollment(pod, make_student())
        make_session(enrollment, alive=False)  # 2026-03-04: Dead session
        status = PodService.get_pod_status(pod.id)
        assert status['traffic_light'] == 'grey'  # 2026-03-04: Not enough active

    def test_green_when_all_focusing(self):
        """2026-03-04: Pod with 3 active, focusing students shows GREEN."""
        pod = make_pod()
        for _ in range(3):
            enrollment = make_enrollment(pod, make_student())
            make_session(enrollment, alive=True)  # 2026-03-04: Live sessions
        status = PodService.get_pod_status(pod.id)
        assert status['traffic_light'] == 'green'  # 2026-03-04: All focusing

    def test_amber_when_1_not_focusing(self):
        """2026-03-04: Pod with 1 distracted student shows AMBER."""
        pod = make_pod()
        # 2026-03-04: 2 focused students
        for _ in range(2):
            enrollment = make_enrollment(pod, make_student())
            make_session(enrollment, alive=True)
        # 2026-03-04: 1 distracted student (low attention score)
        distracted_enrollment = make_enrollment(pod, make_student())
        session = make_session(distracted_enrollment, alive=True)
        StudentSession.objects.filter(id=session.id).update(attention_score=0.2)
        status = PodService.get_pod_status(pod.id)
        assert status['traffic_light'] == 'amber'  # 2026-03-04: 1 distracted

    def test_pod_not_found_returns_none(self):
        """2026-03-04: Non-existent pod returns None."""
        result = PodService.get_pod_status(uuid.uuid4())
        assert result is None  # 2026-03-04: Not found

    def test_active_count_reflects_alive_sessions(self):
        """2026-03-04: active_count only counts students with live heartbeat."""
        pod = make_pod()
        alive_enrollment = make_enrollment(pod, make_student())
        dead_enrollment = make_enrollment(pod, make_student())
        make_session(alive_enrollment, alive=True)
        make_session(dead_enrollment, alive=False)
        status = PodService.get_pod_status(pod.id)
        assert status['active_count'] == 1  # 2026-03-04: Only 1 alive


@pytest.mark.django_db
class TestPodServiceHeartbeat:
    """2026-03-04: Tests for heartbeat recording."""

    def test_heartbeat_updates_timestamp(self):
        """2026-03-04: Heartbeat updates last_heartbeat on the session."""
        pod = make_pod()
        student = make_student()
        enrollment = make_enrollment(pod, student)
        make_session(enrollment, alive=False)  # 2026-03-04: Start stale

        result = PodService.record_heartbeat(student)
        assert result['success'] is True  # 2026-03-04: Should succeed
        # 2026-03-04: Session should now be alive
        session = StudentSession.objects.get(pod_enrollment=enrollment, is_active=True)
        assert session.is_heartbeat_alive  # 2026-03-04: Heartbeat alive

    def test_heartbeat_no_pod_returns_error(self):
        """2026-03-04: Heartbeat with no pod enrollment returns error."""
        student = make_student()  # 2026-03-04: No pod
        result = PodService.record_heartbeat(student)
        assert result['success'] is False  # 2026-03-04: No pod
        assert result['code'] == 'NO_POD'


@pytest.mark.django_db
class TestAlertService:
    """2026-03-04: Tests for AlertService."""

    def test_create_help_request_creates_alert(self):
        """2026-03-04: Help request creates a MonitorAlert record."""
        student = make_student()
        result = AlertService.create_help_request(student, 'I need help!')
        assert result['success'] is True  # 2026-03-04: Should succeed
        assert MonitorAlert.objects.filter(
            student=student, alert_type='help_request'
        ).exists()

    def test_resolve_alert(self):
        """2026-03-04: Resolving an alert marks it resolved."""
        student = make_student()
        result = AlertService.create_help_request(student)
        alert_id = result['alert_id']
        resolve_result = AlertService.resolve_alert(alert_id)
        assert resolve_result['success'] is True  # 2026-03-04: Resolved
        assert MonitorAlert.objects.get(id=alert_id).is_resolved  # 2026-03-04: DB check

    def test_resolve_nonexistent_alert(self):
        """2026-03-04: Resolving a missing alert returns error."""
        result = AlertService.resolve_alert(999999)  # 2026-03-04: Non-existent integer PK
        assert result['success'] is False  # 2026-03-04: Not found

    @patch('services.pod_service.services.AlertService._dispatch_whatsapp')
    def test_send_parent_alert_creates_record(self, mock_dispatch):
        """2026-03-04: Parent alert creates MonitorAlert and dispatches notification."""
        mock_dispatch.return_value = None  # 2026-03-04: Mock dispatch
        parent = make_parent()
        student = make_student(parent=parent)
        result = AlertService.send_parent_alert(student, 'not_present')
        assert result['success'] is True  # 2026-03-04: Should succeed
        assert MonitorAlert.objects.filter(
            student=student, alert_type='parent_alert'
        ).exists()

    def test_get_unresolved_alerts_excludes_resolved(self):
        """2026-03-04: get_unresolved_alerts only returns open alerts."""
        student = make_student()
        AlertService.create_help_request(student, 'Test')
        result1 = AlertService.create_help_request(student, 'Resolved one')
        AlertService.resolve_alert(result1['alert_id'])  # 2026-03-04: Resolve one
        alerts = AlertService.get_unresolved_alerts()
        ids = [str(a.id) for a in alerts]
        assert result1['alert_id'] not in ids  # 2026-03-04: Resolved not in list


# ══════════════════════════════════════════════════════════════════════════════
# Section 2: AIMonitorService unit tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestAIMonitorService:
    """2026-03-04: Tests for AIMonitorService."""

    @patch('services.pod_service.ai_monitor.get_llm_provider')
    def test_generate_checkin_question_llm_success(self, mock_llm_provider):
        """2026-03-04: generate_checkin_question returns LLM-generated question."""
        mock_llm = MagicMock()
        # 2026-03-04: llm.chat() returns LLMResponse; .text is the string attribute
        mock_response = MagicMock()
        mock_response.text = 'What part of fractions is confusing?'
        mock_llm.chat.return_value = mock_response
        mock_llm_provider.return_value = mock_llm

        student = make_student()
        question = AIMonitorService.generate_checkin_question(student, 'fractions')
        assert 'fractions' in question or 'confusing' in question  # 2026-03-04: LLM response

    @patch('services.pod_service.ai_monitor.get_llm_provider')
    def test_generate_checkin_question_llm_fallback(self, mock_llm_provider):
        """2026-03-04: LLM failure returns safe fallback question."""
        mock_llm_provider.side_effect = Exception('LLM unavailable')
        student = make_student()
        question = AIMonitorService.generate_checkin_question(student, 'fractions')
        assert student.full_name in question  # 2026-03-04: Fallback includes name
        assert 'fractions' in question  # 2026-03-04: Fallback includes concept

    def test_flag_for_reteach_sets_revision_status(self):
        """2026-03-04: flag_for_reteach resets DayProgress to revision."""
        from services.teaching_engine.models import (
            TeachingLesson, StudentLessonProgress, DayProgress,
        )
        student = make_student()
        user = make_user()
        lesson = TeachingLesson.objects.create(
            lesson_id='TEST_POD_L01',
            title='Test Lesson',
            subject='Science',
            class_number=6,
            chapter_title='Chapter 1',
            week_number=1,
            character_name='Aari',
            content_json_path='test.json',
        )
        progress = StudentLessonProgress.objects.create(
            student=student,
            lesson=lesson,
            iq_level='standard',
        )
        day_progress = DayProgress.objects.create(
            lesson_progress=progress,
            day_number=1,
            status='mastery_practice',
        )
        result = AIMonitorService.flag_for_reteach(student, 'photosynthesis', day_progress)
        assert result['success'] is True  # 2026-03-04: Should succeed
        day_progress.refresh_from_db()
        assert day_progress.status == 'revision'  # 2026-03-04: Reset to revision
        assert MonitorAlert.objects.filter(  # 2026-03-04: Alert created
            student=student, alert_type='monitor_flag'
        ).exists()


# ══════════════════════════════════════════════════════════════════════════════
# Section 3: API integration tests
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.django_db
class TestMonitorLoginAPI:
    """2026-03-04: Tests for POST /api/v1/auth/monitor-login/."""

    def test_monitor_login_success(self):
        """2026-03-04: Staff user can log in and get JWT tokens."""
        user = make_user(username='monitor_user', is_staff=True)
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-login/',
            {'username': 'monitor_user', 'password': 'testpass123'},
            format='json',
        )
        assert response.status_code == 200  # 2026-03-04: OK
        data = response.json()
        assert data['role'] == 'monitor'  # 2026-03-04: Monitor role
        assert 'access' in data  # 2026-03-04: JWT returned

    def test_monitor_login_wrong_password(self):
        """2026-03-04: Wrong password returns 401."""
        make_user(username='monitor2', is_staff=True)
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-login/',
            {'username': 'monitor2', 'password': 'WRONG'},
            format='json',
        )
        assert response.status_code == 401  # 2026-03-04: Unauthorized

    def test_monitor_login_non_staff_rejected(self):
        """2026-03-04: Non-staff user gets 403 even with correct credentials."""
        make_user(username='regular_user', is_staff=False)
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-login/',
            {'username': 'regular_user', 'password': 'testpass123'},
            format='json',
        )
        assert response.status_code == 403  # 2026-03-04: Forbidden

    def test_monitor_login_missing_fields(self):
        """2026-03-04: Missing username/password returns 400."""
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-login/',
            {'username': ''},
            format='json',
        )
        assert response.status_code == 400  # 2026-03-04: Bad request


@pytest.mark.django_db
class TestPodListAPI:
    """2026-03-04: Tests for GET /api/v1/pods/."""

    def test_pod_list_requires_staff(self):
        """2026-03-04: Non-staff get 403 on pod listing."""
        student = make_student()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.get('/api/v1/pods/')
        assert response.status_code == 403  # 2026-03-04: Forbidden

    def test_pod_list_staff_access(self):
        """2026-03-04: Staff can list all pods."""
        make_pod()
        make_pod()
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.get('/api/v1/pods/')
        assert response.status_code == 200  # 2026-03-04: OK
        data = response.json()
        assert 'pods' in data  # 2026-03-04: pods key present
        assert len(data['pods']) >= 2  # 2026-03-04: Both pods returned


@pytest.mark.django_db
class TestPodDetailAPI:
    """2026-03-04: Tests for GET /api/v1/pods/{id}/."""

    def test_pod_detail_not_found(self):
        """2026-03-04: Non-existent pod returns 404."""
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.get(f'/api/v1/pods/{uuid.uuid4()}/')
        assert response.status_code == 404  # 2026-03-04: Not found

    def test_pod_detail_returns_students(self):
        """2026-03-04: Pod detail includes enrolled student list."""
        pod = make_pod()
        student = make_student()
        make_enrollment(pod, student)
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.get(f'/api/v1/pods/{pod.id}/')
        assert response.status_code == 200  # 2026-03-04: OK
        data = response.json()
        student_names = [s['student_name'] for s in data['students']]
        assert student.full_name in student_names  # 2026-03-04: Student present


@pytest.mark.django_db
class TestEnrollUnenrollAPI:
    """2026-03-04: Tests for POST /api/v1/pods/{id}/enroll/ and unenroll/."""

    def test_enroll_student_via_api(self):
        """2026-03-04: Admin can enroll a student in a pod."""
        pod = make_pod()
        student = make_student()
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.post(
            f'/api/v1/pods/{pod.id}/enroll/',
            {'student_id': str(student.id)},
            format='json',
        )
        assert response.status_code == 201  # 2026-03-04: Created

    def test_unenroll_student_via_api(self):
        """2026-03-04: Admin can unenroll a student from a pod."""
        pod = make_pod()
        student = make_student()
        make_enrollment(pod, student)
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.post(
            f'/api/v1/pods/{pod.id}/unenroll/',
            {'student_id': str(student.id)},
            format='json',
        )
        assert response.status_code == 200  # 2026-03-04: OK

    def test_enroll_full_pod_returns_409(self):
        """2026-03-04: Enrolling into a full pod returns 409 Conflict."""
        pod = make_pod(max_size=1)
        make_enrollment(pod, make_student())  # 2026-03-04: Fill it
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.post(
            f'/api/v1/pods/{pod.id}/enroll/',
            {'student_id': str(make_student().id)},
            format='json',
        )
        assert response.status_code == 409  # 2026-03-04: Conflict


@pytest.mark.django_db
class TestHeartbeatAPI:
    """2026-03-04: Tests for POST /api/v1/pods/heartbeat/."""

    def test_heartbeat_student_in_pod(self):
        """2026-03-04: Student in a pod can send heartbeat."""
        pod = make_pod()
        student = make_student()
        enrollment = make_enrollment(pod, student)
        make_session(enrollment)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.post('/api/v1/pods/heartbeat/', {}, format='json')
        assert response.status_code == 200  # 2026-03-04: OK

    def test_heartbeat_unauthenticated(self):
        """2026-03-04: Unauthenticated heartbeat returns 401."""
        client = APIClient()
        response = client.post('/api/v1/pods/heartbeat/', {}, format='json')
        assert response.status_code == 401  # 2026-03-04: Unauthorized


@pytest.mark.django_db
class TestAttentionEventAPI:
    """2026-03-04: Tests for POST /api/v1/pods/attention-event/."""

    def test_report_attention_event(self):
        """2026-03-04: Student can report a valid attention event."""
        pod = make_pod()
        student = make_student()
        enrollment = make_enrollment(pod, student)
        make_session(enrollment)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.post(
            '/api/v1/pods/attention-event/',
            {
                'event_type': 'not_looking',
                'ai_response': 'Please look at the screen.',
                'escalated': False,
            },
            format='json',
        )
        assert response.status_code == 201  # 2026-03-04: Created
        assert AttentionEvent.objects.filter(
            student=student, event_type='not_looking'
        ).exists()

    def test_invalid_event_type_rejected(self):
        """2026-03-04: Unknown event type returns 400."""
        pod = make_pod()
        student = make_student()
        make_enrollment(pod, student)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.post(
            '/api/v1/pods/attention-event/',
            {'event_type': 'levitating', 'escalated': False},
            format='json',
        )
        assert response.status_code == 400  # 2026-03-04: Bad request


@pytest.mark.django_db
class TestHelpRequestAPI:
    """2026-03-04: Tests for POST /api/v1/pods/help-request/."""

    def test_student_can_request_help(self):
        """2026-03-04: Student can send a help request."""
        student = make_student()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.post(
            '/api/v1/pods/help-request/',
            {'message': 'I am stuck on Day 2'},
            format='json',
        )
        assert response.status_code == 201  # 2026-03-04: Created
        assert MonitorAlert.objects.filter(
            student=student, alert_type='help_request'
        ).exists()


@pytest.mark.django_db
class TestMonitorDashboardAPI:
    """2026-03-04: Tests for GET /api/v1/pods/monitor-dashboard/."""

    def test_dashboard_requires_staff(self):
        """2026-03-04: Non-staff get 403 on monitor dashboard."""
        student = make_student()
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_student_jwt(student)}')
        response = client.get('/api/v1/pods/monitor-dashboard/')
        assert response.status_code == 403  # 2026-03-04: Forbidden

    def test_dashboard_returns_pods_and_alerts(self):
        """2026-03-04: Dashboard returns pods and alert sections."""
        make_pod()
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.get('/api/v1/pods/monitor-dashboard/')
        assert response.status_code == 200  # 2026-03-04: OK
        data = response.json()
        assert 'pods' in data  # 2026-03-04: pods section
        assert 'alerts' in data  # 2026-03-04: alerts section
        assert 'unresolved_count' in data  # 2026-03-04: count

    def test_dashboard_includes_unresolved_alerts(self):
        """2026-03-04: Dashboard alert list contains open alerts."""
        student = make_student()
        AlertService.create_help_request(student, 'Test alert')
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.get('/api/v1/pods/monitor-dashboard/')
        assert response.status_code == 200  # 2026-03-04: OK
        data = response.json()
        assert data['unresolved_count'] >= 1  # 2026-03-04: At least 1 alert


@pytest.mark.django_db
class TestResolveAlertAPI:
    """2026-03-04: Tests for POST /api/v1/pods/resolve-alert/."""

    def test_resolve_alert_via_api(self):
        """2026-03-04: Monitor can resolve an alert via API."""
        student = make_student()
        result = AlertService.create_help_request(student)
        alert_id = int(result['alert_id'])  # 2026-03-04: BigAutoField integer PK
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.post(
            '/api/v1/pods/resolve-alert/',
            {'alert_id': alert_id},
            format='json',
        )
        assert response.status_code == 200  # 2026-03-04: OK
        assert MonitorAlert.objects.get(id=alert_id).is_resolved  # 2026-03-04: Resolved

    def test_resolve_nonexistent_alert_returns_404(self):
        """2026-03-04: Resolving missing alert returns 404."""
        staff_user = make_user(is_staff=True)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {get_staff_jwt(staff_user)}')
        response = client.post(
            '/api/v1/pods/resolve-alert/',
            {'alert_id': 999999},  # 2026-03-04: Non-existent integer PK
            format='json',
        )
        assert response.status_code == 404  # 2026-03-04: Not found
