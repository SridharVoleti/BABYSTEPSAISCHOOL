# 2025-12-11: Curriculum Models Tests
# Author: BabySteps Development Team
# Purpose: Comprehensive automated tests for curriculum data models
# Coverage: All model validations, relationships, and constraints

import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from services.curriculum_loader_service.models import (
    CurriculumMetadata,
    LessonFile,
    QuestionBankFile,
    CurriculumCache
)
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestCurriculumMetadataModel(TestCase):
    """
    Test suite for CurriculumMetadata model
    Tests: Model creation, validation, constraints
    """
    
    def test_create_curriculum_metadata(self):
        """
        TC-037: Test creating curriculum metadata
        Expected: Model instance created successfully
        """
        curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='EVS',
            total_months=10,
            total_weeks=40,
            curriculum_path='curriculam/class_1/EVS',
            version='1.0',
            academic_year='2025-2026'
        )
        self.assertEqual(curriculum.class_number, 1)
        self.assertEqual(curriculum.subject, 'EVS')
        self.assertTrue(curriculum.is_active)
    
    def test_curriculum_string_representation(self):
        """
        TC-038: Test curriculum __str__ method
        Expected: Proper string representation
        """
        curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='Math',
            curriculum_path='curriculam/class_1/Math'
        )
        expected = "Class 1 - Math (2025-2026)"
        self.assertEqual(str(curriculum), expected)
    
    def test_curriculum_unique_together_constraint(self):
        """
        TC-039: Test unique_together constraint
        Expected: Cannot create duplicate class-subject combination
        """
        CurriculumMetadata.objects.create(
            class_number=1,
            subject='EVS',
            curriculum_path='path1'
        )
        # Try to create duplicate
        with self.assertRaises(Exception):
            CurriculumMetadata.objects.create(
                class_number=1,
                subject='EVS',
                curriculum_path='path2'
            )
    
    def test_curriculum_default_values(self):
        """
        TC-040: Test default field values
        Expected: Default values set correctly
        """
        curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='Science',
            curriculum_path='path'
        )
        self.assertEqual(curriculum.total_months, 10)
        self.assertEqual(curriculum.version, '1.0')
        self.assertTrue(curriculum.is_active)
        self.assertFalse(curriculum.is_frozen)


@pytest.mark.django_db
class TestLessonFileModel(TestCase):
    """
    Test suite for LessonFile model
    Tests: Lesson file tracking and metadata
    """
    
    def setUp(self):
        """Create curriculum metadata for testing"""
        self.curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='EVS',
            curriculum_path='curriculam/class_1/EVS'
        )
    
    def test_create_lesson_file(self):
        """
        TC-041: Test creating lesson file
        Expected: Lesson file created with proper relationships
        """
        lesson = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='SCI_C1_M1_W1_D1',
            lesson_title='Introduction to Plants',
            month=1,
            week=1,
            day=1,
            file_path='curriculam/class_1/EVS/lesson.json'
        )
        self.assertEqual(lesson.curriculum, self.curriculum)
        self.assertEqual(lesson.lesson_id, 'SCI_C1_M1_W1_D1')
    
    def test_lesson_string_representation(self):
        """
        TC-042: Test lesson __str__ method
        Expected: Proper string representation
        """
        lesson = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='TEST_ID',
            lesson_title='Test Lesson',
            month=1,
            week=1,
            day=1,
            file_path='test.json'
        )
        expected = "TEST_ID: Test Lesson"
        self.assertEqual(str(lesson), expected)
    
    def test_lesson_unique_together_constraint(self):
        """
        TC-043: Test unique lesson per curriculum/month/week/day
        Expected: Cannot create duplicate lessons
        """
        LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='ID1',
            lesson_title='Lesson 1',
            month=1,
            week=1,
            day=1,
            file_path='path1.json'
        )
        with self.assertRaises(Exception):
            LessonFile.objects.create(
                curriculum=self.curriculum,
                lesson_id='ID2',
                lesson_title='Lesson 2',
                month=1,
                week=1,
                day=1,
                file_path='path2.json'
            )
    
    def test_lesson_default_values(self):
        """
        TC-044: Test lesson default field values
        Expected: Defaults set correctly
        """
        lesson = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='TEST',
            lesson_title='Test',
            month=1,
            week=1,
            day=1,
            file_path='test.json'
        )
        self.assertEqual(lesson.duration_minutes, 30)
        self.assertEqual(lesson.level, 'Foundational')
        self.assertFalse(lesson.has_tts)
        self.assertTrue(lesson.is_active)
        self.assertEqual(lesson.access_count, 0)


