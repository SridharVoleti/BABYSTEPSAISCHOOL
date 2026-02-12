# 2025-12-18: Learning Engine Model Tests
# Author: BabySteps Development Team
# Purpose: TDD tests for learning engine models
# Last Modified: 2025-12-18

"""
Test Suite for Learning Engine Models

Tests cover:
- StudentLearningProfile: streak calculations, profile updates
- MicroLesson: structure validation, PRD compliance
- MicroLessonProgress: mastery calculations, step progression
- PracticeAttempt: answer validation, feedback
- DifficultyCalibration: adaptive difficulty adjustments
"""

# 2025-12-18: Import pytest for testing
import pytest

# 2025-12-18: Import Django test utilities
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

# 2025-12-18: Import datetime for date manipulation
from datetime import date, timedelta

# 2025-12-18: Import models to test
from services.learning_engine.models import (
    StudentLearningProfile,
    MicroLesson,
    MicroLessonProgress,
    PracticeAttempt,
    DifficultyCalibration,
)

# 2025-12-18: Get User model
User = get_user_model()


class TestStudentLearningProfile(TestCase):
    """
    2025-12-18: Test cases for StudentLearningProfile model.
    Tests streak calculations and profile management.
    """
    
    def setUp(self):
        """2025-12-18: Set up test user and profile."""
        # 2025-12-18: Create test user
        self.user = User.objects.create_user(
            username='teststudent',
            email='test@example.com',
            password='testpass123'
        )
        # 2025-12-18: Create learning profile
        self.profile = StudentLearningProfile.objects.create(user=self.user)
    
    def test_profile_creation(self):
        """2025-12-18: Test that profile is created with correct defaults."""
        # 2025-12-18: Verify default values
        self.assertEqual(self.profile.learning_speed, 'average')
        self.assertEqual(self.profile.preferred_explanation_mode, 'visual')
        self.assertEqual(self.profile.total_mastery_points, 0)
        self.assertEqual(self.profile.current_streak_days, 0)
        self.assertEqual(self.profile.longest_streak_days, 0)
        self.assertIsNone(self.profile.last_activity_date)
    
    def test_first_activity_starts_streak(self):
        """2025-12-18: Test that first activity starts a streak of 1."""
        # 2025-12-18: Update streak for first activity
        self.profile.update_streak()
        
        # 2025-12-18: Verify streak started
        self.assertEqual(self.profile.current_streak_days, 1)
        self.assertEqual(self.profile.last_activity_date, timezone.now().date())
    
    def test_same_day_activity_no_streak_change(self):
        """2025-12-18: Test that multiple activities on same day don't increase streak."""
        # 2025-12-18: First activity
        self.profile.update_streak()
        initial_streak = self.profile.current_streak_days
        
        # 2025-12-18: Second activity same day
        self.profile.update_streak()
        
        # 2025-12-18: Streak should not change
        self.assertEqual(self.profile.current_streak_days, initial_streak)
    
    def test_consecutive_day_increases_streak(self):
        """2025-12-18: Test that activity on consecutive day increases streak."""
        # 2025-12-18: Set last activity to yesterday
        yesterday = timezone.now().date() - timedelta(days=1)
        self.profile.last_activity_date = yesterday
        self.profile.current_streak_days = 5
        self.profile.save()
        
        # 2025-12-18: Activity today
        self.profile.update_streak()
        
        # 2025-12-18: Streak should increase
        self.assertEqual(self.profile.current_streak_days, 6)
    
    def test_missed_day_resets_streak(self):
        """2025-12-18: Test that missing a day resets streak to 1."""
        # 2025-12-18: Set last activity to 2 days ago
        two_days_ago = timezone.now().date() - timedelta(days=2)
        self.profile.last_activity_date = two_days_ago
        self.profile.current_streak_days = 10
        self.profile.save()
        
        # 2025-12-18: Activity today
        self.profile.update_streak()
        
        # 2025-12-18: Streak should reset to 1
        self.assertEqual(self.profile.current_streak_days, 1)
    
    def test_longest_streak_updated(self):
        """2025-12-18: Test that longest streak is updated when current exceeds it."""
        # 2025-12-18: Set up profile with existing streak
        yesterday = timezone.now().date() - timedelta(days=1)
        self.profile.last_activity_date = yesterday
        self.profile.current_streak_days = 5
        self.profile.longest_streak_days = 5
        self.profile.save()
        
        # 2025-12-18: Activity today increases streak
        self.profile.update_streak()
        
        # 2025-12-18: Both should be 6 now
        self.assertEqual(self.profile.current_streak_days, 6)
        self.assertEqual(self.profile.longest_streak_days, 6)
    
    def test_longest_streak_preserved_on_reset(self):
        """2025-12-18: Test that longest streak is preserved when current resets."""
        # 2025-12-18: Set up profile with high longest streak
        self.profile.longest_streak_days = 30
        self.profile.current_streak_days = 5
        self.profile.last_activity_date = timezone.now().date() - timedelta(days=3)
        self.profile.save()
        
        # 2025-12-18: Activity after gap resets current
        self.profile.update_streak()
        
        # 2025-12-18: Current reset but longest preserved
        self.assertEqual(self.profile.current_streak_days, 1)
        self.assertEqual(self.profile.longest_streak_days, 30)


