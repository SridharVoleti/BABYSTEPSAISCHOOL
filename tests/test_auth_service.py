"""
2026-02-12: Tests for the authentication service.

Purpose:
    Comprehensive test coverage for OTP, registration, student login,
    consent, and RBAC functionality.
"""

import pytest  # 2026-02-12: Test framework
from datetime import date, timedelta  # 2026-02-12: Date utilities
from unittest.mock import patch, MagicMock  # 2026-02-12: Mocking

from django.contrib.auth import get_user_model  # 2026-02-12: User model
from django.test import TestCase  # 2026-02-12: Django test case
from django.utils import timezone  # 2026-02-12: Timezone
from rest_framework.test import APIClient  # 2026-02-12: DRF test client

from services.auth_service.models import (  # 2026-02-12: Models
    Parent, Student, OTPRequest, ConsentRecord, AuditLog,
)
from services.auth_service.services import AuthService  # 2026-02-12: Service
from services.auth_service.otp_providers.factory import OTPFactory  # 2026-02-12: Factory
from services.auth_service.otp_providers.mock_provider import MockOTPProvider  # 2026-02-12: Mock

User = get_user_model()  # 2026-02-12: Django User model


@pytest.fixture
def api_client():
    """2026-02-12: DRF API client fixture."""
    return APIClient()


@pytest.fixture
def mock_otp_provider():
    """2026-02-12: Reset OTP factory and use mock provider."""
    OTPFactory.reset()  # 2026-02-12: Clear singleton
    provider = OTPFactory.get_provider()  # 2026-02-12: Creates mock
    yield provider
    OTPFactory.reset()  # 2026-02-12: Cleanup


@pytest.fixture
def auth_parent(db):
    """2026-02-12: Create a registered parent fixture."""
    user = User.objects.create_user(username='parent_test')  # 2026-02-12: Django user
    parent = Parent.objects.create(  # 2026-02-12: Parent profile
        user=user,
        phone='+919876543210',
        full_name='Test Parent',
        email='parent@test.com',
        state='Telangana',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def auth_student(db, auth_parent):
    """2026-02-12: Create a student fixture under auth_parent."""
    user = User.objects.create_user(username='student_test')  # 2026-02-12: Django user
    student = Student.objects.create(  # 2026-02-12: Student profile
        parent=auth_parent,
        user=user,
        full_name='Test Student',
        dob=date(2018, 6, 15),  # 2026-02-12: Age ~7, so 6-12 group
        age_group='6-12',
        grade=2,
        login_method='pin',
        avatar_id='avatar_01',
        pin_hash=AuthService._hash_value('1234'),  # 2026-02-12: PIN = 1234
    )
    return student


@pytest.fixture
def authenticated_parent_client(db, auth_parent):
    """2026-02-12: API client authenticated as a parent."""
    from services.auth_service.jwt_utils import get_tokens_for_parent
    client = APIClient()  # 2026-02-12: New client
    tokens = get_tokens_for_parent(auth_parent)  # 2026-02-12: Get JWT
    client.credentials(  # 2026-02-12: Set auth header
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}"
    )
    return client


# ============================================================
# OTP Tests
# ============================================================