@pytest.mark.django_db
class TestQuestionBankFileModel(TestCase):
    """
    Test suite for QuestionBankFile model
    Tests: Question bank file tracking
    """
    
    def setUp(self):
        """Create curriculum and lesson for testing"""
        self.curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='EVS',
            curriculum_path='curriculam/class_1/EVS'
        )
        self.lesson = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='SCI_C1_M1_W1_D1',
            lesson_title='Test Lesson',
            month=1,
            week=1,
            day=1,
            file_path='lesson.json'
        )
    
    def test_create_question_bank(self):
        """
        TC-045: Test creating question bank
        Expected: Question bank created with lesson relationship
        """
        qb = QuestionBankFile.objects.create(
            lesson=self.lesson,
            qb_id='SCI_C1_M1_W1_D1_QB',
            file_path='qb.json'
        )
        self.assertEqual(qb.lesson, self.lesson)
        self.assertEqual(qb.qb_id, 'SCI_C1_M1_W1_D1_QB')
    
    def test_question_bank_one_to_one_relationship(self):
        """
        TC-046: Test one-to-one relationship with lesson
        Expected: Only one question bank per lesson
        """
        QuestionBankFile.objects.create(
            lesson=self.lesson,
            qb_id='QB1',
            file_path='qb1.json'
        )
        with self.assertRaises(Exception):
            QuestionBankFile.objects.create(
                lesson=self.lesson,
                qb_id='QB2',
                file_path='qb2.json'
            )
    
    def test_question_bank_default_values(self):
        """
        TC-047: Test question bank default values
        Expected: Defaults set correctly
        """
        qb = QuestionBankFile.objects.create(
            lesson=self.lesson,
            qb_id='TEST_QB',
            file_path='test.json'
        )
        self.assertEqual(qb.total_questions, 0)
        self.assertTrue(qb.is_active)
        self.assertEqual(qb.access_count, 0)


@pytest.mark.django_db
class TestCurriculumCacheModel(TestCase):
    """
    Test suite for CurriculumCache model
    Tests: Cache functionality and validation
    """
    
    def setUp(self):
        """Create curriculum and lesson for testing"""
        self.curriculum = CurriculumMetadata.objects.create(
            class_number=1,
            subject='EVS',
            curriculum_path='curriculam/class_1/EVS'
        )
        self.lesson = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='SCI_C1_M1_W1_D1',
            lesson_title='Test Lesson',
            month=1,
            week=1,
            day=1,
            file_path='lesson.json'
        )
    
    def test_create_cache(self):
        """
        TC-048: Test creating curriculum cache
        Expected: Cache created with JSON content
        """
        cache = CurriculumCache.objects.create(
            lesson=self.lesson,
            json_content={'test': 'data'},
            cache_key='test_key',
            content_hash='abc123'
        )
        self.assertEqual(cache.lesson, self.lesson)
        self.assertEqual(cache.json_content, {'test': 'data'})
        self.assertTrue(cache.is_valid)
    
    def test_cache_unique_key_constraint(self):
        """
        TC-049: Test unique cache key constraint
        Expected: Cannot create duplicate cache keys
        """
        CurriculumCache.objects.create(
            lesson=self.lesson,
            json_content={'data': 1},
            cache_key='unique_key',
            content_hash='hash1'
        )
        # Create another lesson for second cache
        lesson2 = LessonFile.objects.create(
            curriculum=self.curriculum,
            lesson_id='DIFF_ID',
            lesson_title='Different',
            month=1,
            week=1,
            day=2,
            file_path='diff.json'
        )
        with self.assertRaises(Exception):
            CurriculumCache.objects.create(
                lesson=lesson2,
                json_content={'data': 2},
                cache_key='unique_key',
                content_hash='hash2'
            )
    
    def test_cache_hit_count_increment(self):
        """
        TC-050: Test cache hit count tracking
        Expected: Hit count can be incremented
        """
        cache = CurriculumCache.objects.create(
            lesson=self.lesson,
            json_content={},
            cache_key='test',
            content_hash='hash'
        )
        initial_count = cache.hit_count
        cache.hit_count += 1
        cache.save()
        cache.refresh_from_db()
        self.assertEqual(cache.hit_count, initial_count + 1)
