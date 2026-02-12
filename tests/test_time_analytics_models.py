"""
Time-on-Task Analytics Models Test Suite

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Comprehensive test suite for time-on-task analytics models.
    Tests session tracking, engagement patterns, and focus time analysis.
    
Test Coverage:
    - LearningSession model creation and validation
    - Session duration tracking
    - Break/pause detection
    - Engagement pattern analysis
    - Focus time calculations
    - Session aggregation
    
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
    LearningSession,
    SessionActivity,
    EngagementMetric,
)


class LearningSessionModelTestCase(TestCase):
    """
    Test suite for LearningSession model.
    
    Purpose:
        Test learning session tracking with detailed time analytics.
        Sessions are continuous learning periods with start/end times.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.student = User.objects.create_user(
            username='student1',
            password='password123'
        )
        
        # Session data
        self.session_data = {
            'student': self.student,
            'started_at': timezone.now() - timedelta(minutes=30),
            'ended_at': timezone.now(),
            'subject': 'Mathematics',
            'grade_level': 5,
        }
    
    def test_TC_TIME_001_create_session_success(self):
        """
        TC-TIME-001: Test successful session creation.
        
        Expected: LearningSession created with all fields
        """
        # Act
        session = LearningSession.objects.create(**self.session_data)
        
        # Assert
        self.assertEqual(session.student, self.student)
        self.assertEqual(session.subject, 'Mathematics')
        self.assertEqual(session.grade_level, 5)
        self.assertIsNotNone(session.started_at)
        self.assertIsNotNone(session.ended_at)
        self.assertTrue(session.is_completed)
    
    def test_TC_TIME_002_session_string_representation(self):
        """
        TC-TIME-002: Test session __str__ method.
        
        Expected: Returns readable string
        """
        # Arrange
        session = LearningSession.objects.create(**self.session_data)
        
        # Act & Assert
        expected = f"{self.student.username} - Mathematics - {session.started_at}"
        self.assertEqual(str(session), expected)
    
    def test_TC_TIME_003_calculate_total_duration(self):
        """
        TC-TIME-003: Test total duration calculation.
        
        Expected: Calculates duration in seconds correctly
        """
        # Arrange & Act
        session = LearningSession.objects.create(**self.session_data)
        
        # Assert
        expected_duration = 30 * 60  # 30 minutes in seconds
        self.assertAlmostEqual(session.total_duration_seconds, expected_duration, delta=5)
    
    def test_TC_TIME_004_calculate_active_duration(self):
        """
        TC-TIME-004: Test active learning time calculation.
        
        Expected: Excludes break time from total duration
        """
        # Arrange
        session = LearningSession.objects.create(**self.session_data)
        
        # Simulate 5 minutes of break time
        session.break_duration_seconds = 300
        session.save()
        
        # Act
        active_time = session.active_duration_seconds
        
        # Assert
        expected_active = (30 * 60) - 300  # 25 minutes
        self.assertEqual(active_time, expected_active)
    
    def test_TC_TIME_005_engagement_percentage_calculation(self):
        """
        TC-TIME-005: Test engagement percentage.
        
        Expected: Calculates (active / total) * 100
        """
        # Arrange
        session = LearningSession.objects.create(**self.session_data)
        session.break_duration_seconds = 300  # 5 min break
        session.save()
        
        # Act
        engagement_pct = session.engagement_percentage()
        
        # Assert
        # 25 active minutes / 30 total minutes = 83.33%
        expected = (25 / 30) * 100
        self.assertAlmostEqual(engagement_pct, expected, places=1)
    
    def test_TC_TIME_006_focus_score_calculation(self):
        """
        TC-TIME-006: Test focus score calculation.
        
        Expected: Calculates focus based on continuous activity
        """
        # Arrange
        session = LearningSession.objects.create(**self.session_data)
        session.interaction_count = 50
        session.context_switches = 5
        session.save()
        
        # Act
        focus_score = session.focus_score()
        
        # Assert
        self.assertGreaterEqual(focus_score, 0)
        self.assertLessEqual(focus_score, 100)
    
    def test_TC_TIME_007_ongoing_session_detection(self):
        """
        TC-TIME-007: Test detection of ongoing sessions.
        
        Expected: Session without end time is ongoing
        """
        # Arrange
        self.session_data['ended_at'] = None
        
        # Act
        session = LearningSession.objects.create(**self.session_data)
        
        # Assert
        self.assertFalse(session.is_completed)
        self.assertIsNone(session.ended_at)
    
    def test_TC_TIME_008_session_auto_end_on_save(self):
        """
        TC-TIME-008: Test automatic duration calculation on save.
        
        Expected: Duration auto-calculated when ended_at is set
        """
        # Arrange
        self.session_data['ended_at'] = None
        session = LearningSession.objects.create(**self.session_data)
        
        # Act
        session.ended_at = timezone.now()
        session.save()
        
        # Assert
        self.assertIsNotNone(session.total_duration_seconds)
        self.assertGreater(session.total_duration_seconds, 0)
    
    def test_TC_TIME_009_multiple_sessions_same_student(self):
        """
        TC-TIME-009: Test creating multiple sessions for same student.
        
        Expected: Student can have multiple sessions
        """
        # Arrange & Act
        session1 = LearningSession.objects.create(**self.session_data)
        
        session2_data = self.session_data.copy()
        session2_data['started_at'] = timezone.now()
        session2_data['ended_at'] = timezone.now() + timedelta(minutes=20)
        session2 = LearningSession.objects.create(**session2_data)
        
        # Assert
        self.assertEqual(
            LearningSession.objects.filter(student=self.student).count(),
            2
        )


