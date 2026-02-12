"""
Student Registration Tests
Author: Cascade AI
Date: 2025-12-13
Description: TDD tests for student registration and admin approval workflow
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import StudentRegistration


# User model for admin authentication
User = get_user_model()


class StudentRegistrationModelTest(TestCase):
    """Test StudentRegistration model fields and validation"""
    
    def setUp(self):
        """Set up test data before each test"""
        # Create test registration data
        self.registration_data = {
            'student_name': 'Test Student',
            'student_email': 'student@test.com',
            'parent_name': 'Test Parent',
            'parent_email': 'parent@test.com',
            'phone': '9876543210',
            'grade': '5',
            'school_name': 'Test School',
            'address': '123 Test Street',
            'city': 'Test City',
            'state': 'Test State',
            'pincode': '123456',
            'date_of_birth': '2015-05-15',
            'preferred_language': 'english'
        }
    
    def test_create_registration_with_valid_data(self):
        """Test creating a registration with valid data"""
        # Create registration instance
        registration = StudentRegistration.objects.create(**self.registration_data)
        
        # Verify registration was created with correct data
        self.assertEqual(registration.student_name, 'Test Student')
        self.assertEqual(registration.student_email, 'student@test.com')
        self.assertEqual(registration.status, 'pending')  # Default status
        self.assertIsNotNone(registration.registration_id)  # Auto-generated ID
        self.assertIsNotNone(registration.created_at)  # Auto-timestamp
    
    def test_registration_id_is_unique(self):
        """Test that each registration gets a unique ID"""
        # Create two registrations
        reg1 = StudentRegistration.objects.create(**self.registration_data)
        reg2_data = self.registration_data.copy()
        reg2_data['student_email'] = 'student2@test.com'
        reg2 = StudentRegistration.objects.create(**reg2_data)
        
        # Verify IDs are different
        self.assertNotEqual(reg1.registration_id, reg2.registration_id)
    
    def test_default_status_is_pending(self):
        """Test that new registrations have 'pending' status by default"""
        # Create registration
        registration = StudentRegistration.objects.create(**self.registration_data)
        
        # Verify default status
        self.assertEqual(registration.status, 'pending')
    
    def test_phone_validation(self):
        """Test phone number must be exactly 10 digits"""
        # Test with invalid phone (9 digits)
        invalid_data = self.registration_data.copy()
        invalid_data['phone'] = '987654321'  # Only 9 digits
        
        with self.assertRaises(Exception):
            registration = StudentRegistration.objects.create(**invalid_data)
            registration.full_clean()  # Trigger validation
    
    def test_pincode_validation(self):
        """Test pincode must be exactly 6 digits"""
        # Test with invalid pincode
        invalid_data = self.registration_data.copy()
        invalid_data['pincode'] = '12345'  # Only 5 digits
        
        with self.assertRaises(Exception):
            registration = StudentRegistration.objects.create(**invalid_data)
            registration.full_clean()  # Trigger validation
    
    def test_email_validation(self):
        """Test email fields must contain valid email addresses"""
        # Test with invalid email
        invalid_data = self.registration_data.copy()
        invalid_data['student_email'] = 'not-an-email'
        
        with self.assertRaises(Exception):
            registration = StudentRegistration.objects.create(**invalid_data)
            registration.full_clean()  # Trigger validation
    
    def test_str_representation(self):
        """Test string representation of registration"""
        # Create registration
        registration = StudentRegistration.objects.create(**self.registration_data)
        
        # Verify string contains student name and status
        str_repr = str(registration)
        self.assertIn('Test Student', str_repr)
        self.assertIn('pending', str_repr)


class StudentRegistrationAPITest(APITestCase):
    """Test API endpoints for student registration"""
    
    def setUp(self):
        """Set up test data and admin user"""
        # Create admin user for approval tests
        self.admin_user = User.objects.create_superuser(
            username='testadmin',
            email='testadmin@test.com',
            password='testpass123'
        )
        
        # Test registration data
        self.registration_data = {
            'student_name': 'API Test Student',
            'student_email': 'apistudent@test.com',
            'parent_name': 'API Test Parent',
            'parent_email': 'apiparent@test.com',
            'phone': '9876543210',
            'grade': '5',
            'school_name': 'API Test School',
            'address': '456 API Street',
            'city': 'API City',
            'state': 'API State',
            'pincode': '654321',
            'date_of_birth': '2015-08-20',
            'preferred_language': 'telugu'
        }
    
    def test_create_registration_via_api(self):
        """Test creating a registration through POST API"""
        # Send POST request to create registration
        response = self.client.post('/api/registrations/', self.registration_data)
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('registration_id', response.data)
        self.assertEqual(response.data['student_name'], 'API Test Student')
        self.assertEqual(response.data['status'], 'pending')
    
    def test_get_all_registrations_requires_auth(self):
        """Test that listing registrations requires authentication"""
        # Attempt to get registrations without authentication
        response = self.client.get('/api/registrations/')
        
        # Verify unauthorized (403 Forbidden when using IsAuthenticated without credentials)
        # DRF returns 403 when permission is denied, 401 is for authentication schemes
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_admin_can_list_all_registrations(self):
        """Test that admin can list all pending registrations"""
        # Create some registrations
        StudentRegistration.objects.create(**self.registration_data)
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Get all registrations
        response = self.client.get('/api/registrations/')
        
        # Verify response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_approve_registration(self):
        """Test admin can approve a pending registration"""
        # Create a pending registration
        registration = StudentRegistration.objects.create(**self.registration_data)
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Approve the registration
        response = self.client.post(
            f'/api/registrations/{registration.registration_id}/approve/'
        )
        
        # Verify approval
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'approved')
        self.assertIsNotNone(registration.approved_at)
        self.assertEqual(registration.approved_by, self.admin_user)
    
    def test_reject_registration(self):
        """Test admin can reject a pending registration"""
        # Create a pending registration
        registration = StudentRegistration.objects.create(**self.registration_data)
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Reject the registration with reason
        response = self.client.post(
            f'/api/registrations/{registration.registration_id}/reject/',
            {'reason': 'Incomplete information'}
        )
        
        # Verify rejection
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh from database
        registration.refresh_from_db()
        self.assertEqual(registration.status, 'rejected')
        self.assertEqual(registration.rejection_reason, 'Incomplete information')
    
    def test_cannot_approve_already_approved_registration(self):
        """Test that already approved registrations cannot be approved again"""
        # Create and approve a registration
        registration = StudentRegistration.objects.create(**self.registration_data)
        registration.status = 'approved'
        registration.save()
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Try to approve again
        response = self.client.post(
            f'/api/registrations/{registration.registration_id}/approve/'
        )
        
        # Verify error response
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_filter_registrations_by_status(self):
        """Test filtering registrations by status"""
        # Create registrations with different statuses
        reg1 = StudentRegistration.objects.create(**self.registration_data)
        
        reg2_data = self.registration_data.copy()
        reg2_data['student_email'] = 'student2@test.com'
        reg2 = StudentRegistration.objects.create(**reg2_data)
        reg2.status = 'approved'
        reg2.save()
        
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)
        
        # Filter for pending only
        response = self.client.get('/api/registrations/?status=pending')
        
        # Verify only pending registrations returned
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], 'pending')