@pytest.mark.django_db
class TestOTPSendVerify:
    """2026-02-12: Tests for OTP send and verify flow."""

    def test_send_otp_success(self, mock_otp_provider):
        """2026-02-12: Test successful OTP sending."""
        result = AuthService.send_otp('+919999999999')  # 2026-02-12: Send OTP
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert OTPRequest.objects.filter(phone='+919999999999').exists()

    def test_send_otp_cooldown(self, mock_otp_provider):
        """2026-02-12: Test OTP cooldown enforcement."""
        AuthService.send_otp('+919999999998')  # 2026-02-12: First send
        result = AuthService.send_otp('+919999999998')  # 2026-02-12: Immediate resend
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'COOLDOWN_ACTIVE'

    def test_verify_otp_success(self, mock_otp_provider):
        """2026-02-12: Test successful OTP verification."""
        # 2026-02-12: Create OTP with known code
        otp_code = '123456'
        otp_hash = AuthService._hash_value(otp_code)
        OTPRequest.objects.create(
            phone='+919999999997',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        result = AuthService.verify_otp('+919999999997', otp_code)
        assert result['success'] is True  # 2026-02-12: Should verify

    def test_verify_otp_invalid_code(self, mock_otp_provider):
        """2026-02-12: Test OTP verification with wrong code."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919999999996',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
        )
        result = AuthService.verify_otp('+919999999996', '000000')
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'INVALID_OTP'

    def test_verify_otp_expired(self, mock_otp_provider):
        """2026-02-12: Test OTP verification with expired OTP."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919999999995',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() - timedelta(minutes=1),  # 2026-02-12: Expired
        )
        result = AuthService.verify_otp('+919999999995', '123456')
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'OTP_NOT_FOUND'

    def test_verify_otp_max_attempts(self, mock_otp_provider):
        """2026-02-12: Test OTP max attempts enforcement."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919999999994',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            attempts=3,  # 2026-02-12: Already at max
        )
        result = AuthService.verify_otp('+919999999994', '123456')
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'MAX_ATTEMPTS'

    def test_verify_otp_no_request(self, mock_otp_provider):
        """2026-02-12: Test OTP verification with no request found."""
        result = AuthService.verify_otp('+910000000000', '123456')
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'OTP_NOT_FOUND'


# ============================================================
# Registration Tests
# ============================================================

@pytest.mark.django_db
class TestRegistration:
    """2026-02-12: Tests for parent registration flow."""

    def test_complete_registration_success(self, mock_otp_provider):
        """2026-02-12: Test successful registration."""
        # 2026-02-12: Create verified OTP
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919888888888',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        result = AuthService.complete_registration(
            phone='+919888888888',
            full_name='New Parent',
            email='new@test.com',
            state='Telangana',
        )
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert 'tokens' in result  # 2026-02-12: Should have JWT
        assert result['parent']['full_name'] == 'New Parent'

    def test_registration_duplicate_phone(self, mock_otp_provider, auth_parent):
        """2026-02-12: Test registration with existing phone."""
        OTPRequest.objects.create(
            phone=auth_parent.phone,
            otp_hash=AuthService._hash_value('123456'),
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        result = AuthService.complete_registration(
            phone=auth_parent.phone,
            full_name='Duplicate',
        )
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'DUPLICATE_PHONE'

    def test_registration_without_otp_verification(self, mock_otp_provider):
        """2026-02-12: Test registration without verified OTP."""
        result = AuthService.complete_registration(
            phone='+919777777777',
            full_name='Unverified',
        )
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'PHONE_NOT_VERIFIED'


# ============================================================
# Student Creation Tests
# ============================================================

@pytest.mark.django_db
class TestStudentCreation:
    """2026-02-12: Tests for student profile creation."""

    def test_create_student_young_child(self, auth_parent):
        """2026-02-12: Test creating student ages 3-6 gets picture login."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Young Child',
            dob=date(2022, 1, 1),  # 2026-02-12: ~4 years old
            grade=1,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert result['student']['age_group'] == '3-6'
        assert result['student']['login_method'] == 'picture'

    def test_create_student_middle_child(self, auth_parent):
        """2026-02-12: Test creating student ages 6-12 gets PIN login."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Middle Child',
            dob=date(2018, 6, 15),  # 2026-02-12: ~7 years old
            grade=3,
            pin='5678',
        )
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert result['student']['age_group'] == '6-12'
        assert result['student']['login_method'] == 'pin'

    def test_create_student_teen(self, auth_parent):
        """2026-02-12: Test creating student 12+ gets password login."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Teen Student',
            dob=date(2013, 3, 20),  # 2026-02-12: ~12 years old
            grade=7,
            password='secure_password_123',
        )
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert result['student']['age_group'] == '12+'
        assert result['student']['login_method'] == 'password'

    def test_age_group_computation(self):
        """2026-02-12: Test age group computation from DOB."""
        assert Student.compute_age_group(date(2023, 1, 1)) == '3-6'  # ~3
        assert Student.compute_age_group(date(2018, 1, 1)) == '6-12'  # ~8
        assert Student.compute_age_group(date(2012, 1, 1)) == '12+'  # ~14


