"""
Adaptive Difficulty Adjustment Test Suite

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Comprehensive test suite for adaptive difficulty adjustment system.
    Tests performance-based difficulty scaling and optimal challenge calculation.
    
Test Coverage:
    - DifficultyProfile model creation and validation
    - Performance tracking
    - Difficulty level adjustment algorithms
    - Optimal challenge zone calculation
    - Real-time difficulty scaling
    - Learning curve analysis
    
Test-Driven Development:
    These tests are written BEFORE implementation.
    Implementation must satisfy all tests.
"""

# Django imports
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

# Python standard library
from datetime import timedelta
from decimal import Decimal

# Import models (to be implemented)
from services.analytics_service.models import (
    DifficultyProfile,
    PerformanceSnapshot,
    ContentDifficulty,
    StudentMastery,
    Skill,
)


class DifficultyProfileModelTestCase(TestCase):
    """
    Test suite for DifficultyProfile model.
    
    Purpose:
        Test student difficulty profile tracking.
        Profiles track current difficulty level and adjustment history.
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
            code='MATH_ADD',
            name='Addition',
            subject='Mathematics',
            grade_level=2,
            difficulty=3
        )
        
        # Profile data
        self.profile_data = {
            'student': self.student,
            'skill': self.skill,
            'current_difficulty': Decimal('50.0'),
            'target_success_rate': Decimal('75.0'),
            'adjustment_speed': Decimal('5.0'),
        }
    
    def test_TC_DIFF_001_create_profile_success(self):
        """
        TC-DIFF-001: Test successful difficulty profile creation.
        
        Expected: DifficultyProfile created with all fields
        """
        # Act
        profile = DifficultyProfile.objects.create(**self.profile_data)
        
        # Assert
        self.assertEqual(profile.student, self.student)
        self.assertEqual(profile.skill, self.skill)
        self.assertEqual(profile.current_difficulty, Decimal('50.0'))
        self.assertEqual(profile.target_success_rate, Decimal('75.0'))
    
    def test_TC_DIFF_002_unique_student_skill(self):
        """
        TC-DIFF-002: Test unique constraint on student+skill.
        
        Expected: Cannot create duplicate profiles
        """
        # Arrange
        DifficultyProfile.objects.create(**self.profile_data)
        
        # Act & Assert
        from django.db import transaction, IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                DifficultyProfile.objects.create(**self.profile_data)
    
    def test_TC_DIFF_003_difficulty_range_validation(self):
        """
        TC-DIFF-003: Test difficulty range validation.
        
        Expected: Difficulty must be 0-100
        """
        # Arrange
        self.profile_data['current_difficulty'] = Decimal('150.0')
        
        # Act
        profile = DifficultyProfile.objects.create(**self.profile_data)
        
        # Assert
        with self.assertRaises(ValidationError):
            profile.full_clean()
    
    def test_TC_DIFF_004_suggest_difficulty_increase(self):
        """
        TC-DIFF-004: Test difficulty increase suggestion.
        
        Expected: Suggests increase when performance is high
        """
        # Arrange
        profile = DifficultyProfile.objects.create(**self.profile_data)
        
        # Act - simulate high performance (90% success)
        suggested = profile.suggest_next_difficulty(success_rate=90.0)
        
        # Assert
        self.assertGreater(suggested, float(profile.current_difficulty))
    
    def test_TC_DIFF_005_suggest_difficulty_decrease(self):
        """
        TC-DIFF-005: Test difficulty decrease suggestion.
        
        Expected: Suggests decrease when performance is low
        """
        # Arrange
        profile = DifficultyProfile.objects.create(**self.profile_data)
        
        # Act - simulate low performance (40% success)
        suggested = profile.suggest_next_difficulty(success_rate=40.0)
        
        # Assert
        self.assertLess(suggested, float(profile.current_difficulty))
    
    def test_TC_DIFF_006_maintain_difficulty_optimal(self):
        """
        TC-DIFF-006: Test difficulty maintenance at optimal.
        
        Expected: Maintains when performance is at target
        """
        # Arrange
        profile = DifficultyProfile.objects.create(**self.profile_data)
        
        # Act - simulate target performance (75% success)
        suggested = profile.suggest_next_difficulty(success_rate=75.0)
        
        # Assert
        # Should stay close to current difficulty
        self.assertAlmostEqual(suggested, float(profile.current_difficulty), delta=2.0)
    
    def test_TC_DIFF_007_apply_difficulty_adjustment(self):
        """
        TC-DIFF-007: Test applying difficulty adjustment.
        
        Expected: Updates current difficulty and records history
        """
        # Arrange
        profile = DifficultyProfile.objects.create(**self.profile_data)
        initial_difficulty = float(profile.current_difficulty)
        
        # Act
        new_difficulty = profile.apply_adjustment(Decimal('60.0'))
        
        # Assert
        self.assertEqual(new_difficulty, Decimal('60.0'))
        self.assertNotEqual(float(profile.current_difficulty), initial_difficulty)
    
    def test_TC_DIFF_008_adjustment_speed_factor(self):
        """
        TC-DIFF-008: Test adjustment speed affects change rate.
        
        Expected: Higher speed = larger adjustments
        """
        # Arrange
        slow_profile = DifficultyProfile.objects.create(
            student=self.student,
            skill=self.skill,
            current_difficulty=Decimal('50.0'),
            adjustment_speed=Decimal('2.0')
        )
        
        # Need different skill for unique constraint
        fast_skill = Skill.objects.create(
            code='MATH_SUB',
            name='Subtraction',
            subject='Mathematics',
            grade_level=2
        )
        
        fast_profile = DifficultyProfile.objects.create(
            student=self.student,
            skill=fast_skill,
            current_difficulty=Decimal('50.0'),
            adjustment_speed=Decimal('10.0')
        )
        
        # Act
        slow_adjustment = slow_profile.suggest_next_difficulty(success_rate=90.0)
        fast_adjustment = fast_profile.suggest_next_difficulty(success_rate=90.0)
        
        # Assert
        self.assertGreater(abs(fast_adjustment - 50.0), abs(slow_adjustment - 50.0))


class PerformanceSnapshotModelTestCase(TestCase):
    """
    Test suite for PerformanceSnapshot model.
    
    Purpose:
        Test performance snapshot tracking for difficulty adjustment.
        Snapshots capture performance at specific points in time.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user and skill
        self.student = User.objects.create_user(username='student1')
        
        self.skill = Skill.objects.create(
            code='MATH_ADD',
            name='Addition',
            subject='Mathematics',
            grade_level=2
        )
        
        # Snapshot data
        self.snapshot_data = {
            'student': self.student,
            'skill': self.skill,
            'difficulty_level': Decimal('50.0'),
            'attempts': 10,
            'successes': 8,
            'avg_time_seconds': 30,
        }
    
    def test_TC_DIFF_011_create_snapshot_success(self):
        """
        TC-DIFF-011: Test snapshot creation.
        
        Expected: PerformanceSnapshot created successfully
        """
        # Act
        snapshot = PerformanceSnapshot.objects.create(**self.snapshot_data)
        
        # Assert
        self.assertEqual(snapshot.student, self.student)
        self.assertEqual(snapshot.skill, self.skill)
        self.assertEqual(snapshot.attempts, 10)
        self.assertEqual(snapshot.successes, 8)
    
    def test_TC_DIFF_012_calculate_success_rate(self):
        """
        TC-DIFF-012: Test success rate calculation.
        
        Expected: Calculates percentage correctly
        """
        # Arrange & Act
        snapshot = PerformanceSnapshot.objects.create(**self.snapshot_data)
        success_rate = snapshot.calculate_success_rate()
        
        # Assert
        self.assertEqual(success_rate, 80.0)  # 8/10 = 80%
    
    def test_TC_DIFF_013_performance_trend_analysis(self):
        """
        TC-DIFF-013: Test performance trend over time.
        
        Expected: Can analyze improving/declining performance
        """
        # Arrange - create multiple snapshots with explicit timestamps
        import time
        for i in range(3):
            snapshot = PerformanceSnapshot(
                student=self.student,
                skill=self.skill,
                difficulty_level=Decimal('50.0'),
                attempts=10,
                successes=5 + i * 2,  # Improving: 50%, 70%, 90%
                avg_time_seconds=30
            )
            snapshot.save()
            time.sleep(0.01)  # Small delay to ensure ordering
        
        # Act
        snapshots = PerformanceSnapshot.objects.filter(
            student=self.student,
            skill=self.skill
        ).order_by('recorded_at')
        
        rates = [s.calculate_success_rate() for s in snapshots]
        
        # Assert - should be improving
        self.assertEqual(len(rates), 3)
        self.assertLess(rates[0], rates[1])
        self.assertLess(rates[1], rates[2])


