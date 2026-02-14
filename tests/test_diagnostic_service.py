"""
2026-02-12: Integration tests for diagnostic assessment service API.

Purpose:
    Test the full diagnostic flow: start session, submit responses,
    check status, and retrieve results. Uses Django test client
    with authenticated student requests.
"""

import pytest  # 2026-02-12: Pytest framework
from datetime import date  # 2026-02-12: Date for DOB

from django.contrib.auth import get_user_model  # 2026-02-12: User model
from rest_framework.test import APIClient  # 2026-02-12: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-12: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-12: Auth models
from services.diagnostic_service.models import (  # 2026-02-12: Diagnostic models
    DiagnosticSession, DiagnosticResponse, DiagnosticResult,
)
from services.diagnostic_service.irt import load_question_bank  # 2026-02-12: Question bank

User = get_user_model()  # 2026-02-12: Django User model


@pytest.fixture
def parent_user(db):
    """2026-02-12: Create a parent user for testing."""
    user = User.objects.create_user(  # 2026-02-12: Django user
        username='test_parent_diag', password='testpass123'
    )
    parent = Parent.objects.create(  # 2026-02-12: Parent profile
        user=user,
        phone='+919876543210',
        full_name='Test Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student_user(parent_user, db):
    """2026-02-12: Create a student user for testing."""
    user = User.objects.create_user(  # 2026-02-12: Django user for student
        username='test_student_diag', password='testpass123'
    )
    student = Student.objects.create(  # 2026-02-12: Student profile
        parent=parent_user,
        user=user,
        full_name='Test Student',
        dob=date(2016, 5, 15),  # 2026-02-12: Age ~10, group 6-12
        age_group='6-12',
        grade=4,
        login_method='pin',
    )
    return student


@pytest.fixture
def student_client(student_user):
    """2026-02-12: Authenticated API client for student."""
    client = APIClient()  # 2026-02-12: DRF test client
    token = RefreshToken.for_user(student_user.user)  # 2026-02-12: Generate token
    client.credentials(  # 2026-02-12: Set auth header
        HTTP_AUTHORIZATION=f'Bearer {token.access_token}'
    )
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-12: Authenticated API client for parent (should be denied)."""
    client = APIClient()  # 2026-02-12: DRF test client
    token = RefreshToken.for_user(parent_user.user)  # 2026-02-12: Generate token
    client.credentials(  # 2026-02-12: Set auth header
        HTTP_AUTHORIZATION=f'Bearer {token.access_token}'
    )
    return client


@pytest.mark.django_db
class TestDiagnosticStartAPI:
    """2026-02-12: Tests for POST /api/v1/diagnostic/start/."""

    def test_start_session(self, student_client):
        """2026-02-12: Student should be able to start a diagnostic session."""
        response = student_client.post('/api/v1/diagnostic/start/')
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert 'session_id' in data
        assert data['total_items'] == 25
        assert data['items_administered'] == 0
        assert 'current_item' in data
        assert 'question' in data['current_item']
        assert 'options' in data['current_item']

    def test_resume_existing_session(self, student_client):
        """2026-02-12: Starting again should resume existing session."""
        resp1 = student_client.post('/api/v1/diagnostic/start/')
        resp2 = student_client.post('/api/v1/diagnostic/start/')
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # 2026-02-12: Should be same session
        assert resp2.json()['session_id'] == resp1.json()['session_id']

    def test_parent_denied(self, parent_client):
        """2026-02-12: Parent users should be denied access."""
        response = parent_client.post('/api/v1/diagnostic/start/')
        assert response.status_code == 403

    def test_unauthenticated_denied(self):
        """2026-02-12: Unauthenticated requests should be denied."""
        client = APIClient()  # 2026-02-12: No auth
        response = client.post('/api/v1/diagnostic/start/')
        assert response.status_code == 401


@pytest.mark.django_db
class TestDiagnosticRespondAPI:
    """2026-02-12: Tests for POST /api/v1/diagnostic/respond/."""

    def test_submit_response(self, student_client):
        """2026-02-12: Should accept a response and return next item."""
        # 2026-02-12: Start session
        start_resp = student_client.post('/api/v1/diagnostic/start/')
        start_data = start_resp.json()
        item_id = start_data['current_item']['id']

        # 2026-02-12: Submit response
        response = student_client.post('/api/v1/diagnostic/respond/', {
            'item_id': item_id,
            'selected_option': 0,
            'response_time_ms': 5000,
        }, format='json')

        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['items_administered'] == 1

    def test_wrong_item_id_rejected(self, student_client):
        """2026-02-12: Submitting wrong item ID should fail."""
        student_client.post('/api/v1/diagnostic/start/')

        response = student_client.post('/api/v1/diagnostic/respond/', {
            'item_id': 'FAKE_ITEM',
            'selected_option': 0,
        }, format='json')

        assert response.status_code == 400
        assert response.json()['code'] == 'ITEM_MISMATCH'

    def test_no_session_error(self, student_client):
        """2026-02-12: Responding without session should fail."""
        response = student_client.post('/api/v1/diagnostic/respond/', {
            'item_id': 'MATH_01',
            'selected_option': 0,
        }, format='json')

        assert response.status_code == 400
        assert response.json()['code'] == 'NO_SESSION'

    def test_complete_assessment(self, student_client):
        """2026-02-12: Completing all 25 items should return final result."""
        # 2026-02-12: Start session
        start_resp = student_client.post('/api/v1/diagnostic/start/')
        data = start_resp.json()

        # 2026-02-12: Answer all 25 items
        for i in range(25):
            item_id = data['current_item']['id']
            resp = student_client.post('/api/v1/diagnostic/respond/', {
                'item_id': item_id,
                'selected_option': 0,  # 2026-02-12: Just pick first option
                'response_time_ms': 3000,
            }, format='json')
            data = resp.json()
            assert data['success'] is True

            if data.get('is_complete'):
                break

        # 2026-02-12: Should be complete
        assert data['is_complete'] is True
        assert 'result' in data
        assert data['result']['overall_level'] in ['foundation', 'standard', 'advanced']
        assert 'domain_levels' in data['result']

    def test_cannot_restart_after_complete(self, student_client):
        """2026-02-12: Cannot start new session after completing assessment."""
        # 2026-02-12: Complete the assessment
        start_resp = student_client.post('/api/v1/diagnostic/start/')
        data = start_resp.json()

        for i in range(25):
            item_id = data['current_item']['id']
            resp = student_client.post('/api/v1/diagnostic/respond/', {
                'item_id': item_id,
                'selected_option': 0,
            }, format='json')
            data = resp.json()
            if data.get('is_complete'):
                break

        # 2026-02-12: Try to start again
        restart_resp = student_client.post('/api/v1/diagnostic/start/')
        assert restart_resp.status_code == 400
        assert restart_resp.json()['code'] == 'ALREADY_COMPLETED'


@pytest.mark.django_db
class TestDiagnosticStatusAPI:
    """2026-02-12: Tests for GET /api/v1/diagnostic/status/."""

    def test_not_started(self, student_client):
        """2026-02-12: Status should be not_started before starting."""
        response = student_client.get('/api/v1/diagnostic/status/')
        assert response.status_code == 200
        assert response.json()['status'] == 'not_started'

    def test_in_progress(self, student_client):
        """2026-02-12: Status should be in_progress after starting."""
        student_client.post('/api/v1/diagnostic/start/')
        response = student_client.get('/api/v1/diagnostic/status/')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'in_progress'
        assert 'current_item' in data

    def test_completed(self, student_client):
        """2026-02-12: Status should be completed after finishing."""
        # 2026-02-12: Complete assessment
        start_resp = student_client.post('/api/v1/diagnostic/start/')
        data = start_resp.json()

        for i in range(25):
            item_id = data['current_item']['id']
            resp = student_client.post('/api/v1/diagnostic/respond/', {
                'item_id': item_id,
                'selected_option': 0,
            }, format='json')
            data = resp.json()
            if data.get('is_complete'):
                break

        # 2026-02-12: Check status
        status_resp = student_client.get('/api/v1/diagnostic/status/')
        assert status_resp.status_code == 200
        assert status_resp.json()['status'] == 'completed'


@pytest.mark.django_db
class TestDiagnosticResultAPI:
    """2026-02-12: Tests for GET /api/v1/diagnostic/result/."""

    def test_no_result_before_completion(self, student_client):
        """2026-02-12: Should return 404 before assessment is completed."""
        response = student_client.get('/api/v1/diagnostic/result/')
        assert response.status_code == 404

    def test_result_after_completion(self, student_client):
        """2026-02-12: Should return result after completing assessment."""
        # 2026-02-12: Complete assessment
        start_resp = student_client.post('/api/v1/diagnostic/start/')
        data = start_resp.json()

        for i in range(25):
            item_id = data['current_item']['id']
            resp = student_client.post('/api/v1/diagnostic/respond/', {
                'item_id': item_id,
                'selected_option': 0,
            }, format='json')
            data = resp.json()
            if data.get('is_complete'):
                break

        # 2026-02-12: Get result
        result_resp = student_client.get('/api/v1/diagnostic/result/')
        assert result_resp.status_code == 200
        result = result_resp.json()
        assert result['success'] is True
        assert result['result']['overall_level'] in ['foundation', 'standard', 'advanced']
        assert 'theta_final' in result['result']
        assert 'domain_levels' in result['result']
