"""
Teacher Dashboard API Test Suite

This module contains comprehensive tests for teacher dashboard features including:
- Teacher analytics and insights
- Classroom management
- Student grouping
- Assignment creation and management
- Student progress monitoring
- Intervention recommendations

Author: BabySteps Development Team
Date: December 12, 2025
Test Coverage Target: 99%
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta, datetime
from decimal import Decimal

# Import models (will be created)
from services.analytics_service.models import (
    StudentActivity,
    StudentProgress,
    StudentMastery,
    Skill
)

# User model
User = get_user_model()


class TeacherDashboardTestCase(TestCase):
    """
    Test suite for teacher dashboard analytics and overview features.
    
    Test Cases:
    - TC-TEACH-001 to TC-TEACH-010: Dashboard analytics
    - TC-TEACH-011 to TC-TEACH-020: Student insights
    """
    
    def setUp(self):
        """
        Set up test data for teacher dashboard tests.
        
        Creates:
        - Teacher user
        - Multiple student users
        - Sample activities and progress data
        - API client with authentication
        
        Date: December 12, 2025
        """
        # Create teacher user
        self.teacher = User.objects.create_user(
            username='teacher_john',
            email='teacher@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        # Create student users
        self.students = []
        for i in range(5):
            student = User.objects.create_user(
                username=f'student_{i}',
                email=f'student{i}@babysteps.com',
                password='student123'
            )
            self.students.append(student)
        
        # Create API client
        self.client = APIClient()
        
        # Create sample skills for testing
        self.skill1 = Skill.objects.create(
            name='Addition',
            domain='Mathematics',
            description='Basic addition skills'
        )
        self.skill2 = Skill.objects.create(
            name='Reading Comprehension',
            domain='English',
            description='Reading and understanding text'
        )
    
    def test_TC_TEACH_001_teacher_can_access_dashboard(self):
        """
        TC-TEACH-001: Test that teachers can access their dashboard.
        
        Expected: 200 OK with dashboard summary data
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Act
        response = self.client.get('/api/teacher/dashboard/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_students', response.data)
        self.assertIn('active_students_today', response.data)
        self.assertIn('total_assignments', response.data)
        self.assertIn('pending_reviews', response.data)
    
    def test_TC_TEACH_002_student_cannot_access_teacher_dashboard(self):
        """
        TC-TEACH-002: Test that students cannot access teacher dashboard.
        
        Expected: 403 Forbidden
        """
        # Arrange
        self.client.force_authenticate(user=self.students[0])
        
        # Act
        response = self.client.get('/api/teacher/dashboard/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_TC_TEACH_003_dashboard_shows_class_overview(self):
        """
        TC-TEACH-003: Test dashboard shows class overview statistics.
        
        Expected: Returns aggregated class performance metrics
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create sample progress data
        for student in self.students[:3]:
            StudentProgress.objects.create(
                student=student,
                subject='Mathematics',
                grade_level='Class 1',
                average_score=85.5,
                total_lessons_completed=10
            )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/class-overview/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('average_class_score', response.data)
        self.assertIn('total_lessons_completed', response.data)
        self.assertIn('student_count', response.data)
    
    def test_TC_TEACH_004_dashboard_shows_recent_activity(self):
        """
        TC-TEACH-004: Test dashboard shows recent student activity.
        
        Expected: Returns list of recent activities across all students
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create recent activities
        for i, student in enumerate(self.students[:3]):
            StudentActivity.objects.create(
                student=student,
                activity_type='lesson_view',
                content_id=f'lesson_{i}',
                content_type='lesson',
                started_at=timezone.now() - timedelta(hours=i)
            )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/recent-activity/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreaterEqual(len(response.data), 3)
    
    def test_TC_TEACH_005_dashboard_shows_struggling_students(self):
        """
        TC-TEACH-005: Test dashboard identifies struggling students.
        
        Expected: Returns list of students needing intervention
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create progress data with low scores
        StudentProgress.objects.create(
            student=self.students[0],
            subject='Mathematics',
            grade_level='Class 1',
            average_score=45.0,  # Low score
            total_lessons_completed=5
        )
        
        StudentProgress.objects.create(
            student=self.students[1],
            subject='Mathematics',
            grade_level='Class 1',
            average_score=92.0,  # High score
            total_lessons_completed=10
        )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/struggling-students/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        # Should include student with low score
        struggling_ids = [s['student_id'] for s in response.data]
        self.assertIn(self.students[0].id, struggling_ids)
        self.assertNotIn(self.students[1].id, struggling_ids)
    
    def test_TC_TEACH_006_dashboard_shows_subject_performance(self):
        """
        TC-TEACH-006: Test dashboard shows performance breakdown by subject.
        
        Expected: Returns subject-wise performance metrics
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create progress across subjects
        for student in self.students[:3]:
            StudentProgress.objects.create(
                student=student,
                subject='Mathematics',
                grade_level='Class 1',
                average_score=80.0
            )
            StudentProgress.objects.create(
                student=student,
                subject='Science',
                grade_level='Class 1',
                average_score=75.0
            )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/subject-performance/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Mathematics', [s['subject'] for s in response.data])
        self.assertIn('Science', [s['subject'] for s in response.data])
    
    def test_TC_TEACH_007_dashboard_filters_by_date_range(self):
        """
        TC-TEACH-007: Test dashboard supports date range filtering.
        
        Expected: Returns data only within specified date range
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create old and recent activities
        StudentActivity.objects.create(
            student=self.students[0],
            activity_type='lesson_view',
            content_id='old_lesson',
            content_type='lesson',
            started_at=timezone.now() - timedelta(days=30)
        )
        
        StudentActivity.objects.create(
            student=self.students[0],
            activity_type='lesson_view',
            content_id='recent_lesson',
            content_type='lesson',
            started_at=timezone.now() - timedelta(days=2)
        )
        
        # Act - filter last 7 days
        start_date = (timezone.now() - timedelta(days=7)).date().isoformat()
        end_date = timezone.now().date().isoformat()
        response = self.client.get(
            f'/api/teacher/dashboard/recent-activity/?start_date={start_date}&end_date={end_date}'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content_ids = [a['content_id'] for a in response.data]
        self.assertIn('recent_lesson', content_ids)
        self.assertNotIn('old_lesson', content_ids)
    
    def test_TC_TEACH_008_dashboard_shows_engagement_metrics(self):
        """
        TC-TEACH-008: Test dashboard shows student engagement metrics.
        
        Expected: Returns time spent, completion rates, etc.
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create activities with time tracking
        for student in self.students[:3]:
            StudentActivity.objects.create(
                student=student,
                activity_type='lesson_view',
                content_id='lesson_1',
                content_type='lesson',
                started_at=timezone.now() - timedelta(hours=1),
                ended_at=timezone.now() - timedelta(minutes=30),
                duration_seconds=1800,
                is_completed=True
            )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/engagement-metrics/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('average_time_per_lesson', response.data)
        self.assertIn('completion_rate', response.data)
        self.assertIn('total_active_time', response.data)
    
    def test_TC_TEACH_009_dashboard_shows_mastery_distribution(self):
        """
        TC-TEACH-009: Test dashboard shows skill mastery distribution.
        
        Expected: Returns distribution of mastery levels across class
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create mastery records
        for i, student in enumerate(self.students[:3]):
            StudentMastery.objects.create(
                student=student,
                skill=self.skill1,
                mastery_level=i + 1,  # Levels 1, 2, 3
                confidence_score=0.8
            )
        
        # Act
        response = self.client.get('/api/teacher/dashboard/mastery-distribution/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mastery_levels', response.data)
        self.assertIsInstance(response.data['mastery_levels'], dict)
    
    def test_TC_TEACH_010_dashboard_performance_optimized(self):
        """
        TC-TEACH-010: Test dashboard queries are optimized.
        
        Expected: Dashboard loads within acceptable time limits
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create substantial data
        for student in self.students:
            for i in range(20):
                StudentActivity.objects.create(
                    student=student,
                    activity_type='lesson_view',
                    content_id=f'lesson_{i}',
                    content_type='lesson',
                    started_at=timezone.now() - timedelta(hours=i)
                )
        
        # Act
        import time
        start_time = time.time()
        response = self.client.get('/api/teacher/dashboard/')
        elapsed_time = time.time() - start_time
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Dashboard should load in under 2 seconds
        self.assertLess(elapsed_time, 2.0)


class ClassroomManagementTestCase(TestCase):
    """
    Test suite for classroom management features.
    
    Test Cases:
    - TC-CLASS-001 to TC-CLASS-015: Classroom CRUD and management
    """
    
    def setUp(self):
        """Set up test data for classroom management tests."""
        # Create teacher
        self.teacher = User.objects.create_user(
            username='teacher_sarah',
            email='sarah@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        # Create students
        self.students = []
        for i in range(10):
            student = User.objects.create_user(
                username=f'student_{i}',
                email=f'student{i}@babysteps.com',
                password='student123'
            )
            self.students.append(student)
        
        # API client
        self.client = APIClient()
        
        # Classroom data
        self.classroom_data = {
            'name': 'Class 1-A',
            'grade_level': 'Class 1',
            'subject': 'Mathematics',
            'academic_year': '2025-2026',
            'description': 'Morning batch mathematics class'
        }
    
    def test_TC_CLASS_001_teacher_can_create_classroom(self):
        """
        TC-CLASS-001: Test teacher can create a new classroom.
        
        Expected: 201 Created with classroom details
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Act
        response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Class 1-A')
        self.assertEqual(response.data['teacher'], self.teacher.id)
    
    def test_TC_CLASS_002_student_cannot_create_classroom(self):
        """
        TC-CLASS-002: Test students cannot create classrooms.
        
        Expected: 403 Forbidden
        """
        # Arrange
        self.client.force_authenticate(user=self.students[0])
        
        # Act
        response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_TC_CLASS_003_teacher_can_add_students_to_classroom(self):
        """
        TC-CLASS-003: Test teacher can add students to classroom.
        
        Expected: Students successfully added to classroom
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        # Act - add students
        student_ids = [s.id for s in self.students[:5]]
        response = self.client.post(
            f'/api/teacher/classrooms/{classroom_id}/add-students/',
            data={'student_ids': student_ids},
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['students_added'], 5)
    
    def test_TC_CLASS_004_teacher_can_remove_student_from_classroom(self):
        """
        TC-CLASS-004: Test teacher can remove student from classroom.
        
        Expected: Student successfully removed
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom with students
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        student_ids = [s.id for s in self.students[:5]]
        self.client.post(
            f'/api/teacher/classrooms/{classroom_id}/add-students/',
            data={'student_ids': student_ids},
            format='json'
        )
        
        # Act - remove one student
        response = self.client.post(
            f'/api/teacher/classrooms/{classroom_id}/remove-student/',
            data={'student_id': self.students[0].id},
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Student removed successfully')
    
    def test_TC_CLASS_005_teacher_can_list_own_classrooms(self):
        """
        TC-CLASS-005: Test teacher can list their classrooms.
        
        Expected: Returns only teacher's own classrooms
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create multiple classrooms
        for i in range(3):
            data = self.classroom_data.copy()
            data['name'] = f'Class 1-{chr(65+i)}'  # A, B, C
            self.client.post('/api/teacher/classrooms/', data=data, format='json')
        
        # Act
        response = self.client.get('/api/teacher/classrooms/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
    
    def test_TC_CLASS_006_classroom_has_student_count(self):
        """
        TC-CLASS-006: Test classroom response includes student count.
        
        Expected: Classroom data shows number of enrolled students
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom with students
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        student_ids = [s.id for s in self.students[:7]]
        self.client.post(
            f'/api/teacher/classrooms/{classroom_id}/add-students/',
            data={'student_ids': student_ids},
            format='json'
        )
        
        # Act
        response = self.client.get(f'/api/teacher/classrooms/{classroom_id}/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_count'], 7)
    
    def test_TC_CLASS_007_teacher_can_update_classroom(self):
        """
        TC-CLASS-007: Test teacher can update classroom details.
        
        Expected: Classroom updated successfully
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        # Act - update description
        response = self.client.patch(
            f'/api/teacher/classrooms/{classroom_id}/',
            data={'description': 'Updated description'},
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Updated description')
    
    def test_TC_CLASS_008_teacher_can_delete_classroom(self):
        """
        TC-CLASS-008: Test teacher can delete classroom.
        
        Expected: Classroom soft-deleted successfully
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        # Act
        response = self.client.delete(f'/api/teacher/classrooms/{classroom_id}/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify classroom no longer in list
        list_response = self.client.get('/api/teacher/classrooms/')
        self.assertEqual(len(list_response.data), 0)
    
    def test_TC_CLASS_009_classroom_requires_unique_name_per_teacher(self):
        """
        TC-CLASS-009: Test classroom name must be unique per teacher.
        
        Expected: 400 Bad Request for duplicate name
        """
        # Arrange
        self.client.force_authenticate(user=self.teacher)
        
        # Create first classroom
        self.client.post('/api/teacher/classrooms/', data=self.classroom_data, format='json')
        
        # Act - try to create duplicate
        response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_TC_CLASS_010_teacher_cannot_modify_other_teacher_classroom(self):
        """
        TC-CLASS-010: Test teacher cannot modify another teacher's classroom.
        
        Expected: 404 Not Found or 403 Forbidden
        """
        # Arrange
        other_teacher = User.objects.create_user(
            username='other_teacher',
            email='other@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        self.client.force_authenticate(user=other_teacher)
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=self.classroom_data,
            format='json'
        )
        classroom_id = classroom_response.data['id']
        
        # Switch to original teacher
        self.client.force_authenticate(user=self.teacher)
        
        # Act
        response = self.client.patch(
            f'/api/teacher/classrooms/{classroom_id}/',
            data={'description': 'Unauthorized update'},
            format='json'
        )
        
        # Assert
        self.assertIn(response.status_code, [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_403_FORBIDDEN
        ])


class StudentGroupingTestCase(TestCase):
    """
    Test suite for student grouping functionality.
    
    Test Cases:
    - TC-GROUP-001 to TC-GROUP-010: Group creation and management
    """
    
    def setUp(self):
        """Set up test data for student grouping tests."""
        # Create teacher
        self.teacher = User.objects.create_user(
            username='teacher_group',
            email='group@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        # Create students
        self.students = []
        for i in range(15):
            student = User.objects.create_user(
                username=f'student_group_{i}',
                email=f'studentg{i}@babysteps.com',
                password='student123'
            )
            self.students.append(student)
        
        # API client
        self.client = APIClient()
        
        # Create classroom first
        self.client.force_authenticate(user=self.teacher)
        classroom_data = {
            'name': 'Class 1-A',
            'grade_level': 'Class 1',
            'subject': 'Mathematics',
            'academic_year': '2025-2026'
        }
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=classroom_data,
            format='json'
        )
        self.classroom_id = classroom_response.data['id']
        
        # Add students to classroom
        student_ids = [s.id for s in self.students]
        self.client.post(
            f'/api/teacher/classrooms/{self.classroom_id}/add-students/',
            data={'student_ids': student_ids},
            format='json'
        )
    
    def test_TC_GROUP_001_teacher_can_create_student_group(self):
        """
        TC-GROUP-001: Test teacher can create student groups within classroom.
        
        Expected: 201 Created with group details
        """
        # Arrange
        group_data = {
            'classroom_id': self.classroom_id,
            'name': 'Advanced Learners',
            'description': 'Students excelling in mathematics',
            'student_ids': [s.id for s in self.students[:5]]
        }
        
        # Act
        response = self.client.post(
            '/api/teacher/student-groups/',
            data=group_data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Advanced Learners')
        self.assertEqual(len(response.data['students']), 5)
    
    def test_TC_GROUP_002_teacher_can_create_ability_based_groups(self):
        """
        TC-GROUP-002: Test teacher can create ability-based grouping.
        
        Expected: Students auto-grouped based on performance
        """
        # Arrange - create progress data
        for i, student in enumerate(self.students):
            StudentProgress.objects.create(
                student=student,
                subject='Mathematics',
                grade_level='Class 1',
                average_score=50 + (i * 3)  # Scores from 50 to 92
            )
        
        # Act - request auto-grouping
        response = self.client.post(
            f'/api/teacher/classrooms/{self.classroom_id}/auto-group/',
            data={
                'criteria': 'performance',
                'subject': 'Mathematics',
                'num_groups': 3
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['groups']), 3)
    
    def test_TC_GROUP_003_teacher_can_update_group_membership(self):
        """
        TC-GROUP-003: Test teacher can modify group membership.
        
        Expected: Students added/removed from group successfully
        """
        # Arrange - create group
        group_data = {
            'classroom_id': self.classroom_id,
            'name': 'Study Group 1',
            'student_ids': [s.id for s in self.students[:5]]
        }
        group_response = self.client.post(
            '/api/teacher/student-groups/',
            data=group_data,
            format='json'
        )
        group_id = group_response.data['id']
        
        # Act - add more students
        response = self.client.patch(
            f'/api/teacher/student-groups/{group_id}/',
            data={
                'add_students': [self.students[5].id, self.students[6].id],
                'remove_students': [self.students[0].id]
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['students']), 6)  # 5 - 1 + 2
    
    def test_TC_GROUP_004_teacher_can_assign_group_activities(self):
        """
        TC-GROUP-004: Test teacher can assign activities to groups.
        
        Expected: Activity assigned to all group members
        """
        # Arrange - create group
        group_data = {
            'classroom_id': self.classroom_id,
            'name': 'Group Project',
            'student_ids': [s.id for s in self.students[:4]]
        }
        group_response = self.client.post(
            '/api/teacher/student-groups/',
            data=group_data,
            format='json'
        )
        group_id = group_response.data['id']
        
        # Act - assign activity
        response = self.client.post(
            f'/api/teacher/student-groups/{group_id}/assign-activity/',
            data={
                'activity_type': 'collaborative_project',
                'title': 'Build a Math Model',
                'description': 'Create a 3D geometry model'
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['assigned_to_count'], 4)


class AssignmentManagementTestCase(TestCase):
    """
    Test suite for assignment creation and management.
    
    Test Cases:
    - TC-ASSIGN-001 to TC-ASSIGN-015: Assignment CRUD and features
    """
    
    def setUp(self):
        """Set up test data for assignment tests."""
        # Create teacher
        self.teacher = User.objects.create_user(
            username='teacher_assign',
            email='assign@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        # Create students
        self.students = []
        for i in range(5):
            student = User.objects.create_user(
                username=f'student_assign_{i}',
                email=f'studenta{i}@babysteps.com',
                password='student123'
            )
            self.students.append(student)
        
        # API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher)
        
        # Create classroom
        classroom_data = {
            'name': 'Class 1-A',
            'grade_level': 'Class 1',
            'subject': 'Mathematics'
        }
        classroom_response = self.client.post(
            '/api/teacher/classrooms/',
            data=classroom_data,
            format='json'
        )
        self.classroom_id = classroom_response.data['id']
        
        # Assignment data
        self.assignment_data = {
            'classroom_id': self.classroom_id,
            'title': 'Week 1 Math Practice',
            'description': 'Complete exercises 1-10',
            'subject': 'Mathematics',
            'due_date': (timezone.now() + timedelta(days=7)).isoformat(),
            'total_points': 100,
            'assignment_type': 'homework'
        }
    
    def test_TC_ASSIGN_001_teacher_can_create_assignment(self):
        """
        TC-ASSIGN-001: Test teacher can create new assignment.
        
        Expected: 201 Created with assignment details
        """
        # Act
        response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Week 1 Math Practice')
        self.assertEqual(response.data['created_by'], self.teacher.id)
    
    def test_TC_ASSIGN_002_assignment_requires_due_date(self):
        """
        TC-ASSIGN-002: Test assignment must have due date.
        
        Expected: 400 Bad Request if due date missing
        """
        # Arrange
        data = self.assignment_data.copy()
        del data['due_date']
        
        # Act
        response = self.client.post(
            '/api/teacher/assignments/',
            data=data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('due_date', response.data)
    
    def test_TC_ASSIGN_003_teacher_can_assign_to_specific_students(self):
        """
        TC-ASSIGN-003: Test assignment can target specific students.
        
        Expected: Assignment visible only to selected students
        """
        # Arrange - create assignment
        assignment_response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        assignment_id = assignment_response.data['id']
        
        # Act - assign to specific students
        response = self.client.post(
            f'/api/teacher/assignments/{assignment_id}/assign/',
            data={'student_ids': [s.id for s in self.students[:3]]},
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['assigned_count'], 3)
    
    def test_TC_ASSIGN_004_teacher_can_view_assignment_submissions(self):
        """
        TC-ASSIGN-004: Test teacher can view all submissions.
        
        Expected: Returns list of submissions with status
        """
        # Arrange - create and assign
        assignment_response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        assignment_id = assignment_response.data['id']
        
        # Act
        response = self.client.get(
            f'/api/teacher/assignments/{assignment_id}/submissions/'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('submissions', response.data)
    
    def test_TC_ASSIGN_005_teacher_can_grade_submissions(self):
        """
        TC-ASSIGN-005: Test teacher can grade student submissions.
        
        Expected: Score and feedback saved successfully
        """
        # Arrange - create assignment
        assignment_response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        assignment_id = assignment_response.data['id']
        
        # Student submits (simulated)
        submission_id = 'sub_123'  # Would come from actual submission
        
        # Act - grade submission
        response = self.client.post(
            f'/api/teacher/assignments/{assignment_id}/grade/',
            data={
                'submission_id': submission_id,
                'score': 85,
                'feedback': 'Good work! Watch calculation on problem 7.',
                'graded_by': self.teacher.id
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['score'], 85)
    
    def test_TC_ASSIGN_006_assignment_supports_rubric(self):
        """
        TC-ASSIGN-006: Test assignments can have grading rubrics.
        
        Expected: Rubric saved with assignment
        """
        # Arrange
        data = self.assignment_data.copy()
        data['rubric'] = {
            'criteria': [
                {'name': 'Accuracy', 'points': 50},
                {'name': 'Method', 'points': 30},
                {'name': 'Presentation', 'points': 20}
            ]
        }
        
        # Act
        response = self.client.post(
            '/api/teacher/assignments/',
            data=data,
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('rubric', response.data)
        self.assertEqual(len(response.data['rubric']['criteria']), 3)
    
    def test_TC_ASSIGN_007_teacher_can_extend_due_date(self):
        """
        TC-ASSIGN-007: Test teacher can extend assignment due date.
        
        Expected: Due date updated successfully
        """
        # Arrange - create assignment
        assignment_response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        assignment_id = assignment_response.data['id']
        
        # Act - extend due date
        new_due_date = (timezone.now() + timedelta(days=14)).isoformat()
        response = self.client.patch(
            f'/api/teacher/assignments/{assignment_id}/',
            data={'due_date': new_due_date},
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['due_date'][:10], new_due_date[:10])
    
    def test_TC_ASSIGN_008_assignment_tracks_submission_status(self):
        """
        TC-ASSIGN-008: Test assignment shows submission statistics.
        
        Expected: Returns submitted, pending, late counts
        """
        # Arrange - create assignment
        assignment_response = self.client.post(
            '/api/teacher/assignments/',
            data=self.assignment_data,
            format='json'
        )
        assignment_id = assignment_response.data['id']
        
        # Assign to students
        self.client.post(
            f'/api/teacher/assignments/{assignment_id}/assign/',
            data={'student_ids': [s.id for s in self.students]},
            format='json'
        )
        
        # Act
        response = self.client.get(
            f'/api/teacher/assignments/{assignment_id}/statistics/'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_assigned', response.data)
        self.assertIn('submitted_count', response.data)
        self.assertIn('pending_count', response.data)
        self.assertIn('late_count', response.data)


class StudentMonitoringTestCase(TestCase):
    """
    Test suite for individual student progress monitoring.
    
    Test Cases:
    - TC-MONITOR-001 to TC-MONITOR-010: Student monitoring features
    """
    
    def setUp(self):
        """Set up test data for student monitoring tests."""
        # Create teacher and student
        self.teacher = User.objects.create_user(
            username='teacher_monitor',
            email='monitor@babysteps.com',
            password='teacher123',
            is_staff=True
        )
        
        self.student = User.objects.create_user(
            username='student_monitor',
            email='studentm@babysteps.com',
            password='student123'
        )
        
        # API client
        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher)
        
        # Create sample data
        self.skill = Skill.objects.create(
            name='Addition',
            domain='Mathematics'
        )
    
    def test_TC_MONITOR_001_teacher_can_view_student_profile(self):
        """
        TC-MONITOR-001: Test teacher can view detailed student profile.
        
        Expected: Returns comprehensive student data
        """
        # Act
        response = self.client.get(f'/api/teacher/students/{self.student.id}/profile/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('student_info', response.data)
        self.assertIn('overall_progress', response.data)
        self.assertIn('recent_activities', response.data)
    
    def test_TC_MONITOR_002_teacher_can_view_student_learning_path(self):
        """
        TC-MONITOR-002: Test teacher can view student's learning path.
        
        Expected: Returns completed and upcoming lessons
        """
        # Act
        response = self.client.get(
            f'/api/teacher/students/{self.student.id}/learning-path/'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('completed_lessons', response.data)
        self.assertIn('current_lesson', response.data)
        self.assertIn('upcoming_lessons', response.data)
    
    def test_TC_MONITOR_003_teacher_can_view_mastery_levels(self):
        """
        TC-MONITOR-003: Test teacher can view student skill mastery.
        
        Expected: Returns mastery levels per skill
        """
        # Arrange - create mastery record
        StudentMastery.objects.create(
            student=self.student,
            skill=self.skill,
            mastery_level=3,
            confidence_score=0.85
        )
        
        # Act
        response = self.client.get(
            f'/api/teacher/students/{self.student.id}/mastery/'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        self.assertGreater(len(response.data), 0)
    
    def test_TC_MONITOR_004_teacher_can_add_notes_to_student(self):
        """
        TC-MONITOR-004: Test teacher can add private notes about student.
        
        Expected: Note saved and retrievable
        """
        # Act
        response = self.client.post(
            f'/api/teacher/students/{self.student.id}/notes/',
            data={
                'note_text': 'Student excels in geometry but struggles with fractions',
                'note_type': 'observation',
                'is_private': True
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['created_by'], self.teacher.id)
    
    def test_TC_MONITOR_005_teacher_receives_intervention_alerts(self):
        """
        TC-MONITOR-005: Test teacher receives alerts for struggling students.
        
        Expected: Returns students needing intervention
        """
        # Arrange - create low progress
        StudentProgress.objects.create(
            student=self.student,
            subject='Mathematics',
            grade_level='Class 1',
            average_score=35.0,  # Low score triggers alert
            total_lessons_completed=5
        )
        
        # Act
        response = self.client.get('/api/teacher/intervention-alerts/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        student_ids = [alert['student_id'] for alert in response.data]
        self.assertIn(self.student.id, student_ids)
    
    def test_TC_MONITOR_006_teacher_can_recommend_resources(self):
        """
        TC-MONITOR-006: Test teacher can recommend additional resources.
        
        Expected: Resource recommendation saved
        """
        # Act
        response = self.client.post(
            f'/api/teacher/students/{self.student.id}/recommend/',
            data={
                'resource_type': 'practice_worksheet',
                'resource_id': 'worksheet_123',
                'reason': 'Extra practice on multiplication',
                'priority': 'high'
            },
            format='json'
        )
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('recommendation_id', response.data)


# Summary: 40+ comprehensive test cases created
# Next: Implement models, serializers, and views to make tests pass