class ContentDifficultyModelTestCase(TestCase):
    """
    Test suite for ContentDifficulty model.
    
    Purpose:
        Test content difficulty rating and metadata.
        Tracks difficulty of individual content items.
    """
    
    def setUp(self):
        """Set up test data."""
        self.difficulty_data = {
            'content_id': 'lesson_math_001',
            'content_type': 'lesson',
            'base_difficulty': Decimal('60.0'),
            'cognitive_load': Decimal('70.0'),
            'complexity_score': Decimal('65.0'),
        }
    
    def test_TC_DIFF_021_create_content_difficulty(self):
        """
        TC-DIFF-021: Test content difficulty creation.
        
        Expected: ContentDifficulty created successfully
        """
        # Act
        content = ContentDifficulty.objects.create(**self.difficulty_data)
        
        # Assert
        self.assertEqual(content.content_id, 'lesson_math_001')
        self.assertEqual(content.base_difficulty, Decimal('60.0'))
    
    def test_TC_DIFF_022_calculate_effective_difficulty(self):
        """
        TC-DIFF-022: Test effective difficulty calculation.
        
        Expected: Combines base difficulty with cognitive load
        """
        # Arrange & Act
        content = ContentDifficulty.objects.create(**self.difficulty_data)
        effective = content.calculate_effective_difficulty()
        
        # Assert
        # Should be weighted average of factors
        self.assertGreater(effective, 0)
        self.assertLessEqual(effective, 100)
    
    def test_TC_DIFF_023_adjust_for_prerequisites(self):
        """
        TC-DIFF-023: Test difficulty adjustment for prerequisites.
        
        Expected: Difficulty increases if prerequisites not met
        """
        # Arrange
        content = ContentDifficulty.objects.create(**self.difficulty_data)
        
        # Act
        adjusted = content.adjust_for_student(
            has_prerequisites=False
        )
        
        # Assert
        # Should be harder without prerequisites
        self.assertGreater(adjusted, float(content.base_difficulty))