# ============================================================
# Student Login Tests
# ============================================================

@pytest.mark.django_db
class TestStudentLogin:
    """2026-02-12: Tests for student login methods."""

    def test_pin_login_success(self, auth_student):
        """2026-02-12: Test successful PIN login."""
        result = AuthService.student_pin_login(  # 2026-02-12: Correct PIN
            student_id=auth_student.id, pin='1234'
        )
        assert result['success'] is True  # 2026-02-12: Should succeed
        assert 'tokens' in result

    def test_pin_login_wrong_pin(self, auth_student):
        """2026-02-12: Test PIN login with wrong PIN."""
        result = AuthService.student_pin_login(  # 2026-02-12: Wrong PIN
            student_id=auth_student.id, pin='0000'
        )
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'INVALID_PIN'

    def test_pin_login_nonexistent_student(self):
        """2026-02-12: Test PIN login with non-existent student."""
        import uuid
        result = AuthService.student_pin_login(
            student_id=uuid.uuid4(), pin='1234'
        )
        assert result['success'] is False
        assert result['code'] == 'STUDENT_NOT_FOUND'

    def test_picture_login_success(self, auth_parent):
        """2026-02-12: Test successful picture login."""
        # 2026-02-12: Create picture-login student
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Picture Kid',
            dob=date(2022, 5, 10),  # ~3-6
            grade=1,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        student_id = result['student']['id']

        # 2026-02-12: Login with correct sequence
        login_result = AuthService.student_picture_login(
            student_id=student_id,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        assert login_result['success'] is True

    def test_picture_login_wrong_sequence(self, auth_parent):
        """2026-02-12: Test picture login with wrong sequence."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Picture Kid 2',
            dob=date(2022, 5, 10),
            grade=1,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        student_id = result['student']['id']

        login_result = AuthService.student_picture_login(
            student_id=student_id,
            picture_sequence=['fish', 'dog', 'cat'],  # 2026-02-12: Wrong order
        )
        assert login_result['success'] is False
        assert login_result['code'] == 'INVALID_PICTURES'


# ============================================================
# Consent Tests
# ============================================================

@pytest.mark.django_db
class TestConsent:
    """2026-02-12: Tests for consent management."""

    def test_grant_consent(self, auth_parent):
        """2026-02-12: Test consent grant creates record."""
        result = AuthService.record_consent(
            parent=auth_parent,
            consent_version='1.0',
            action='grant',
            scroll_percentage=100,
        )
        assert result['success'] is True
        assert result['consent']['action'] == 'grant'
        assert ConsentRecord.objects.filter(parent=auth_parent).count() == 1

    def test_withdraw_consent(self, auth_parent):
        """2026-02-12: Test consent withdrawal creates record."""
        AuthService.record_consent(  # 2026-02-12: Grant first
            parent=auth_parent, consent_version='1.0', action='grant',
        )
        result = AuthService.record_consent(  # 2026-02-12: Then withdraw
            parent=auth_parent, consent_version='1.0', action='withdraw',
        )
        assert result['success'] is True
        assert result['consent']['action'] == 'withdraw'
        # 2026-02-12: Both records should exist (append-only)
        assert ConsentRecord.objects.filter(parent=auth_parent).count() == 2


# ============================================================
# API Endpoint Tests
# ============================================================

@pytest.mark.django_db
class TestAuthEndpoints:
    """2026-02-12: Tests for auth API endpoints."""

    def test_send_otp_endpoint(self, api_client):
        """2026-02-12: Test POST /api/v1/auth/send-otp/."""
        response = api_client.post(
            '/api/v1/auth/send-otp/',
            {'phone': '+919111111111', 'purpose': 'registration'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True

    def test_send_otp_invalid_phone(self, api_client):
        """2026-02-12: Test send OTP with invalid phone."""
        response = api_client.post(
            '/api/v1/auth/send-otp/',
            {'phone': '12345', 'purpose': 'registration'},
            format='json',
        )
        assert response.status_code == 400  # 2026-02-12: Validation error

    def test_consent_notice_endpoint(self, api_client):
        """2026-02-12: Test GET /api/v1/auth/consent/notice/."""
        response = api_client.get('/api/v1/auth/consent/notice/')
        assert response.status_code == 200
        assert 'version' in response.data
        assert 'content' in response.data

    def test_language_suggestions_endpoint(self, api_client):
        """2026-02-12: Test GET /api/v1/auth/languages/suggestions/."""
        response = api_client.get(
            '/api/v1/auth/languages/suggestions/',
            {'state': 'Telangana'},
        )
        assert response.status_code == 200
        assert response.data['suggestions']['language_1'] == 'Telugu'

    def test_language_available_endpoint(self, api_client):
        """2026-02-12: Test GET /api/v1/auth/languages/available/."""
        response = api_client.get('/api/v1/auth/languages/available/')
        assert response.status_code == 200
        assert 'English' in response.data['languages']

    def test_students_list_requires_auth(self, api_client):
        """2026-02-12: Test student list requires parent auth."""
        response = api_client.get('/api/v1/auth/students/')
        assert response.status_code in [401, 403]  # 2026-02-12: Denied

    def test_students_list_authenticated(self, authenticated_parent_client, auth_parent, auth_student):
        """2026-02-12: Test authenticated parent can list students."""
        response = authenticated_parent_client.get('/api/v1/auth/students/')
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['full_name'] == 'Test Student'

    def test_picture_grid_endpoint(self, api_client, auth_parent):
        """2026-02-12: Test picture grid returns shuffled pictures."""
        # 2026-02-12: Create picture-login student
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Grid Kid',
            dob=date(2022, 5, 10),
            grade=1,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        student_id = result['student']['id']

        response = api_client.get(
            f'/api/v1/auth/student-auth/picture-grid/{student_id}/'
        )
        assert response.status_code == 200
        assert len(response.data['pictures']) == 12


# ============================================================
# RBAC Tests
# ============================================================

@pytest.mark.django_db
class TestRBAC:
    """2026-02-12: Tests for role-based access control."""

    def test_parent_cannot_access_other_children(self, db):
        """2026-02-12: Test parent can only access own children."""
        # 2026-02-12: Create two parents
        user1 = User.objects.create_user(username='parent1')
        parent1 = Parent.objects.create(
            user=user1, phone='+911111111111', full_name='Parent 1',
            is_phone_verified=True, is_profile_complete=True,
        )
        user2 = User.objects.create_user(username='parent2')
        parent2 = Parent.objects.create(
            user=user2, phone='+912222222222', full_name='Parent 2',
            is_phone_verified=True, is_profile_complete=True,
        )

        # 2026-02-12: Create student under parent2
        result = AuthService.create_student(
            parent=parent2,
            full_name='Other Child',
            dob=date(2018, 1, 1),
            grade=3,
            pin='9999',
        )
        other_student_id = result['student']['id']

        # 2026-02-12: Authenticate as parent1
        from services.auth_service.jwt_utils import get_tokens_for_parent
        client = APIClient()
        tokens = get_tokens_for_parent(parent1)
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        # 2026-02-12: Try to access parent2's child
        response = client.get(f'/api/v1/auth/students/{other_student_id}/')
        assert response.status_code == 403  # 2026-02-12: Access denied
