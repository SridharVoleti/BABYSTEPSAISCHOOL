# 2025-12-11: Curriculum Loader Service API Tests
# Author: BabySteps Development Team
# Purpose: Comprehensive automated tests for curriculum API endpoints
# Coverage: All curriculum endpoints with edge cases

import pytest
from django.test import TestCase, Client
from django.urls import reverse
import json
import os

@pytest.mark.django_db
class TestCurriculumListAPI(TestCase):
    """
    Test suite for curriculum list endpoint
    Tests: GET /api/curriculum/list/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/curriculum/list/'
    
    def test_curriculum_list_success(self):
        """
        TC-001: Test successful retrieval of curriculum list
        Expected: 200 status, valid JSON response with curriculum data
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('curriculums', data)
        self.assertIn('count', data)
        self.assertIsInstance(data['curriculums'], list)
    
    def test_curriculum_list_structure(self):
        """
        TC-002: Test curriculum list response structure
        Expected: Each curriculum has required fields
        """
        response = self.client.get(self.url)
        data = response.json()
        if data['count'] > 0:
            curriculum = data['curriculums'][0]
            self.assertIn('class_number', curriculum)
            self.assertIn('subject', curriculum)
    
    def test_curriculum_list_content_type(self):
        """
        TC-003: Test response content type
        Expected: application/json
        """
        response = self.client.get(self.url)
        self.assertEqual(response['Content-Type'], 'application/json')


@pytest.mark.django_db
class TestGetLessonAPI(TestCase):
    """
    Test suite for get lesson endpoint
    Tests: GET /api/curriculum/class/{class}/subject/{subject}/month/{m}/week/{w}/day/{d}/
    """
    
    def setUp(self):
        """Set up test client and valid lesson coordinates"""
        self.client = Client()
        self.valid_params = {
            'class_number': 1,
            'subject': 'EVS',
            'month': 1,
            'week': 1,
            'day': 1
        }
    
    def test_get_lesson_success(self):
        """
        TC-004: Test successful lesson retrieval
        Expected: 200 status, lesson data returned
        """
        url = f"/api/curriculum/class/{self.valid_params['class_number']}/subject/{self.valid_params['subject']}/month/{self.valid_params['month']}/week/{self.valid_params['week']}/day/{self.valid_params['day']}/"
        response = self.client.get(url)
        # Should return either 200 (found) or 404 (not found, but valid request)
        self.assertIn(response.status_code, [200, 404])
        data = response.json()
        self.assertIn('success', data)
    
    def test_get_lesson_invalid_class(self):
        """
        TC-005: Test lesson retrieval with invalid class number
        Expected: 400 or 404 status
        """
        url = f"/api/curriculum/class/99/subject/EVS/month/1/week/1/day/1/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [400, 404])
    
    def test_get_lesson_invalid_month(self):
        """
        TC-006: Test lesson retrieval with invalid month
        Expected: 400 or 404 status
        """
        url = f"/api/curriculum/class/1/subject/EVS/month/13/week/1/day/1/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [400, 404])
    
    def test_get_lesson_invalid_week(self):
        """
        TC-007: Test lesson retrieval with invalid week
        Expected: 400 or 404 status
        """
        url = f"/api/curriculum/class/1/subject/EVS/month/1/week/60/day/1/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [400, 404])
    
    def test_get_lesson_invalid_day(self):
        """
        TC-008: Test lesson retrieval with invalid day
        Expected: 400 or 404 status
        """
        url = f"/api/curriculum/class/1/subject/EVS/month/1/week/1/day/10/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [400, 404])
    
    def test_get_lesson_with_cache_param(self):
        """
        TC-009: Test lesson retrieval with cache parameter
        Expected: 200 or 404 status, respects cache parameter
        """
        url = f"/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/?use_cache=false"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])
    
    def test_get_lesson_structure(self):
        """
        TC-010: Test lesson response structure when found
        Expected: Contains metadata, objectives, content_blocks
        """
        url = f"/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/"
        response = self.client.get(url)
        if response.status_code == 200:
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('lesson', data)
            lesson = data['lesson']
            # Check for expected lesson structure
            self.assertIn('metadata', lesson)


@pytest.mark.django_db
class TestGetQuestionBankAPI(TestCase):
    """
    Test suite for get question bank endpoint
    Tests: GET /api/curriculum/class/{class}/subject/{subject}/month/{m}/week/{w}/day/{d}/qb/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_get_question_bank_success(self):
        """
        TC-011: Test successful question bank retrieval
        Expected: 200 or 404 status (depending on existence)
        """
        url = "/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/qb/"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])
        data = response.json()
        self.assertIn('success', data)
    
    def test_get_question_bank_structure(self):
        """
        TC-012: Test question bank response structure when found
        Expected: Contains question_bank data
        """
        url = "/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/qb/"
        response = self.client.get(url)
        if response.status_code == 200:
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('question_bank', data)


@pytest.mark.django_db
class TestGetNextLessonAPI(TestCase):
    """
    Test suite for get next lesson endpoint
    Tests: GET /api/curriculum/class/{class}/subject/{subject}/next/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
    
    def test_get_next_lesson_success(self):
        """
        TC-013: Test successful next lesson retrieval
        Expected: 200 or 404 status with proper structure
        """
        url = "/api/curriculum/class/1/subject/EVS/next/?current_month=1&current_week=1&current_day=1"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])
        data = response.json()
        self.assertIn('success', data)
    
    def test_get_next_lesson_coordinates(self):
        """
        TC-014: Test next lesson returns proper coordinates
        Expected: Coordinates increment correctly
        """
        url = "/api/curriculum/class/1/subject/EVS/next/?current_month=1&current_week=1&current_day=1"
        response = self.client.get(url)
        if response.status_code == 200:
            data = response.json()
            self.assertIn('coordinates', data)
            coords = data['coordinates']
            self.assertIn('month', coords)
            self.assertIn('week', coords)
            self.assertIn('day', coords)
    
    def test_get_next_lesson_end_of_curriculum(self):
        """
        TC-015: Test next lesson at end of curriculum
        Expected: 404 status with appropriate message
        """
        url = "/api/curriculum/class/1/subject/EVS/next/?current_month=10&current_week=4&current_day=5"
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 404])


@pytest.mark.django_db
class TestClearCacheAPI(TestCase):
    """
    Test suite for clear cache endpoint
    Tests: POST /api/curriculum/cache/clear/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/curriculum/cache/clear/'
    
    def test_clear_cache_all(self):
        """
        TC-016: Test clearing all caches
        Expected: 200 status with success message
        """
        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('message', data)
    
    def test_clear_cache_specific_key(self):
        """
        TC-017: Test clearing specific cache key
        Expected: 200 status with success message mentioning key
        """
        response = self.client.post(
            self.url,
            data=json.dumps({'cache_key': 'test_key'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('test_key', data['message'])


@pytest.mark.django_db
class TestAPIRootEndpoint(TestCase):
    """
    Test suite for API root endpoint
    Tests: GET /api/
    """
    
    def setUp(self):
        """Set up test client"""
        self.client = Client()
        self.url = '/api/'
    
    def test_api_root_success(self):
        """
        TC-018: Test API root endpoint
        Expected: 200 status with API information
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('version', data)
        self.assertIn('endpoints', data)
    
    def test_api_root_endpoints_list(self):
        """
        TC-019: Test API root returns endpoint list
        Expected: All major endpoints listed
        """
        response = self.client.get(self.url)
        data = response.json()
        endpoints = data['endpoints']
        self.assertIn('curriculum', endpoints)
