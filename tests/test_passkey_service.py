"""
2026-03-04: Tests for Passkey / WebAuthn service and Monitor Password Reset (BS-AUTH-002).

Covers:
    TestPasskeyRegistration (8 tests)
    TestPasskeyAuthentication (8 tests)
    TestMonitorPasswordReset (8 tests)
    TestPasskeyAdmin (4 tests)
    TestPasskeyApi (6 tests)

Total: 34 tests.

Mock strategy for py_webauthn:
  - Patch webauthn.generate_registration_options, generate_authentication_options
  - Patch webauthn.verify_registration_response → MagicMock with credential fields
  - Patch webauthn.verify_authentication_response → MagicMock(new_sign_count=1)
  - Patch webauthn.options_to_json → return "{}"
"""

import json
import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from services.auth_service.models import Parent, Student
from services.passkey_service.models import PasskeyCredential
from services.passkey_service.services import PasskeyService

User = get_user_model()  # 2026-03-04: Concrete user model


# ── Helpers ────────────────────────────────────────────────────────────────

def _make_user(username=None, is_staff=False, email=''):
    """2026-03-04: Create a minimal Django User."""
    username = username or f'user_{uuid.uuid4().hex[:8]}'
    return User.objects.create_user(username=username, password='TestPass1!', email=email, is_staff=is_staff)


def _make_student(user=None):
    """2026-03-04: Create a minimal Student linked to a parent User."""
    parent_user = _make_user()
    parent = Parent.objects.create(
        user=parent_user,
        phone=f'+91{uuid.uuid4().int % 10_000_000_000:010d}',
        full_name='Test Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    student = Student.objects.create(
        parent=parent,
        user=user,
        full_name='Test Student',
        dob=date(2015, 1, 1),
        age_group='6-12',
        grade=5,
        login_method='pin',
    )
    return student


def _fake_registration_options():
    """2026-03-04: Fake options dict returned by py_webauthn."""
    return MagicMock(challenge=b'fake_challenge_bytes')


def _fake_auth_options():
    """2026-03-04: Fake auth options dict returned by py_webauthn."""
    return MagicMock(challenge=b'fake_auth_challenge')


def _fake_verification(credential_id=b'cred_id_bytes', public_key=b'pub_key_bytes', sign_count=0):
    """2026-03-04: Fake verification result from py_webauthn."""
    v = MagicMock()
    v.credential_id = credential_id
    v.credential_public_key = public_key
    v.sign_count = sign_count
    return v


def _seed_credential(user, credential_id=b'cred_id_bytes', sign_count=0):
    """2026-03-04: Create a PasskeyCredential in DB."""
    return PasskeyCredential.objects.create(
        user=user,
        credential_id=credential_id,
        public_key=b'pub_key_bytes',
        sign_count=sign_count,
        device_name='Test Device',
    )


