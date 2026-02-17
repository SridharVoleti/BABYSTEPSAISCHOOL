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
            password='TestPass123',
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
            password='TestPass123',
        )
        assert result['success'] is False  # 2026-02-12: Should fail
        assert result['code'] == 'DUPLICATE_PHONE'

    def test_registration_without_otp_verification(self, mock_otp_provider):
        """2026-02-12: Test registration without verified OTP."""
        result = AuthService.complete_registration(
            phone='+919777777777',
            full_name='Unverified',
            password='TestPass123',
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


# ============================================================
# Password Login Tests (ages 12+)
# ============================================================

@pytest.mark.django_db
class TestPasswordLogin:
    """2026-02-13: Tests for password-based student login (12+ age group)."""

    def test_password_login_success(self, db, auth_parent):
        """2026-02-13: Test successful password login for 12+ student."""
        # 2026-02-13: Create a 12+ student with password
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Teen Student',
            dob=date(2012, 1, 15),  # 2026-02-13: ~14 years old
            grade=9,
            password='SecurePass123',
        )
        assert result['success'] is True
        assert result['student']['login_method'] == 'password'

        # 2026-02-13: Login with correct password
        login_result = AuthService.student_password_login(
            student_id=result['student']['id'],
            password='SecurePass123',
        )
        assert login_result['success'] is True
        assert 'tokens' in login_result
        assert login_result['student']['full_name'] == 'Teen Student'

    def test_password_login_wrong_password(self, db, auth_parent):
        """2026-02-13: Test password login with incorrect password."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Teen Student 2',
            dob=date(2012, 6, 1),
            grade=9,
            password='CorrectPass',
        )
        login_result = AuthService.student_password_login(
            student_id=result['student']['id'],
            password='WrongPass',
        )
        assert login_result['success'] is False
        assert login_result['code'] == 'INVALID_PASSWORD'

    def test_password_login_endpoint(self, api_client, db, auth_parent):
        """2026-02-13: Test password login API endpoint."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Endpoint Teen',
            dob=date(2011, 3, 20),
            grade=10,
            password='ApiPass456',
        )
        student_id = result['student']['id']

        response = api_client.post(
            '/api/v1/auth/student-auth/password-login/',
            {'student_id': student_id, 'password': 'ApiPass456'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert 'tokens' in response.data

    def test_password_login_endpoint_wrong_password(self, api_client, db, auth_parent):
        """2026-02-13: Test password login endpoint with wrong password."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Endpoint Teen 2',
            dob=date(2011, 7, 10),
            grade=10,
            password='RealPass',
        )
        student_id = result['student']['id']

        response = api_client.post(
            '/api/v1/auth/student-auth/password-login/',
            {'student_id': student_id, 'password': 'FakePass'},
            format='json',
        )
        assert response.status_code == 400
        assert response.data['success'] is False


# ============================================================
# Parent Profile Update Tests
# ============================================================

@pytest.mark.django_db
class TestParentProfileUpdate:
    """2026-02-13: Tests for parent profile get/update."""

    def test_update_profile_service(self, db, auth_parent):
        """2026-02-13: Test profile update via service layer."""
        result = AuthService.update_parent_profile(
            parent=auth_parent,
            full_name='Updated Name',
            email='new@test.com',
            state='Karnataka',
        )
        assert result['success'] is True
        assert result['parent']['full_name'] == 'Updated Name'
        assert result['parent']['email'] == 'new@test.com'
        assert result['parent']['state'] == 'Karnataka'

        # 2026-02-13: Verify DB was updated
        auth_parent.refresh_from_db()
        assert auth_parent.full_name == 'Updated Name'

    def test_update_profile_no_fields(self, db, auth_parent):
        """2026-02-13: Test profile update with no valid fields."""
        result = AuthService.update_parent_profile(parent=auth_parent)
        assert result['success'] is False
        assert result['code'] == 'NO_FIELDS'

    def test_get_profile_endpoint(self, authenticated_parent_client):
        """2026-02-13: Test GET /profile/ returns parent data."""
        response = authenticated_parent_client.get('/api/v1/auth/profile/')
        assert response.status_code == 200
        assert 'full_name' in response.data
        assert 'phone' in response.data

    def test_update_profile_endpoint(self, authenticated_parent_client):
        """2026-02-13: Test PUT /profile/ updates parent data."""
        response = authenticated_parent_client.put(
            '/api/v1/auth/profile/',
            {'full_name': 'API Updated', 'state': 'Telangana'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['parent']['full_name'] == 'API Updated'

    def test_profile_requires_auth(self, api_client, db):
        """2026-02-13: Test profile endpoint requires authentication."""
        response = api_client.get('/api/v1/auth/profile/')
        assert response.status_code in (401, 403)


# ============================================================
# Student Profile Update Tests
# ============================================================

@pytest.mark.django_db
class TestStudentProfileUpdate:
    """2026-02-13: Tests for student profile update by parent."""

    def test_update_student_service(self, db, auth_parent, auth_student):
        """2026-02-13: Test student update via service layer."""
        result = AuthService.update_student_profile(
            student=auth_student,
            parent=auth_parent,
            full_name='Updated Child',
            grade=5,
            avatar_id='avatar_03',
            language_1='Telugu',
        )
        assert result['success'] is True
        assert result['student']['full_name'] == 'Updated Child'
        assert result['student']['grade'] == 5
        assert result['student']['avatar_id'] == 'avatar_03'
        assert result['student']['language_1'] == 'Telugu'

        # 2026-02-13: Verify DB
        auth_student.refresh_from_db()
        assert auth_student.full_name == 'Updated Child'

    def test_update_student_wrong_parent(self, db, auth_student):
        """2026-02-13: Test update denied for non-owner parent."""
        other_user = User.objects.create_user(username='other_parent')
        other_parent = Parent.objects.create(
            user=other_user, phone='+910000000000', full_name='Other',
            is_phone_verified=True, is_profile_complete=True,
        )
        result = AuthService.update_student_profile(
            student=auth_student,
            parent=other_parent,
            full_name='Hacked',
        )
        assert result['success'] is False
        assert result['code'] == 'NOT_OWNER'

    def test_update_student_endpoint(self, authenticated_parent_client, auth_student):
        """2026-02-13: Test PUT /students/{id}/ updates student."""
        response = authenticated_parent_client.put(
            f'/api/v1/auth/students/{auth_student.id}/',
            {'full_name': 'API Child', 'grade': 4},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert response.data['student']['full_name'] == 'API Child'
        assert response.data['student']['grade'] == 4

    def test_update_student_endpoint_not_found(self, authenticated_parent_client):
        """2026-02-13: Test update returns 404 for invalid student ID."""
        import uuid
        fake_id = str(uuid.uuid4())
        response = authenticated_parent_client.put(
            f'/api/v1/auth/students/{fake_id}/',
            {'full_name': 'Ghost'},
            format='json',
        )
        assert response.status_code == 404


# ============================================================
# Student Credential Reset Tests
# ============================================================

@pytest.mark.django_db
class TestCredentialReset:
    """2026-02-13: Tests for student credential reset by parent."""

    def test_reset_pin_service(self, db, auth_parent, auth_student):
        """2026-02-13: Test PIN reset via service layer."""
        # 2026-02-13: auth_student has login_method='pin', PIN='1234'
        result = AuthService.reset_student_credentials(
            student=auth_student, parent=auth_parent, pin='5678',
        )
        assert result['success'] is True

        # 2026-02-13: Old PIN should fail, new PIN should work
        login_old = AuthService.student_pin_login(str(auth_student.id), '1234')
        assert login_old['success'] is False
        login_new = AuthService.student_pin_login(str(auth_student.id), '5678')
        assert login_new['success'] is True

    def test_reset_password_service(self, db, auth_parent):
        """2026-02-13: Test password reset via service layer."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Password Teen',
            dob=date(2012, 1, 1),
            grade=9,
            password='OldPass123',
        )
        student = Student.objects.get(id=result['student']['id'])

        reset = AuthService.reset_student_credentials(
            student=student, parent=auth_parent, password='NewPass456',
        )
        assert reset['success'] is True

        # 2026-02-13: Old password fails, new password works
        login_old = AuthService.student_password_login(str(student.id), 'OldPass123')
        assert login_old['success'] is False
        login_new = AuthService.student_password_login(str(student.id), 'NewPass456')
        assert login_new['success'] is True

    def test_reset_picture_service(self, db, auth_parent):
        """2026-02-13: Test picture sequence reset via service layer."""
        result = AuthService.create_student(
            parent=auth_parent,
            full_name='Picture Kid',
            dob=date(2022, 5, 10),
            grade=1,
            picture_sequence=['cat', 'dog', 'fish'],
        )
        student = Student.objects.get(id=result['student']['id'])

        reset = AuthService.reset_student_credentials(
            student=student, parent=auth_parent,
            picture_sequence=['sun', 'moon', 'star'],
        )
        assert reset['success'] is True

        # 2026-02-13: Old sequence fails, new sequence works
        login_old = AuthService.student_picture_login(
            str(student.id), ['cat', 'dog', 'fish']
        )
        assert login_old['success'] is False
        login_new = AuthService.student_picture_login(
            str(student.id), ['sun', 'moon', 'star']
        )
        assert login_new['success'] is True

    def test_reset_method_mismatch(self, db, auth_parent, auth_student):
        """2026-02-13: Test reset fails when credential type mismatches login method."""
        # 2026-02-13: auth_student is PIN-based, try resetting password
        result = AuthService.reset_student_credentials(
            student=auth_student, parent=auth_parent, password='WrongType',
        )
        assert result['success'] is False
        assert result['code'] == 'METHOD_MISMATCH'

    def test_reset_wrong_parent(self, db, auth_student):
        """2026-02-13: Test credential reset denied for non-owner parent."""
        other_user = User.objects.create_user(username='other_cred_parent')
        other_parent = Parent.objects.create(
            user=other_user, phone='+910000000001', full_name='Other Cred',
            is_phone_verified=True, is_profile_complete=True,
        )
        result = AuthService.reset_student_credentials(
            student=auth_student, parent=other_parent, pin='9999',
        )
        assert result['success'] is False
        assert result['code'] == 'NOT_OWNER'

    def test_reset_pin_endpoint(self, authenticated_parent_client, auth_student):
        """2026-02-13: Test POST /students/reset-credentials/ for PIN."""
        response = authenticated_parent_client.post(
            '/api/v1/auth/students/reset-credentials/',
            {'student_id': str(auth_student.id), 'pin': '0000'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True

        # 2026-02-13: Verify new PIN works
        login = AuthService.student_pin_login(str(auth_student.id), '0000')
        assert login['success'] is True


# ============================================================
# Consent Status & Withdrawal Tests
# ============================================================

@pytest.mark.django_db
class TestConsentManagement:
    """2026-02-13: Tests for consent status and withdrawal endpoints."""

    def test_consent_status_no_records(self, authenticated_parent_client):
        """2026-02-13: Test status returns not consented when no records exist."""
        response = authenticated_parent_client.get('/api/v1/auth/consent/status/')
        assert response.status_code == 200
        assert response.data['has_consented'] is False

    def test_consent_grant_then_status(self, authenticated_parent_client):
        """2026-02-13: Test status reflects grant after consent is given."""
        # 2026-02-13: Grant consent
        authenticated_parent_client.post(
            '/api/v1/auth/consent/grant/',
            {'consent_version': '1.0', 'action': 'grant', 'scroll_percentage': 100},
            format='json',
        )

        # 2026-02-13: Check status
        response = authenticated_parent_client.get('/api/v1/auth/consent/status/')
        assert response.status_code == 200
        assert response.data['has_consented'] is True
        assert response.data['consent_version'] == '1.0'

    def test_consent_withdraw_then_status(self, authenticated_parent_client):
        """2026-02-13: Test status reflects withdrawal after consent is withdrawn."""
        # 2026-02-13: Grant first
        authenticated_parent_client.post(
            '/api/v1/auth/consent/grant/',
            {'consent_version': '1.0', 'action': 'grant'},
            format='json',
        )
        # 2026-02-13: Withdraw
        response = authenticated_parent_client.post(
            '/api/v1/auth/consent/withdraw/',
            {'consent_version': '1.0', 'action': 'withdraw'},
            format='json',
        )
        assert response.status_code == 201

        # 2026-02-13: Check status
        status_response = authenticated_parent_client.get('/api/v1/auth/consent/status/')
        assert status_response.data['has_consented'] is False
        assert status_response.data['latest_action'] == 'withdraw'

    def test_consent_status_requires_auth(self, api_client, db):
        """2026-02-13: Test consent status requires authentication."""
        response = api_client.get('/api/v1/auth/consent/status/')
        assert response.status_code in (401, 403)


# ============================================================
# Parent Password Login Tests
# ============================================================

@pytest.mark.django_db
class TestParentPasswordLogin:
    """2026-02-17: Tests for parent phone + password login."""

    def test_parent_password_login_success(self, mock_otp_provider):
        """2026-02-17: Test successful parent password login."""
        # 2026-02-17: Register parent with password
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919555555555',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919555555555',
            full_name='Password Parent',
            password='MyPass123',
        )

        # 2026-02-17: Login with correct password
        result = AuthService.parent_password_login(
            phone='+919555555555',
            password='MyPass123',
        )
        assert result['success'] is True
        assert 'tokens' in result
        assert result['parent']['full_name'] == 'Password Parent'

    def test_parent_password_login_wrong_password(self, mock_otp_provider):
        """2026-02-17: Test parent login with incorrect password."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919555555554',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919555555554',
            full_name='Wrong Pass Parent',
            password='RealPass',
        )

        result = AuthService.parent_password_login(
            phone='+919555555554',
            password='WrongPass',
        )
        assert result['success'] is False
        assert result['code'] == 'INVALID_PASSWORD'

    def test_parent_password_login_not_found(self, db):
        """2026-02-17: Test parent login with non-existent phone."""
        result = AuthService.parent_password_login(
            phone='+910000000099',
            password='AnyPass',
        )
        assert result['success'] is False
        assert result['code'] == 'PARENT_NOT_FOUND'

    def test_parent_password_login_endpoint(self, api_client, mock_otp_provider):
        """2026-02-17: Test POST /api/v1/auth/password-login/ endpoint."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919555555553',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919555555553',
            full_name='Endpoint Parent',
            password='EndpointPass',
        )

        response = api_client.post(
            '/api/v1/auth/password-login/',
            {'phone': '+919555555553', 'password': 'EndpointPass'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        assert 'tokens' in response.data

    def test_parent_password_login_endpoint_wrong_password(self, api_client, mock_otp_provider):
        """2026-02-17: Test password-login endpoint returns 401 for wrong password."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919555555552',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919555555552',
            full_name='Wrong Pass Endpoint',
            password='RealEndpointPass',
        )

        response = api_client.post(
            '/api/v1/auth/password-login/',
            {'phone': '+919555555552', 'password': 'WrongPass'},
            format='json',
        )
        assert response.status_code == 401
        assert response.data['code'] == 'INVALID_PASSWORD'


# ============================================================
# Parent Forgot Password Tests
# ============================================================

@pytest.mark.django_db
class TestParentForgotPassword:
    """2026-02-17: Tests for parent forgot password (OTP-based reset)."""

    def test_reset_password_success(self, mock_otp_provider):
        """2026-02-17: Test successful password reset after OTP verification."""
        # 2026-02-17: Register parent
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919444444444',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919444444444',
            full_name='Reset Parent',
            password='OldPassword',
        )

        # 2026-02-17: Create verified reset OTP
        reset_hash = AuthService._hash_value('654321')
        OTPRequest.objects.create(
            phone='+919444444444',
            otp_hash=reset_hash,
            purpose='reset',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )

        # 2026-02-17: Reset password
        result = AuthService.parent_reset_password(
            phone='+919444444444',
            new_password='NewPassword',
        )
        assert result['success'] is True

        # 2026-02-17: Old password fails, new password works
        old_login = AuthService.parent_password_login('+919444444444', 'OldPassword')
        assert old_login['success'] is False
        new_login = AuthService.parent_password_login('+919444444444', 'NewPassword')
        assert new_login['success'] is True

    def test_reset_password_without_otp(self, db, auth_parent):
        """2026-02-17: Test reset fails without verified reset OTP."""
        result = AuthService.parent_reset_password(
            phone=auth_parent.phone,
            new_password='HackedPass',
        )
        assert result['success'] is False
        assert result['code'] == 'PHONE_NOT_VERIFIED'

    def test_reset_password_not_found(self, db):
        """2026-02-17: Test reset fails for non-existent phone."""
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+910000000088',
            otp_hash=otp_hash,
            purpose='reset',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        result = AuthService.parent_reset_password(
            phone='+910000000088',
            new_password='AnyPass',
        )
        assert result['success'] is False
        assert result['code'] == 'PARENT_NOT_FOUND'

    def test_forgot_password_endpoint(self, api_client, mock_otp_provider):
        """2026-02-17: Test POST /api/v1/auth/forgot-password/ endpoint."""
        # 2026-02-17: Register parent
        otp_hash = AuthService._hash_value('123456')
        OTPRequest.objects.create(
            phone='+919444444443',
            otp_hash=otp_hash,
            purpose='registration',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )
        AuthService.complete_registration(
            phone='+919444444443',
            full_name='Forgot Parent',
            password='ForgotOld',
        )

        # 2026-02-17: Create verified reset OTP
        reset_hash = AuthService._hash_value('654321')
        OTPRequest.objects.create(
            phone='+919444444443',
            otp_hash=reset_hash,
            purpose='reset',
            expires_at=timezone.now() + timedelta(minutes=10),
            is_verified=True,
        )

        response = api_client.post(
            '/api/v1/auth/forgot-password/',
            {'phone': '+919444444443', 'new_password': 'ForgotNew'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True

    def test_send_otp_with_reset_purpose(self, api_client):
        """2026-02-17: Test send-otp endpoint accepts 'reset' purpose."""
        response = api_client.post(
            '/api/v1/auth/send-otp/',
            {'phone': '+919444444442', 'purpose': 'reset'},
            format='json',
        )
        assert response.status_code == 200
        assert response.data['success'] is True
        # 2026-02-17: Verify OTP was created with reset purpose
        assert OTPRequest.objects.filter(
            phone='+919444444442', purpose='reset'
        ).exists()