class TestMicroLesson(TestCase):
    """
    2025-12-18: Test cases for MicroLesson model.
    Tests PRD compliance validation.
    """
    
    def setUp(self):
        """2025-12-18: Set up test micro-lesson."""
        # 2025-12-18: Create a valid micro-lesson
        self.valid_lesson = MicroLesson.objects.create(
            lesson_id='MATH_C5_CH1_ML1',
            title='Introduction to Fractions',
            learning_objective='Students will understand what a fraction represents and identify numerator and denominator.',
            subject='Math',
            class_number=5,
            chapter_id='CH1',
            chapter_name='Fractions',
            sequence_in_chapter=1,
            duration_minutes=7,
            worked_examples=[
                {'example': 'Example 1', 'steps': ['Step 1', 'Step 2']},
                {'example': 'Example 2', 'steps': ['Step 1', 'Step 2']}
            ],
            practice_questions=[
                {'q': f'Question {i}', 'answer': f'Answer {i}'} for i in range(1, 11)
            ],
            practice_themes=[
                'Theme 1', 'Theme 2', 'Theme 3', 'Theme 4', 
                'Theme 5', 'Theme 6', 'Theme 7'
            ],
            visual_assets=[
                {'type': 'concept_intro', 'url': '/visuals/fractions_intro.png'}
            ]
        )
    
    def test_valid_lesson_passes_validation(self):
        """2025-12-18: Test that a properly structured lesson passes validation."""
        # 2025-12-18: Validate structure
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should pass with no errors
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_wrong_worked_examples_count_fails(self):
        """2025-12-18: Test that lesson with wrong number of worked examples fails."""
        # 2025-12-18: Create lesson with only 1 worked example
        self.valid_lesson.worked_examples = [{'example': 'Only one'}]
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('worked examples' in e.lower() for e in errors))
    
    def test_wrong_practice_questions_count_fails(self):
        """2025-12-18: Test that lesson with wrong number of practice questions fails."""
        # 2025-12-18: Create lesson with only 5 questions
        self.valid_lesson.practice_questions = [{'q': f'Q{i}'} for i in range(5)]
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('practice questions' in e.lower() for e in errors))
    
    def test_too_few_practice_themes_fails(self):
        """2025-12-18: Test that lesson with fewer than 6 themes fails."""
        # 2025-12-18: Only 3 themes
        self.valid_lesson.practice_themes = ['Theme 1', 'Theme 2', 'Theme 3']
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('practice themes' in e.lower() for e in errors))
    
    def test_too_many_practice_themes_fails(self):
        """2025-12-18: Test that lesson with more than 10 themes fails."""
        # 2025-12-18: 12 themes
        self.valid_lesson.practice_themes = [f'Theme {i}' for i in range(12)]
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('practice themes' in e.lower() for e in errors))
    
    def test_missing_visual_assets_fails(self):
        """2025-12-18: Test that lesson without visual assets fails."""
        # 2025-12-18: Empty visual assets
        self.valid_lesson.visual_assets = []
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('visual' in e.lower() for e in errors))
    
    def test_missing_learning_objective_fails(self):
        """2025-12-18: Test that lesson without learning objective fails."""
        # 2025-12-18: Empty objective
        self.valid_lesson.learning_objective = ''
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('objective' in e.lower() for e in errors))
    
    def test_duration_out_of_range_fails(self):
        """2025-12-18: Test that lesson with duration outside 5-10 minutes fails."""
        # 2025-12-18: Duration too long
        self.valid_lesson.duration_minutes = 15
        
        # 2025-12-18: Validate
        is_valid, errors = self.valid_lesson.validate_structure()
        
        # 2025-12-18: Should fail
        self.assertFalse(is_valid)
        self.assertTrue(any('duration' in e.lower() for e in errors))