class AdaptiveDifficultyAlgorithmTestCase(TestCase):
    """
    Test suite for adaptive difficulty algorithms.
    
    Purpose:
        Test the algorithms that adjust difficulty in real-time.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create student
        self.student = User.objects.create_user(username='student1')
        
        # Create skill
        self.skill = Skill.objects.create(
            code='MATH_ADD',
            name='Addition',
            subject='Mathematics',
            grade_level=2,
            difficulty=3
        )
        
        # Create mastery record
        self.mastery = StudentMastery.objects.create(
            student=self.student,
            skill=self.skill,
            mastery_level=2,
            practice_count=20,
            success_count=15
        )
    
    def test_TC_DIFF_101_calculate_optimal_difficulty(self):
        """
        TC-DIFF-101: Test optimal difficulty calculation.
        
        Expected: Returns difficulty in optimal challenge zone
        """
        # Import algorithm (to be implemented)
        from services.analytics_service.adaptive_difficulty import calculate_optimal_difficulty
        
        # Act
        optimal = calculate_optimal_difficulty(self.student, self.skill)
        
        # Assert
        self.assertIsNotNone(optimal)
        self.assertGreaterEqual(optimal, 0)
        self.assertLessEqual(optimal, 100)
    
    def test_TC_DIFF_102_zone_of_proximal_development(self):
        """
        TC-DIFF-102: Test ZPD-based difficulty.
        
        Expected: Difficulty slightly above current ability
        """
        from services.analytics_service.adaptive_difficulty import calculate_optimal_difficulty
        
        # Act
        optimal = calculate_optimal_difficulty(self.student, self.skill)
        
        # Assert
        # Should be achievable but challenging
        # With 75% success rate, difficulty should promote growth
        self.assertGreater(optimal, 40)  # Not too easy
        self.assertLess(optimal, 85)     # Not too hard
    
    def test_TC_DIFF_103_adjust_based_on_recent_performance(self):
        """
        TC-DIFF-103: Test adjustment based on recent performance.
        
        Expected: Recent performance weighs more heavily
        """
        from services.analytics_service.adaptive_difficulty import adjust_difficulty_realtime
        
        # Arrange - create recent poor performance
        for i in range(5):
            PerformanceSnapshot.objects.create(
                student=self.student,
                skill=self.skill,
                difficulty_level=Decimal('70.0'),
                attempts=10,
                successes=3,  # Only 30% success
                avg_time_seconds=45,
                recorded_at=timezone.now() - timedelta(hours=i)
            )
        
        # Act
        adjusted = adjust_difficulty_realtime(self.student, self.skill)
        
        # Assert
        # Should decrease due to poor performance
        self.assertLess(adjusted, 70.0)
    
    def test_TC_DIFF_104_prevent_extreme_adjustments(self):
        """
        TC-DIFF-104: Test prevention of extreme difficulty swings.
        
        Expected: Adjustments are gradual and bounded
        """
        from services.analytics_service.adaptive_difficulty import adjust_difficulty_realtime
        
        # Arrange - create profile at 50 difficulty
        profile = DifficultyProfile.objects.create(
            student=self.student,
            skill=self.skill,
            current_difficulty=Decimal('50.0')
        )
        
        # Create extreme performance (100% success)
        PerformanceSnapshot.objects.create(
            student=self.student,
            skill=self.skill,
            difficulty_level=Decimal('50.0'),
            attempts=10,
            successes=10,
            avg_time_seconds=20
        )
        
        # Act
        adjusted = adjust_difficulty_realtime(self.student, self.skill)
        
        # Assert
        # Should increase but not dramatically
        self.assertGreater(adjusted, 50.0)
        self.assertLess(adjusted, 70.0)  # No more than 20 point jump
    
    def test_TC_DIFF_105_flow_state_optimization(self):
        """
        TC-DIFF-105: Test flow state optimization.
        
        Expected: Targets difficulty for flow state (70-80% success)
        """
        from services.analytics_service.adaptive_difficulty import calculate_optimal_difficulty
        
        # Arrange - student with consistent 85% success (too easy)
        self.mastery.mastery_level = 4  # High mastery
        self.mastery.practice_count = 30
        self.mastery.success_count = 26  # 86.7% success
        self.mastery.save()
        
        # Act
        optimal = calculate_optimal_difficulty(self.student, self.skill)
        
        # Assert
        # Should suggest higher difficulty to reach flow state
        # With mastery level 4 (80% ability) and high success rate
        self.assertGreater(optimal, 60)
