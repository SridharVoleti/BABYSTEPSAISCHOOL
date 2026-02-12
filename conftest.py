# 2025-12-11: Pytest configuration and fixtures
# Author: BabySteps Development Team
# Purpose: Shared test fixtures and configuration

import pytest
import os
import django
from django.conf import settings

# Configure Django settings for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

def pytest_configure(config):
    """
    Configure Django for pytest
    Called before test collection
    """
    if not settings.configured:
        django.setup()

@pytest.fixture(scope='session')
def django_db_setup():
    """
    Setup test database
    This fixture is session-scoped to improve performance
    """
    pass

@pytest.fixture
def api_client():
    """
    Fixture to provide Django test client
    """
    from django.test import Client
    return Client()

@pytest.fixture
def sample_curriculum():
    """
    Fixture to provide sample curriculum data
    """
    return {
        'class_number': 1,
        'subject': 'EVS',
        'month': 1,
        'week': 1,
        'day': 1
    }

@pytest.fixture
def sample_lesson():
    """
    Fixture to provide sample lesson structure
    """
    return {
        'metadata': {
            'lesson_id': 'TEST_L1',
            'lesson_title': 'Test Lesson',
            'class': 'Class 1',
            'subject': 'EVS',
            'duration_minutes': 30,
            'level': 'Foundational'
        },
        'objectives': {
            'primary_objective': 'Learn about plants',
            'learning_outcomes': ['Identify plants', 'Understand growth']
        },
        'vocabulary': {
            'word_list': [
                {
                    'word': 'plant',
                    'definition': 'A living organism',
                    'example_usage': 'The plant grows.'
                }
            ]
        },
        'content_blocks': [
            {
                'id': 'block1',
                'type': 'text',
                'text': 'Welcome to the lesson!'
            }
        ]
    }

@pytest.fixture
def mock_ollama_response():
    """
    Fixture to provide mock Ollama chat response
    """
    return {
        'success': True,
        'text': 'This is a test response from the AI mentor.',
        'teacher': 'Aarini',
        'class': 1,
        'subject': 'Science',
        'tts': {
            'enabled': True,
            'rate': 0.7,
            'pitch': 1.0,
            'voice': 'female',
            'language': 'en-IN'
        }
    }