class SessionActivityModelTestCase(TestCase):
    """
    Test suite for SessionActivity model.
    
    Purpose:
        Test individual activities within a learning session.
        Tracks micro-level interactions for engagement analysis.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user and session
        self.student = User.objects.create_user(username='student1')
        
        self.session = LearningSession.objects.create(
            student=self.student,
            started_at=timezone.now() - timedelta(minutes=10),
            ended_at=timezone.now(),
            subject='Science',
            grade_level=5
        )
        
        # Activity data
        self.activity_data = {
            'session': self.session,
            'activity_type': 'question_answer',
            'started_at': timezone.now() - timedelta(minutes=5),
            'ended_at': timezone.now(),
            'was_successful': True,
        }
    
    def test_TC_TIME_011_create_activity_success(self):
        """
        TC-TIME-011: Test session activity creation.
        
        Expected: SessionActivity created successfully
        """
        # Act
        activity = SessionActivity.objects.create(**self.activity_data)
        
        # Assert
        self.assertEqual(activity.session, self.session)
        self.assertEqual(activity.activity_type, 'question_answer')
        self.assertTrue(activity.was_successful)
    
    def test_TC_TIME_012_activity_duration_calculation(self):
        """
        TC-TIME-012: Test activity duration calculation.
        
        Expected: Duration calculated in seconds
        """
        # Arrange & Act
        activity = SessionActivity.objects.create(**self.activity_data)
        
        # Assert
        expected_duration = 5 * 60  # 5 minutes
        self.assertAlmostEqual(activity.duration_seconds, expected_duration, delta=2)
    
    def test_TC_TIME_013_activity_cascade_delete(self):
        """
        TC-TIME-013: Test activities deleted with session.
        
        Expected: Cascade delete maintains referential integrity
        """
        # Arrange
        activity = SessionActivity.objects.create(**self.activity_data)
        
        # Act
        self.session.delete()
        
        # Assert
        self.assertFalse(
            SessionActivity.objects.filter(id=activity.id).exists()
        )
    
    def test_TC_TIME_014_multiple_activities_per_session(self):
        """
        TC-TIME-014: Test multiple activities in one session.
        
        Expected: Session can contain many activities
        """
        # Act
        activity1 = SessionActivity.objects.create(**self.activity_data)
        
        activity2_data = self.activity_data.copy()
        activity2_data['activity_type'] = 'video_watch'
        activity2 = SessionActivity.objects.create(**activity2_data)
        
        # Assert
        self.assertEqual(self.session.activities.count(), 2)
    
    def test_TC_TIME_015_activity_success_tracking(self):
        """
        TC-TIME-015: Test tracking activity success/failure.
        
        Expected: Can track if activity was successful
        """
        # Arrange
        self.activity_data['was_successful'] = False
        
        # Act
        activity = SessionActivity.objects.create(**self.activity_data)
        
        # Assert
        self.assertFalse(activity.was_successful)


class EngagementMetricModelTestCase(TestCase):
    """
    Test suite for EngagementMetric model.
    
    Purpose:
        Test engagement metrics calculated for sessions.
        Provides detailed analytics on student engagement patterns.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create user and session
        self.student = User.objects.create_user(username='student1')
        
        self.session = LearningSession.objects.create(
            student=self.student,
            started_at=timezone.now() - timedelta(minutes=30),
            ended_at=timezone.now(),
            subject='Mathematics',
            grade_level=5
        )
        
        # Metric data
        self.metric_data = {
            'session': self.session,
            'metric_type': 'attention_score',
            'value': Decimal('85.5'),
            'confidence': Decimal('92.0'),
        }
    
    def test_TC_TIME_021_create_metric_success(self):
        """
        TC-TIME-021: Test engagement metric creation.
        
        Expected: EngagementMetric created successfully
        """
        # Act
        metric = EngagementMetric.objects.create(**self.metric_data)
        
        # Assert
        self.assertEqual(metric.session, self.session)
        self.assertEqual(metric.metric_type, 'attention_score')
        self.assertEqual(metric.value, Decimal('85.5'))
    
    def test_TC_TIME_022_multiple_metrics_per_session(self):
        """
        TC-TIME-022: Test multiple metrics for one session.
        
        Expected: Session can have multiple engagement metrics
        """
        # Act
        metric1 = EngagementMetric.objects.create(**self.metric_data)
        
        metric2_data = self.metric_data.copy()
        metric2_data['metric_type'] = 'participation_rate'
        metric2_data['value'] = Decimal('90.0')
        metric2 = EngagementMetric.objects.create(**metric2_data)
        
        # Assert
        self.assertEqual(self.session.engagement_metrics.count(), 2)
    
    def test_TC_TIME_023_metric_confidence_score(self):
        """
        TC-TIME-023: Test metric confidence tracking.
        
        Expected: Tracks confidence in metric calculation
        """
        # Arrange & Act
        metric = EngagementMetric.objects.create(**self.metric_data)
        
        # Assert
        self.assertEqual(metric.confidence, Decimal('92.0'))
        self.assertGreaterEqual(metric.confidence, 0)
        self.assertLessEqual(metric.confidence, 100)
    
    def test_TC_TIME_024_metric_metadata_storage(self):
        """
        TC-TIME-024: Test storing metric metadata.
        
        Expected: Can store additional metric details in JSON
        """
        # Arrange
        self.metric_data['metadata'] = {
            'algorithm': 'ML_v2',
            'data_points': 150,
            'outliers_removed': 3
        }
        
        # Act
        metric = EngagementMetric.objects.create(**self.metric_data)
        
        # Assert
        self.assertEqual(metric.metadata['algorithm'], 'ML_v2')
        self.assertEqual(metric.metadata['data_points'], 150)