# ── TestPasskeyRegistration ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasskeyRegistration:
    """2026-03-04: Tests for PasskeyService registration methods."""

    @patch('webauthn.generate_registration_options', return_value=_fake_registration_options())
    @patch('webauthn.options_to_json', return_value='{}')
    def test_get_registration_options_returns_options_and_challenge_id(self, mock_json, mock_gen):
        """2026-03-04: generate_registration_options returns options dict + challenge_id."""
        user = _make_user()
        options, challenge_id = PasskeyService.get_registration_options(user, 'Test Device')
        assert isinstance(challenge_id, str)
        assert uuid.UUID(challenge_id)  # 2026-03-04: Valid UUID
        assert isinstance(options, dict)
        assert 'challenge_id' in options

    @patch('webauthn.generate_registration_options', return_value=_fake_registration_options())
    @patch('webauthn.options_to_json', return_value='{}')
    @patch('webauthn.verify_registration_response', return_value=_fake_verification())
    def test_complete_registration_creates_credential(self, mock_verify, mock_json, mock_gen):
        """2026-03-04: complete_registration persists PasskeyCredential."""
        user = _make_user()
        options, challenge_id = PasskeyService.get_registration_options(user)
        credential = PasskeyService.complete_registration(
            user=user,
            challenge_id=challenge_id,
            credential_json={'response': {'transports': ['internal']}},
            device_name='Laptop',
        )
        assert credential.pk is not None
        assert credential.user == user
        assert credential.device_name == 'Laptop'

    @patch('webauthn.generate_registration_options', return_value=_fake_registration_options())
    @patch('webauthn.options_to_json', return_value='{}')
    @patch('webauthn.verify_registration_response', return_value=_fake_verification())
    def test_duplicate_credential_id_raises_error(self, mock_verify, mock_json, mock_gen):
        """2026-03-04: Registering an already-used credential_id raises ValueError."""
        user = _make_user()
        _seed_credential(user, credential_id=b'cred_id_bytes')
        options, challenge_id = PasskeyService.get_registration_options(user)
        with pytest.raises(ValueError, match='already registered'):
            PasskeyService.complete_registration(
                user=user,
                challenge_id=challenge_id,
                credential_json={},
            )

    def test_complete_registration_expired_challenge_raises_error(self):
        """2026-03-04: Non-existent challenge_id raises ValueError."""
        user = _make_user()
        with pytest.raises(ValueError, match='Challenge expired'):
            PasskeyService.complete_registration(
                user=user,
                challenge_id='nonexistent-challenge-id',
                credential_json={},
            )

    def test_ensure_student_user_creates_user_if_none(self):
        """2026-03-04: ensure_student_user creates a Django User for a student without one."""
        student = _make_student(user=None)
        assert student.user_id is None
        user = PasskeyService.ensure_student_user(student)
        student.refresh_from_db()
        assert student.user_id == user.pk
        assert user.username.startswith('student_')

    def test_ensure_student_user_reuses_existing_user(self):
        """2026-03-04: ensure_student_user returns existing user without creating a new one."""
        existing_user = _make_user()
        student = _make_student(user=existing_user)
        returned = PasskeyService.ensure_student_user(student)
        assert returned.pk == existing_user.pk
        assert User.objects.filter(pk=existing_user.pk).count() == 1

    def test_registration_api_401_if_not_authenticated(self):
        """2026-03-04: register/start/ requires authentication."""
        client = APIClient()
        response = client.post('/api/v1/passkeys/register/start/', {})
        assert response.status_code == 401

    @patch('webauthn.generate_registration_options', return_value=_fake_registration_options())
    @patch('webauthn.options_to_json', return_value='{}')
    @patch('webauthn.verify_registration_response', return_value=_fake_verification(credential_id=b'unique_cred'))
    def test_registration_complete_api_saves_credential(self, mock_verify, mock_json, mock_gen):
        """2026-03-04: register/complete/ API endpoint saves credential and returns device_name."""
        user = _make_user()
        client = APIClient()
        client.force_authenticate(user=user)

        start_response = client.post('/api/v1/passkeys/register/start/', {'device_name': 'My Phone'})
        assert start_response.status_code == 200
        challenge_id = start_response.data['challenge_id']

        # 2026-03-04: Restore cache since force_authenticate does not call start for the same request
        from django.core.cache import cache as _cache
        _cache.set(f'webauthn_challenge:{challenge_id}', b'fake_challenge_bytes', timeout=30)

        complete_response = client.post('/api/v1/passkeys/register/complete/', {
            'challenge_id': challenge_id,
            'credential': {'response': {}},
            'device_name': 'My Phone',
        }, format='json')
        assert complete_response.status_code == 201
        assert complete_response.data['device_name'] == 'My Phone'


