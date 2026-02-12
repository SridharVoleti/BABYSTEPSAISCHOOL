"""
Mastery Tracking Models Test Suite

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Comprehensive test suite for mastery tracking models.
    Tests skill/concept tracking, mastery levels, and assessment correlation.
    
Test Coverage:
    - Skill model creation and validation
    - Concept hierarchy and relationships
    - StudentMastery tracking
    - Mastery level progression
    - Assessment evidence tracking
    - Query optimization
    
Test-Driven Development:
    These tests are written BEFORE implementation.
    Implementation must satisfy all tests.
"""

# Django imports
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import IntegrityError

# Python standard library
from datetime import timedelta
from decimal import Decimal

# Import models (to be implemented)
from services.analytics_service.models import (
    Skill,
    Concept,
    StudentMastery,
    MasteryEvidence
)


class SkillModelTestCase(TestCase):
    """
    Test suite for Skill model.
    
    Purpose:
        Test skill definition and metadata.
        Skills are learning objectives students must master.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create test data
        self.skill_data = {
            'code': 'MATH_ADD_2DIGIT',
            'name': 'Addition of 2-digit numbers',
            'description': 'Ability to add two 2-digit numbers with regrouping',
            'subject': 'Mathematics',
            'grade_level': 2,
            'difficulty': 3,
        }
    
    def test_TC_MASTERY_001_create_skill_success(self):
        """
        TC-MASTERY-001: Test successful skill creation.
        
        Expected: Skill created with all fields
        """
        # Act
        skill = Skill.objects.create(**self.skill_data)
        
        # Assert
        self.assertEqual(skill.code, 'MATH_ADD_2DIGIT')
        self.assertEqual(skill.name, 'Addition of 2-digit numbers')
        self.assertEqual(skill.subject, 'Mathematics')
        self.assertEqual(skill.grade_level, 2)
        self.assertEqual(skill.difficulty, 3)
        self.assertTrue(skill.is_active)
    
    def test_TC_MASTERY_002_skill_string_representation(self):
        """
        TC-MASTERY-002: Test skill __str__ method.
        
        Expected: Returns readable string
        """
        # Arrange
        skill = Skill.objects.create(**self.skill_data)
        
        # Act & Assert
        self.assertEqual(
            str(skill),
            'MATH_ADD_2DIGIT: Addition of 2-digit numbers (Grade 2)'
        )
    
    def test_TC_MASTERY_003_skill_code_unique(self):
        """
        TC-MASTERY-003: Test skill code uniqueness.
        
        Expected: Cannot create duplicate skill codes
        """
        # Arrange
        Skill.objects.create(**self.skill_data)
        
        # Act & Assert
        from django.db import transaction
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Skill.objects.create(**self.skill_data)
    
    def test_TC_MASTERY_004_skill_difficulty_validation(self):
        """
        TC-MASTERY-004: Test difficulty level validation.
        
        Expected: Difficulty must be 1-5
        """
        # Arrange
        self.skill_data['difficulty'] = 6
        
        # Act
        skill = Skill.objects.create(**self.skill_data)
        
        # Assert - Should raise validation error when full_clean is called
        with self.assertRaises(ValidationError):
            skill.full_clean()
    
    def test_TC_MASTERY_005_skill_prerequisites(self):
        """
        TC-MASTERY-005: Test skill prerequisite relationships.
        
        Expected: Can define prerequisite skills
        """
        # Arrange
        prereq_skill = Skill.objects.create(
            code='MATH_ADD_1DIGIT',
            name='Addition of 1-digit numbers',
            subject='Mathematics',
            grade_level=1,
            difficulty=2
        )
        main_skill = Skill.objects.create(**self.skill_data)
        
        # Act
        main_skill.prerequisites.add(prereq_skill)
        
        # Assert
        self.assertEqual(main_skill.prerequisites.count(), 1)
        self.assertIn(prereq_skill, main_skill.prerequisites.all())


class ConceptModelTestCase(TestCase):
    """
    Test suite for Concept model.
    
    Purpose:
        Test concept hierarchy and relationships.
        Concepts are knowledge nodes that form curriculum structure.
    """
    
    def setUp(self):
        """Set up test data."""
        self.concept_data = {
            'code': 'MATH_ARITHMETIC',
            'name': 'Arithmetic',
            'description': 'Basic arithmetic operations',
            'subject': 'Mathematics',
            'order': 1,
        }
    
    def test_TC_MASTERY_011_create_concept_success(self):
        """
        TC-MASTERY-011: Test successful concept creation.
        
        Expected: Concept created with all fields
        """
        # Act
        concept = Concept.objects.create(**self.concept_data)
        
        # Assert
        self.assertEqual(concept.code, 'MATH_ARITHMETIC')
        self.assertEqual(concept.name, 'Arithmetic')
        self.assertEqual(concept.order, 1)
        self.assertIsNone(concept.parent)
    
    def test_TC_MASTERY_012_concept_hierarchy(self):
        """
        TC-MASTERY-012: Test concept parent-child relationships.
        
        Expected: Can create concept hierarchy
        """
        # Arrange
        parent = Concept.objects.create(**self.concept_data)
        
        child_data = {
            'code': 'MATH_ADDITION',
            'name': 'Addition',
            'subject': 'Mathematics',
            'parent': parent,
            'order': 1,
        }
        
        # Act
        child = Concept.objects.create(**child_data)
        
        # Assert
        self.assertEqual(child.parent, parent)
        self.assertEqual(parent.children.count(), 1)
        self.assertIn(child, parent.children.all())
    
    def test_TC_MASTERY_013_concept_skills_relationship(self):
        """
        TC-MASTERY-013: Test concept-skill relationships.
        
        Expected: Concepts can contain multiple skills
        """
        # Arrange
        concept = Concept.objects.create(**self.concept_data)
        
        skill1 = Skill.objects.create(
            code='MATH_ADD_1',
            name='Add 1-digit',
            subject='Mathematics',
            grade_level=1,
            difficulty=1
        )
        
        skill2 = Skill.objects.create(
            code='MATH_ADD_2',
            name='Add 2-digit',
            subject='Mathematics',
            grade_level=2,
            difficulty=2
        )
        
        # Act
        skill1.concept = concept
        skill1.save()
        skill2.concept = concept
        skill2.save()
        
        # Assert
        self.assertEqual(concept.skills.count(), 2)


class StudentMasteryModelTestCase(TestCase):
    """
    Test suite for StudentMastery model.
    
    Purpose:
        Test student mastery tracking and progression.
        Tracks how well students have mastered each skill.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.student = User.objects.create_user(
            username='student1',
            password='password123'
        )
        
        # Create skill
        self.skill = Skill.objects.create(
            code='MATH_ADD_2DIGIT',
            name='Addition of 2-digit numbers',
            subject='Mathematics',
            grade_level=2,
            difficulty=3
        )
        
        # Mastery data
        self.mastery_data = {
            'student': self.student,
            'skill': self.skill,
            'mastery_level': 3,
            'confidence_score': Decimal('75.5'),
            'practice_count': 10,
            'success_count': 8,
        }
    
    def test_TC_MASTERY_021_create_mastery_success(self):
        """
        TC-MASTERY-021: Test successful mastery record creation.
        
        Expected: StudentMastery created with all fields
        """
        # Act
        mastery = StudentMastery.objects.create(**self.mastery_data)
        
        # Assert
        self.assertEqual(mastery.student, self.student)
        self.assertEqual(mastery.skill, self.skill)
        self.assertEqual(mastery.mastery_level, 3)
        self.assertEqual(mastery.confidence_score, Decimal('75.5'))
        self.assertIsNotNone(mastery.first_attempted)
        self.assertIsNotNone(mastery.last_practiced)
    
    def test_TC_MASTERY_022_unique_student_skill(self):
        """
        TC-MASTERY-022: Test unique constraint on student+skill.
        
        Expected: Cannot have duplicate mastery records
        """
        # Arrange
        StudentMastery.objects.create(**self.mastery_data)
        
        # Act & Assert
        from django.db import transaction
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                StudentMastery.objects.create(**self.mastery_data)
    
    def test_TC_MASTERY_023_mastery_level_validation(self):
        """
        TC-MASTERY-023: Test mastery level validation.
        
        Expected: Mastery level must be 0-5
        """
        # Arrange
        self.mastery_data['mastery_level'] = 6
        
        # Act
        mastery = StudentMastery.objects.create(**self.mastery_data)
        
        # Assert
        with self.assertRaises(ValidationError):
            mastery.full_clean()
    
    def test_TC_MASTERY_024_success_rate_calculation(self):
        """
        TC-MASTERY-024: Test success rate calculation.
        
        Expected: Calculates success_rate correctly
        """
        # Arrange & Act
        mastery = StudentMastery.objects.create(**self.mastery_data)
        
        # Assert
        expected_rate = (8 / 10) * 100  # 80%
        self.assertEqual(mastery.success_rate(), expected_rate)
    
    def test_TC_MASTERY_025_success_rate_no_practice(self):
        """
        TC-MASTERY-025: Test success rate with no practice.
        
        Expected: Returns 0 if no practice attempts
        """
        # Arrange
        self.mastery_data['practice_count'] = 0
        self.mastery_data['success_count'] = 0
        
        # Act
        mastery = StudentMastery.objects.create(**self.mastery_data)
        
        # Assert
        self.assertEqual(mastery.success_rate(), 0)
    
    def test_TC_MASTERY_026_update_mastery_level(self):
        """
        TC-MASTERY-026: Test mastery level update.
        
        Expected: Can update mastery level and timestamps
        """
        # Arrange
        mastery = StudentMastery.objects.create(**self.mastery_data)
        original_time = mastery.last_practiced
        
        # Wait a moment
        import time
        time.sleep(0.1)
        
        # Act
        mastery.mastery_level = 4
        mastery.save()
        
        # Assert
        self.assertEqual(mastery.mastery_level, 4)
        self.assertGreater(mastery.updated_at, mastery.created_at)
    
    def test_TC_MASTERY_027_is_mastered_check(self):
        """
        TC-MASTERY-027: Test is_mastered() method.
        
        Expected: Returns True if mastery_level >= 4
        """
        # Arrange
        mastery = StudentMastery.objects.create(**self.mastery_data)
        
        # Act & Assert
        mastery.mastery_level = 3
        self.assertFalse(mastery.is_mastered())
        
        mastery.mastery_level = 4
        self.assertTrue(mastery.is_mastered())
        
        mastery.mastery_level = 5
        self.assertTrue(mastery.is_mastered())


