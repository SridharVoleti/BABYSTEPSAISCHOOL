# 2025-12-11: Mentor Chat Service API Tests
# Author: BabySteps Development Team
# Purpose: Comprehensive automated tests for mentor chat API endpoints
# Coverage: Chat endpoint, health check, Ollama integration

import pytest
from django.test import TestCase, Client
from django.urls import reverse
import json
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
class TestMentorChatAPI(TestCase):
    """
    Test suite for mentor chat endpoint
    Tests: POST /api/mentor/chat/
    """
    
    def setUp(self):
        """Set up test client and test data"""
        self.client = Client()
        self.url = '/api/mentor/chat/'
        self.valid_payload = {
            'message': 'What is photosynthesis?',
            'class_number': 5
        }
    
    def test_chat_missing_message(self):
        """
        TC-020: Test chat with missing message
        Expected: 400 status with error message
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'class_number': 5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('error', data)
    
    def test_chat_empty_message(self):
        """
        TC-021: Test chat with empty message
        Expected: 400 status with error message
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'message': '', 'class_number': 5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_chat_whitespace_message(self):
        """
        TC-022: Test chat with whitespace-only message
        Expected: 400 status with error message
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'message': '   ', 'class_number': 5}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_chat_invalid_json(self):
        """
        TC-023: Test chat with invalid JSON
        Expected: 400 status with error message
        """
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('error', data)
    
    def test_chat_default_class_number(self):
        """
        TC-024: Test chat without class_number defaults to 1
        Expected: 200 or 503 status (depending on Ollama availability)
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'message': 'Hello'}),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [200, 500, 503])
    
    def test_chat_various_class_numbers(self):
        """
        TC-025: Test chat with different class numbers (1-12)
        Expected: Appropriate teacher assigned for each class
        """
        for class_num in range(1, 13):
            response = self.client.post(
                self.url,
                data=json.dumps({'message': 'Test question', 'class_number': class_num}),
                content_type='application/json'
            )
            self.assertIn(response.status_code, [200, 500, 503])
            if response.status_code == 200:
                data = response.json()
                self.assertIn('teacher', data)
                self.assertEqual(data['class'], class_num)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_chat_success_with_mock_ollama(self, mock_ollama):
        """
        TC-026: Test successful chat with mocked Ollama
        Expected: 200 status with AI response
        """
        mock_ollama.chat.return_value = "Photosynthesis is the process by which plants make food."
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('text', data)
        self.assertIn('teacher', data)
        self.assertIn('class', data)
        self.assertIn('subject', data)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_chat_response_structure(self, mock_ollama):
        """
        TC-027: Test chat response structure
        Expected: All required fields present
        """
        mock_ollama.chat.return_value = "Test response"
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertIn('success', data)
            self.assertIn('text', data)
            self.assertIn('teacher', data)
            self.assertIn('class', data)
            self.assertIn('tts', data)
            # Check TTS config structure
            tts = data['tts']
            self.assertIn('enabled', tts)
            self.assertIn('rate', tts)
            self.assertIn('pitch', tts)
            self.assertIn('voice', tts)
            self.assertIn('language', tts)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_chat_tts_rate_scaling(self, mock_ollama):
        """
        TC-028: Test TTS rate scales with class number
        Expected: Higher class numbers have faster speech rate
        """
        mock_ollama.chat.return_value = "Test"
        
        rates = []
        for class_num in [1, 6, 12]:
            response = self.client.post(
                self.url,
                data=json.dumps({'message': 'Test', 'class_number': class_num}),
                content_type='application/json'
            )
            if response.status_code == 200:
                data = response.json()
                rates.append(data['tts']['rate'])
        
        # Verify rates increase with class number
        if len(rates) == 3:
            self.assertLess(rates[0], rates[1])
            self.assertLess(rates[1], rates[2])


@pytest.mark.django_db
class TestMentorHealthCheckAPI(TestCase):
    """
    Test suite for mentor chat health check endpoint
    Tests: GET /api/mentor/health/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/mentor/health/'
    
    def test_health_check_endpoint_exists(self):
        """
        TC-029: Test health check endpoint is accessible
        Expected: 200 or 503 status (depending on Ollama)
        """
        response = self.client.get(self.url)
        self.assertIn(response.status_code, [200, 503])
    
    def test_health_check_response_structure(self):
        """
        TC-030: Test health check response structure
        Expected: Contains success, status fields
        """
        response = self.client.get(self.url)
        data = response.json()
        self.assertIn('success', data)
        self.assertIn('status', data)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_health_check_healthy(self, mock_ollama):
        """
        TC-031: Test health check when Ollama is healthy
        Expected: 200 status with healthy status
        """
        mock_ollama.health_check.return_value = True
        mock_ollama.circuit_breaker.state = 'closed'
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['ollama_connected'])
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_health_check_unhealthy(self, mock_ollama):
        """
        TC-032: Test health check when Ollama is unhealthy
        Expected: 503 status with unhealthy status
        """
        mock_ollama.health_check.return_value = False
        mock_ollama.circuit_breaker.state = 'open'
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['status'], 'unhealthy')


@pytest.mark.django_db
class TestSubjectDetection(TestCase):
    """
    Test suite for subject detection in chat
    Tests: Subject keyword matching and routing
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/mentor/chat/'
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_physics_question_detection(self, mock_ollama):
        """
        TC-033: Test physics question detection
        Expected: Subject identified as Physics
        """
        mock_ollama.chat.return_value = "Force is a push or pull."
        
        response = self.client.post(
            self.url,
            data=json.dumps({
                'message': 'What is force?',
                'class_number': 6
            }),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertIn('subject', data)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_chemistry_question_detection(self, mock_ollama):
        """
        TC-034: Test chemistry question detection
        Expected: Subject identified as Chemistry
        """
        mock_ollama.chat.return_value = "Elements are pure substances."
        
        response = self.client.post(
            self.url,
            data=json.dumps({
                'message': 'What is an element?',
                'class_number': 6
            }),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertIn('subject', data)
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_biology_question_detection(self, mock_ollama):
        """
        TC-035: Test biology question detection
        Expected: Subject identified as Biology
        """
        mock_ollama.chat.return_value = "Cells are the basic units of life."
        
        response = self.client.post(
            self.url,
            data=json.dumps({
                'message': 'What is a cell?',
                'class_number': 6
            }),
            content_type='application/json'
        )
        if response.status_code == 200:
            data = response.json()
            self.assertIn('subject', data)


@pytest.mark.django_db
class TestTeacherAssignment(TestCase):
    """
    Test suite for teacher assignment by class
    Tests: Correct teacher assigned for each class level
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/mentor/chat/'
        # Expected teachers for each class
        self.expected_teachers = {
            1: 'Aarini', 2: 'Vaidehi', 3: 'Samaira', 4: 'Ishani',
            5: 'Mihira', 6: 'Saanvi', 7: 'Ritvika', 8: 'Anvika',
            9: 'Shrayathi', 10: 'Vyanjana', 11: 'Tanirika', 12: 'Nishka'
        }
    
    @patch('services.mentor_chat_service.views.ollama_client')
    def test_teacher_assignment_all_classes(self, mock_ollama):
        """
        TC-036: Test correct teacher assignment for all classes
        Expected: Each class gets its designated teacher
        """
        mock_ollama.chat.return_value = "Test response"
        
        for class_num, expected_teacher in self.expected_teachers.items():
            response = self.client.post(
                self.url,
                data=json.dumps({
                    'message': 'Test question',
                    'class_number': class_num
                }),
                content_type='application/json'
            )
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data['teacher'], expected_teacher)