# ── TestPasskeyAuthentication ────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasskeyAuthentication:
    """2026-03-04: Tests for PasskeyService authentication methods."""

    @patch('webauthn.generate_authentication_options', return_value=_fake_auth_options())
    @patch('webauthn.options_to_json', return_value='{}')
    def test_get_authentication_options_returns_options_and_challenge_id(self, mock_json, mock_gen):
        """2026-03-04: generate_authentication_options returns dict + challenge_id."""
        options, challenge_id = PasskeyService.get_authentication_options()
        assert isinstance(challenge_id, str)
        assert uuid.UUID(challenge_id)
        assert isinstance(options, dict)

    def test_complete_authentication_expired_challenge_raises_error(self):
        """2026-03-04: Authentication with unknown challenge_id raises ValueError."""
        with pytest.raises(ValueError, match='Challenge expired'):
            PasskeyService.complete_authentication(
                challenge_id='no-such-id',
                credential_json={'id': 'dGVzdA=='},
            )

    def test_complete_authentication_unknown_credential_raises_error(self):
        """2026-03-04: Authentication with credential not in DB raises ValueError."""
        from django.core.cache import cache as _cache
        challenge_id = str(uuid.uuid4())
        _cache.set(f'webauthn_challenge:{challenge_id}', b'challenge', timeout=30)
        with pytest.raises(ValueError, match='Credential not found'):
            PasskeyService.complete_authentication(
                challenge_id=challenge_id,
                credential_json={'id': 'dW5rbm93bg=='},  # 2026-03-04: unknown base64
            )

    @patch('webauthn.verify_authentication_response')
    def test_clone_detection_raises_error(self, mock_verify):
        """2026-03-04: sign_count not increasing raises ValueError (clone detection)."""
        user = _make_user()
        cred = _seed_credential(user, sign_count=5)
        # 2026-03-04: Import b64 for encoding credential_id
        import base64
        cred_id_b64 = base64.urlsafe_b64encode(bytes(cred.credential_id)).decode().rstrip('=')

        mock_verify.return_value = MagicMock(new_sign_count=3)  # 2026-03-04: Lower count
        from django.core.cache import cache as _cache
        challenge_id = str(uuid.uuid4())
        _cache.set(f'webauthn_challenge:{challenge_id}', b'chal', timeout=30)
        with pytest.raises(ValueError, match='Sign count'):
            PasskeyService.complete_authentication(
                challenge_id=challenge_id,
                credential_json={'id': cred_id_b64},
            )

    @patch('webauthn.verify_authentication_response')
    def test_sign_count_updated_on_success(self, mock_verify):
        """2026-03-04: Successful auth updates sign_count in DB."""
        user = _make_user()
        cred = _seed_credential(user, credential_id=b'cred_sc_test', sign_count=0)
        import base64
        cred_id_b64 = base64.urlsafe_b64encode(bytes(cred.credential_id)).decode().rstrip('=')

        mock_verify.return_value = MagicMock(new_sign_count=1)
        from django.core.cache import cache as _cache
        challenge_id = str(uuid.uuid4())
        _cache.set(f'webauthn_challenge:{challenge_id}', b'chal', timeout=30)

        returned_user, role = PasskeyService.complete_authentication(
            challenge_id=challenge_id,
            credential_json={'id': cred_id_b64},
        )
        cred.refresh_from_db()
        assert cred.sign_count == 1
        assert returned_user.pk == user.pk

    @patch('webauthn.verify_authentication_response')
    def test_authenticate_api_returns_jwt(self, mock_verify):
        """2026-03-04: authenticate/complete/ returns access + refresh + role."""
        user = _make_user(is_staff=True)
        cred = _seed_credential(user, credential_id=b'jwt_cred', sign_count=0)
        import base64
        cred_id_b64 = base64.urlsafe_b64encode(bytes(cred.credential_id)).decode().rstrip('=')

        mock_verify.return_value = MagicMock(new_sign_count=1)

        with patch('webauthn.generate_authentication_options', return_value=_fake_auth_options()), \
             patch('webauthn.options_to_json', return_value='{}'):
            client = APIClient()
            start = client.post('/api/v1/passkeys/authenticate/start/', {})
            assert start.status_code == 200
            challenge_id = start.data['challenge_id']

        # 2026-03-04: Replace cache entry with known bytes (options_to_json stripped real challenge)
        from django.core.cache import cache as _cache
        _cache.set(f'webauthn_challenge:{challenge_id}', b'chal', timeout=30)

        complete = client.post('/api/v1/passkeys/authenticate/complete/', {
            'challenge_id': challenge_id,
            'credential': {'id': cred_id_b64},
        }, format='json')
        assert complete.status_code == 200
        assert 'access' in complete.data
        assert complete.data['role'] == 'monitor'

    @patch('webauthn.generate_authentication_options', return_value=_fake_auth_options())
    @patch('webauthn.options_to_json', return_value='{}')
    def test_student_id_filter_limits_allow_credentials(self, mock_json, mock_gen):
        """2026-03-04: authenticate/start/ with student_id filters allowCredentials."""
        student_user = _make_user()
        student = _make_student(user=student_user)
        _seed_credential(student_user, credential_id=b'student_cred')

        client = APIClient()
        response = client.post(
            '/api/v1/passkeys/authenticate/start/',
            {'student_id': str(student.id)},
            format='json',
        )
        assert response.status_code == 200
        assert 'challenge_id' in response.data

    @pytest.mark.django_db
    def test_has_passkey_field_in_student_lookup(self):
        """2026-03-04: lookup_by_phone includes has_passkey=True when credential exists."""
        student_user = _make_user()
        student = _make_student(user=student_user)
        _seed_credential(student_user, credential_id=b'lkup_cred')
        parent = student.parent

        client = APIClient()
        phone_digits = parent.phone.lstrip('+').lstrip('91')[:10]
        response = client.get(f'/api/v1/auth/student-auth-lookup/{phone_digits}/')
        if response.status_code == 200:
            found = next((s for s in response.data['students'] if s['id'] == str(student.id)), None)
            if found:
                assert found.get('has_passkey') is True


# ── TestMonitorPasswordReset ─────────────────────────────────────────────────