class MasteryEvidenceModelTestCase(TestCase):
    """
    Test suite for MasteryEvidence model.
    
    Purpose:
        Test evidence tracking for mastery claims.
        Links mastery to specific assessment results.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user and skill
        self.student = User.objects.create_user(
            username='student1',
            password='password123'
        )
        
        self.skill = Skill.objects.create(
            code='MATH_ADD_2DIGIT',
            name='Addition of 2-digit numbers',
            subject='Mathematics',
            grade_level=2,
            difficulty=3
        )
        
        self.mastery = StudentMastery.objects.create(
            student=self.student,
            skill=self.skill,
            mastery_level=3,
            confidence_score=Decimal('75.0')
        )
        
        self.evidence_data = {
            'mastery': self.mastery,
            'evidence_type': 'quiz',
            'score': Decimal('85.0'),
            'max_score': Decimal('100.0'),
            'assessment_id': 'quiz_123',
        }
    
    def test_TC_MASTERY_031_create_evidence_success(self):
        """
        TC-MASTERY-031: Test evidence creation.
        
        Expected: MasteryEvidence created successfully
        """
        # Act
        evidence = MasteryEvidence.objects.create(**self.evidence_data)
        
        # Assert
        self.assertEqual(evidence.mastery, self.mastery)
        self.assertEqual(evidence.evidence_type, 'quiz')
        self.assertEqual(evidence.score, Decimal('85.0'))
        self.assertIsNotNone(evidence.recorded_at)
    
    def test_TC_MASTERY_032_evidence_score_percentage(self):
        """
        TC-MASTERY-032: Test score percentage calculation.
        
        Expected: Calculates percentage correctly
        """
        # Arrange & Act
        evidence = MasteryEvidence.objects.create(**self.evidence_data)
        
        # Assert
        expected = (85.0 / 100.0) * 100
        self.assertEqual(evidence.score_percentage(), expected)
    
    def test_TC_MASTERY_033_multiple_evidence_per_mastery(self):
        """
        TC-MASTERY-033: Test multiple evidence items.
        
        Expected: Can have multiple evidence for same mastery
        """
        # Act
        evidence1 = MasteryEvidence.objects.create(**self.evidence_data)
        
        evidence2_data = self.evidence_data.copy()
        evidence2_data['assessment_id'] = 'quiz_124'
        evidence2_data['score'] = Decimal('90.0')
        evidence2 = MasteryEvidence.objects.create(**evidence2_data)
        
        # Assert
        self.assertEqual(self.mastery.evidence.count(), 2)
        self.assertIn(evidence1, self.mastery.evidence.all())
        self.assertIn(evidence2, self.mastery.evidence.all())
    
    def test_TC_MASTERY_034_evidence_ordering(self):
        """
        TC-MASTERY-034: Test evidence ordering.
        
        Expected: Evidence ordered by most recent first
        """
        # Arrange
        import time
        
        evidence1 = MasteryEvidence.objects.create(**self.evidence_data)
        time.sleep(0.1)
        
        evidence2_data = self.evidence_data.copy()
        evidence2_data['assessment_id'] = 'quiz_124'
        evidence2 = MasteryEvidence.objects.create(**evidence2_data)
        
        # Act
        evidence_list = list(self.mastery.evidence.all())
        
        # Assert
        self.assertEqual(evidence_list[0], evidence2)  # Most recent first
        self.assertEqual(evidence_list[1], evidence1)


class MasteryQueryTestCase(TestCase):
    """
    Test suite for mastery query optimization.
    
    Purpose:
        Test query efficiency and filtering.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.student1 = User.objects.create_user(username='student1')
        self.student2 = User.objects.create_user(username='student2')
        
        # Create skills
        self.skill1 = Skill.objects.create(
            code='SKILL1',
            name='Skill 1',
            subject='Math',
            grade_level=1
        )
        self.skill2 = Skill.objects.create(
            code='SKILL2',
            name='Skill 2',
            subject='Science',
            grade_level=1
        )
        
        # Create mastery records
        StudentMastery.objects.create(
            student=self.student1,
            skill=self.skill1,
            mastery_level=4
        )
        StudentMastery.objects.create(
            student=self.student1,
            skill=self.skill2,
            mastery_level=3
        )
        StudentMastery.objects.create(
            student=self.student2,
            skill=self.skill1,
            mastery_level=5
        )
    
    def test_TC_MASTERY_101_filter_by_student(self):
        """
        TC-MASTERY-101: Test filtering by student.
        
        Expected: Returns only student's mastery records
        """
        # Act
        masteries = StudentMastery.objects.filter(student=self.student1)
        
        # Assert
        self.assertEqual(masteries.count(), 2)
        for mastery in masteries:
            self.assertEqual(mastery.student, self.student1)
    
    def test_TC_MASTERY_102_filter_mastered_skills(self):
        """
        TC-MASTERY-102: Test filtering mastered skills.
        
        Expected: Returns only mastered skills (level >= 4)
        """
        # Act
        mastered = StudentMastery.objects.filter(mastery_level__gte=4)
        
        # Assert
        self.assertEqual(mastered.count(), 2)
        for mastery in mastered:
            self.assertGreaterEqual(mastery.mastery_level, 4)
    
    def test_TC_MASTERY_103_filter_by_subject(self):
        """
        TC-MASTERY-103: Test filtering by skill subject.
        
        Expected: Returns masteries for specific subject
        """
        # Act
        math_masteries = StudentMastery.objects.filter(skill__subject='Math')
        
        # Assert
        self.assertEqual(math_masteries.count(), 2)
        for mastery in math_masteries:
            self.assertEqual(mastery.skill.subject, 'Math')