class TestMicroLessonProgress(TestCase):
    """
    2025-12-18: Test cases for MicroLessonProgress model.
    Tests mastery calculations and progress tracking.
    """
    
    def setUp(self):
        """2025-12-18: Set up test data."""
        # 2025-12-18: Create test user
        self.user = User.objects.create_user(
            username='progressstudent',
            email='progress@example.com',
            password='testpass123'
        )
        
        # 2025-12-18: Create test micro-lesson
        self.lesson = MicroLesson.objects.create(
            lesson_id='TEST_LESSON_1',
            title='Test Lesson',
            learning_objective='Test objective for testing purposes.',
            subject='Test',
            class_number=5,
            chapter_id='CH1',
            chapter_name='Test Chapter',
            sequence_in_chapter=1,
            duration_minutes=7,
            worked_examples=[{}, {}],
            practice_questions=[{} for _ in range(10)],
            practice_themes=['T1', 'T2', 'T3', 'T4', 'T5', 'T6'],
            visual_assets=[{'type': 'test'}]
        )
        
        # 2025-12-18: Create progress record
        self.progress = MicroLessonProgress.objects.create(
            student=self.user,
            micro_lesson=self.lesson
        )
    
    def test_progress_creation_defaults(self):
        """2025-12-18: Test that progress is created with correct defaults."""
        # 2025-12-18: Verify defaults
        self.assertEqual(self.progress.status, 'not_started')
        self.assertEqual(self.progress.current_step, 'objective')
        self.assertEqual(self.progress.questions_attempted, 0)
        self.assertEqual(self.progress.questions_correct, 0)
        self.assertEqual(self.progress.mastery_score, 0)
    
    def test_mastery_calculation_perfect_score(self):
        """2025-12-18: Test mastery calculation with perfect performance."""
        # 2025-12-18: Set up perfect performance
        self.progress.questions_attempted = 10
        self.progress.questions_correct = 10
        self.progress.time_spent_seconds = 300  # 5 minutes (within expected)
        self.progress.hints_used = 0
        
        # 2025-12-18: Calculate mastery
        mastery = self.progress.calculate_mastery()
        
        # 2025-12-18: Should be high (70 accuracy + 20 time bonus = 90)
        self.assertEqual(mastery, 90)
    
    def test_mastery_calculation_with_mistakes(self):
        """2025-12-18: Test mastery calculation with some wrong answers."""
        # 2025-12-18: Set up 70% accuracy
        self.progress.questions_attempted = 10
        self.progress.questions_correct = 7
        self.progress.time_spent_seconds = 300
        self.progress.hints_used = 0
        
        # 2025-12-18: Calculate mastery
        mastery = self.progress.calculate_mastery()
        
        # 2025-12-18: Should be 49 (70% of 70) + 20 time = 69
        self.assertEqual(mastery, 69)
    
    def test_mastery_calculation_with_hints_penalty(self):
        """2025-12-18: Test that hints reduce mastery score."""
        # 2025-12-18: Perfect accuracy but used hints
        self.progress.questions_attempted = 10
        self.progress.questions_correct = 10
        self.progress.time_spent_seconds = 300
        self.progress.hints_used = 3  # -6 points
        
        # 2025-12-18: Calculate mastery
        mastery = self.progress.calculate_mastery()
        
        # 2025-12-18: Should be 90 - 6 = 84
        self.assertEqual(mastery, 84)
    
    def test_mastery_calculation_slow_completion(self):
        """2025-12-18: Test mastery with slow completion time."""
        # 2025-12-18: Perfect accuracy but slow
        self.progress.questions_attempted = 10
        self.progress.questions_correct = 10
        self.progress.time_spent_seconds = 900  # 15 minutes (way over)
        self.progress.hints_used = 0
        
        # 2025-12-18: Calculate mastery
        mastery = self.progress.calculate_mastery()
        
        # 2025-12-18: Should be 70 (no time bonus)
        self.assertEqual(mastery, 70)
    
    def test_mastery_no_attempts(self):
        """2025-12-18: Test mastery calculation with no attempts."""
        # 2025-12-18: No attempts yet
        self.progress.questions_attempted = 0
        
        # 2025-12-18: Calculate mastery
        mastery = self.progress.calculate_mastery()
        
        # 2025-12-18: Should be 0
        self.assertEqual(mastery, 0)