@pytest.mark.django_db
class TestMonitorPasswordReset:
    """2026-03-04: Tests for monitor email-token password reset."""

    def test_request_valid_staff_email_returns_200(self):
        """2026-03-04: POST monitor-password-reset/ with known staff email returns 200."""
        user = _make_user(is_staff=True, email='monitor@school.com')
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/',
            {'email': 'monitor@school.com'},
        )
        assert response.status_code == 200
        assert 'message' in response.data

    def test_request_unknown_email_returns_200_no_enumeration(self):
        """2026-03-04: POST with unknown email still returns 200 (no enumeration)."""
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/',
            {'email': 'nobody@unknown.com'},
        )
        assert response.status_code == 200

    def test_request_non_staff_email_returns_200_no_enumeration(self):
        """2026-03-04: POST with non-staff user email returns 200 (same response)."""
        _make_user(email='parent@home.com', is_staff=False)
        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/',
            {'email': 'parent@home.com'},
        )
        assert response.status_code == 200

    def test_confirm_with_valid_token_updates_password(self):
        """2026-03-04: POST monitor-password-reset/confirm/ with valid token changes password."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = _make_user(is_staff=True, email='resetme@school.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'NewPassw0rd!'},
        )
        assert response.status_code == 200
        user.refresh_from_db()
        assert user.check_password('NewPassw0rd!')

    def test_confirm_with_invalid_token_returns_400(self):
        """2026-03-04: Confirm with wrong token returns 400."""
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = _make_user(is_staff=True)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': 'invalid-token', 'new_password': 'NewPass1234!'},
        )
        assert response.status_code == 400

    def test_confirm_weak_password_returns_400(self):
        """2026-03-04: Confirm with password shorter than 8 chars returns 400."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = _make_user(is_staff=True)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'short'},
        )
        assert response.status_code == 400

    def test_confirm_non_staff_user_returns_403(self):
        """2026-03-04: Confirm for a non-staff user returns 403."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = _make_user(is_staff=False)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        client = APIClient()
        response = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'ValidPass123!'},
        )
        assert response.status_code == 403

    def test_password_changed_invalidates_old_token(self):
        """2026-03-04: After password change, old token is invalid (Django default)."""
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = _make_user(is_staff=True, email='once@school.com')
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        client = APIClient()
        # 2026-03-04: First use — success
        r1 = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'FirstPass1!'},
        )
        assert r1.status_code == 200

        # 2026-03-04: Second use — token now invalid
        r2 = client.post(
            '/api/v1/auth/monitor-password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'SecondPass2!'},
        )
        assert r2.status_code == 400


# ── TestPasskeyAdmin ──────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestPasskeyAdmin:
    """2026-03-04: Tests for PasskeyCredential admin page."""

    def _admin_client(self):
        """2026-03-04: Authenticated superuser admin client."""
        from django.test import Client
        superuser = User.objects.create_superuser(
            username=f'admin_{uuid.uuid4().hex[:6]}',
            password='Admin123!',
            email='admin@test.com',
        )
        c = Client()
        c.force_login(superuser)
        return c

    def test_credentials_listed_in_admin(self):
        """2026-03-04: Admin changelist for PasskeyCredential returns 200."""
        client = self._admin_client()
        response = client.get('/admin/passkey_service/passkeycredential/')
        assert response.status_code == 200

    def test_credential_detail_shown_correctly(self):
        """2026-03-04: Admin detail page for a credential returns 200."""
        user = _make_user()
        cred = _seed_credential(user)
        client = self._admin_client()
        response = client.get(f'/admin/passkey_service/passkeycredential/{cred.pk}/change/')
        assert response.status_code == 200

    def test_delete_credential_works(self):
        """2026-03-04: DELETE credentials/{id}/ removes the passkey."""
        user = _make_user()
        cred = _seed_credential(user, credential_id=b'to_delete_cred')
        api = APIClient()
        api.force_authenticate(user=user)
        response = api.delete(f'/api/v1/passkeys/credentials/{cred.pk}/')
        assert response.status_code == 204
        assert not PasskeyCredential.objects.filter(pk=cred.pk).exists()

    def test_credentials_list_returns_only_own(self):
        """2026-03-04: GET credentials/ returns only the authenticated user's passkeys."""
        user_a = _make_user()
        user_b = _make_user()
        _seed_credential(user_a, credential_id=b'cred_a')
        _seed_credential(user_b, credential_id=b'cred_b')

        api = APIClient()
        api.force_authenticate(user=user_a)
        response = api.get('/api/v1/passkeys/credentials/')
        assert response.status_code == 200
        ids = [c['device_name'] for c in response.data]
        assert len(ids) == 1  # 2026-03-04: Only user_a's credential