class TimeAnalyticsQueryTestCase(TestCase):
    """
    Test suite for time analytics query optimization.
    
    Purpose:
        Test query efficiency and aggregations for time analytics.
    """
    
    def setUp(self):
        """Set up test data."""
        # Create users
        self.student1 = User.objects.create_user(username='student1')
        self.student2 = User.objects.create_user(username='student2')
        
        # Create sessions
        # Student 1: 3 sessions
        for i in range(3):
            LearningSession.objects.create(
                student=self.student1,
                started_at=timezone.now() - timedelta(days=i, minutes=30),
                ended_at=timezone.now() - timedelta(days=i),
                subject='Mathematics',
                grade_level=5
            )
        
        # Student 2: 2 sessions
        for i in range(2):
            LearningSession.objects.create(
                student=self.student2,
                started_at=timezone.now() - timedelta(days=i, minutes=20),
                ended_at=timezone.now() - timedelta(days=i),
                subject='Science',
                grade_level=6
            )
    
    def test_TC_TIME_101_filter_by_student(self):
        """
        TC-TIME-101: Test filtering sessions by student.
        
        Expected: Returns only student's sessions
        """
        # Act
        sessions = LearningSession.objects.filter(student=self.student1)
        
        # Assert
        self.assertEqual(sessions.count(), 3)
        for session in sessions:
            self.assertEqual(session.student, self.student1)
    
    def test_TC_TIME_102_filter_by_date_range(self):
        """
        TC-TIME-102: Test filtering by date range.
        
        Expected: Returns sessions within date range
        """
        # Arrange
        start_date = timezone.now() - timedelta(days=1)
        
        # Act
        sessions = LearningSession.objects.filter(
            started_at__gte=start_date
        )
        
        # Assert
        self.assertGreater(sessions.count(), 0)
        for session in sessions:
            self.assertGreaterEqual(session.started_at, start_date)
    
    def test_TC_TIME_103_aggregate_total_time(self):
        """
        TC-TIME-103: Test aggregating total learning time.
        
        Expected: Calculates sum of all session durations
        """
        # Arrange
        from django.db.models import Sum
        
        # Act
        total_time = LearningSession.objects.filter(
            student=self.student1
        ).aggregate(
            total=Sum('total_duration_seconds')
        )
        
        # Assert
        self.assertIsNotNone(total_time['total'])
        self.assertGreater(total_time['total'], 0)
    
    def test_TC_TIME_104_filter_by_subject(self):
        """
        TC-TIME-104: Test filtering by subject.
        
        Expected: Returns sessions for specific subject
        """
        # Act
        math_sessions = LearningSession.objects.filter(subject='Mathematics')
        
        # Assert
        self.assertEqual(math_sessions.count(), 3)
        for session in math_sessions:
            self.assertEqual(session.subject, 'Mathematics')
    
    def test_TC_TIME_105_order_by_recent(self):
        """
        TC-TIME-105: Test ordering by most recent.
        
        Expected: Sessions ordered by start time descending
        """
        # Act
        sessions = LearningSession.objects.all().order_by('-started_at')
        
        # Assert
        self.assertGreater(sessions.count(), 0)
        previous_time = None
        for session in sessions:
            if previous_time:
                self.assertGreaterEqual(previous_time, session.started_at)
            previous_time = session.started_at