class TestDifficultyCalibration(TestCase):
    """
    2025-12-18: Test cases for DifficultyCalibration model.
    Tests adaptive difficulty adjustment.
    """
    
    def setUp(self):
        """2025-12-18: Set up test data."""
        # 2025-12-18: Create test user
        self.user = User.objects.create_user(
            username='calibrationstudent',
            email='calibration@example.com',
            password='testpass123'
        )
        
        # 2025-12-18: Create calibration record
        self.calibration = DifficultyCalibration.objects.create(
            student=self.user,
            subject='Math'
        )
    
    def test_calibration_defaults(self):
        """2025-12-18: Test that calibration is created with correct defaults."""
        # 2025-12-18: Verify defaults
        self.assertEqual(self.calibration.current_difficulty, 'core')
        self.assertEqual(self.calibration.rolling_accuracy, 0.5)
        self.assertEqual(len(self.calibration.recent_attempts), 0)
    
    def test_add_attempt_stores_data(self):
        """2025-12-18: Test that adding attempt stores data correctly."""
        # 2025-12-18: Add an attempt
        self.calibration.add_attempt(is_correct=True, time_seconds=30, retries=0)
        
        # 2025-12-18: Verify stored
        self.assertEqual(len(self.calibration.recent_attempts), 1)
        self.assertTrue(self.calibration.recent_attempts[0]['is_correct'])
    
    def test_add_attempt_trims_to_20(self):
        """2025-12-18: Test that only last 20 attempts are kept."""
        # 2025-12-18: Add 25 attempts
        for i in range(25):
            self.calibration.add_attempt(is_correct=True, time_seconds=30, retries=0)
        
        # 2025-12-18: Should only have 20
        self.assertEqual(len(self.calibration.recent_attempts), 20)
    
    def test_high_accuracy_increases_difficulty(self):
        """2025-12-18: Test that high accuracy and fast time increases difficulty."""
        # 2025-12-18: Start at core level
        self.calibration.current_difficulty = 'core'
        
        # 2025-12-18: Add 10 correct, fast attempts
        for _ in range(10):
            self.calibration.add_attempt(is_correct=True, time_seconds=30, retries=0)
        
        # 2025-12-18: Should increase to challenge
        self.assertEqual(self.calibration.current_difficulty, 'challenge')
    
    def test_low_accuracy_decreases_difficulty(self):
        """2025-12-18: Test that low accuracy decreases difficulty."""
        # 2025-12-18: Start at core level
        self.calibration.current_difficulty = 'core'
        
        # 2025-12-18: Add 10 incorrect attempts
        for _ in range(10):
            self.calibration.add_attempt(is_correct=False, time_seconds=60, retries=2)
        
        # 2025-12-18: Should decrease to support
        self.assertEqual(self.calibration.current_difficulty, 'support')
    
    def test_many_retries_decreases_difficulty(self):
        """2025-12-18: Test that many retries decreases difficulty."""
        # 2025-12-18: Start at core level (not challenge, to test single step decrease)
        self.calibration.current_difficulty = 'core'
        self.calibration.save()
        
        # 2025-12-18: Add attempts with many retries (even if eventually correct)
        for _ in range(10):
            self.calibration.add_attempt(is_correct=True, time_seconds=60, retries=3)
        
        # 2025-12-18: Should decrease to support due to high retries (avg > 2)
        self.assertEqual(self.calibration.current_difficulty, 'support')
    
    def test_support_cannot_decrease_further(self):
        """2025-12-18: Test that support level doesn't decrease further."""
        # 2025-12-18: Start at support level
        self.calibration.current_difficulty = 'support'
        
        # 2025-12-18: Add poor performance
        for _ in range(10):
            self.calibration.add_attempt(is_correct=False, time_seconds=120, retries=5)
        
        # 2025-12-18: Should stay at support
        self.assertEqual(self.calibration.current_difficulty, 'support')
    
    def test_challenge_cannot_increase_further(self):
        """2025-12-18: Test that challenge level doesn't increase further."""
        # 2025-12-18: Start at challenge level
        self.calibration.current_difficulty = 'challenge'
        
        # 2025-12-18: Add excellent performance
        for _ in range(10):
            self.calibration.add_attempt(is_correct=True, time_seconds=20, retries=0)
        
        # 2025-12-18: Should stay at challenge
        self.assertEqual(self.calibration.current_difficulty, 'challenge')
    
    def test_not_enough_data_no_change(self):
        """2025-12-18: Test that calibration doesn't change with insufficient data."""
        # 2025-12-18: Start at core
        self.calibration.current_difficulty = 'core'
        
        # 2025-12-18: Add only 3 attempts (need 5 minimum)
        for _ in range(3):
            self.calibration.add_attempt(is_correct=True, time_seconds=20, retries=0)
        
        # 2025-12-18: Should stay at core (not enough data)
        self.assertEqual(self.calibration.current_difficulty, 'core')
