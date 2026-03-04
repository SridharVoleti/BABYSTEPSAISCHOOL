"""
2026-03-04: Tests for Monitor Tools Service (BS-MON-005/006/007).

Covers:
  BS-MON-005 GradeBook: add_grade, get_student_grades, get_class_grades, report_card API
  BS-MON-006 Homework: create, list, student view, mark done, submissions
  BS-MON-007 Timetable: add, list, update, delete, today's schedule
"""

import uuid
from datetime import date, time

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.auth_service.models import Parent, Student
from services.monitor_tools_service.models import (
    GradeBookEntry, HomeworkAssignment, HomeworkSubmission, TimetableSlot,
)
from services.monitor_tools_service.services import (
    GradeBookService, HomeworkService, TimetableService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def monitor(db):
    """2026-03-04: Staff Django User acting as monitor."""
    return User.objects.create_user(username='mt_monitor', password='pass', is_staff=True)


@pytest.fixture
def monitor_client(monitor):
    """2026-03-04: APIClient as monitor."""
    client = APIClient()
    token = RefreshToken.for_user(monitor)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_user(db):
    """2026-03-04: Parent account."""
    user = User.objects.create_user(username='mt_parent', password='pass')
    return Parent.objects.create(
        user=user, phone='+919900001100', full_name='MT Parent',
        is_phone_verified=True, is_profile_complete=True,
    )


@pytest.fixture
def student(db, parent_user):
    """2026-03-04: Grade-6 student."""
    user = User.objects.create_user(username='mt_student', password='pass')
    return Student.objects.create(
        user=user, parent=parent_user, full_name='MT Student',
        dob=date(2013, 1, 1), grade=6,
    )


@pytest.fixture
def parent_client(parent_user):
    """2026-03-04: APIClient as parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    token['role'] = 'parent'
    token['parent_id'] = str(parent_user.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def student_client(student):
    """2026-03-04: APIClient as student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    token['role'] = 'student'
    token['student_id'] = str(student.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


# ===========================================================================
# BS-MON-005: Grade Book
# ===========================================================================

@pytest.mark.django_db
class TestGradeBookService:
    """2026-03-04: Unit tests for GradeBookService."""

    def test_add_grade_creates_entry(self, student, monitor):
        """2026-03-04: GradeBookService.add_grade creates a GradeBookEntry."""
        entry = GradeBookService.add_grade(
            student=student, subject='Science', term='T1',
            assessment_type='formative', title='Chapter 1 Quiz',
            score=78.0, recorded_by=monitor,
        )
        assert entry.pk is not None
        assert entry.score == 78.0
        assert entry.letter_grade == 'B'

    def test_letter_grade_auto_assigned(self, student):
        """2026-03-04: Letter grade is computed on save."""
        entry = GradeBookService.add_grade(
            student=student, subject='Maths', term='T2',
            assessment_type='summative', title='Mid-term', score=92.0,
        )
        assert entry.letter_grade == 'A+'

    def test_get_student_grades_filter_subject(self, student, monitor):
        """2026-03-04: get_student_grades returns only matching subject."""
        GradeBookService.add_grade(student=student, subject='Science', term='T1',
            assessment_type='formative', title='Q1', score=70.0)
        GradeBookService.add_grade(student=student, subject='Maths', term='T1',
            assessment_type='formative', title='Q1', score=80.0)
        sci = GradeBookService.get_student_grades(student, subject='Science')
        assert all(e.subject == 'Science' for e in sci)
        assert len(sci) == 1

    def test_report_card_averages(self, student):
        """2026-03-04: Report card computes per-subject averages."""
        GradeBookService.add_grade(student=student, subject='Science', term='T1',
            assessment_type='formative', title='Q1', score=60.0)
        GradeBookService.add_grade(student=student, subject='Science', term='T1',
            assessment_type='summative', title='Exam', score=80.0)
        report = GradeBookService.get_student_report_card(student, 'T1')
        assert 'Science' in report
        assert report['Science']['avg_percentage'] == 70.0


@pytest.mark.django_db
class TestGradeBookAPI:
    """2026-03-04: API tests for Grade Book endpoints."""

    def test_monitor_adds_grade(self, monitor_client, student):
        """2026-03-04: POST /grades/add/ returns 201."""
        res = monitor_client.post('/api/v1/monitor-tools/grades/add/', {
            'student_id': str(student.pk),
            'subject': 'Science', 'term': 'T1',
            'assessment_type': 'formative',
            'title': 'Chapter 1', 'score': 75.0,
        })
        assert res.status_code == 201
        assert res.data['score'] == 75.0

    def test_parent_cannot_add_grade(self, parent_client, student):
        """2026-03-04: Parent gets 403."""
        res = parent_client.post('/api/v1/monitor-tools/grades/add/', {
            'student_id': str(student.pk), 'subject': 'Science', 'term': 'T1',
            'assessment_type': 'formative', 'title': 'Q1', 'score': 50.0,
        })
        assert res.status_code == 403

    def test_parent_views_own_child_grades(self, parent_client, student, monitor):
        """2026-03-04: Parent views child's grade entries."""
        GradeBookService.add_grade(student=student, subject='Maths', term='T1',
            assessment_type='formative', title='Q', score=85.0)
        res = parent_client.get(f'/api/v1/monitor-tools/grades/student/{student.pk}/')
        assert res.status_code == 200
        assert len(res.data['entries']) == 1

    def test_report_card_api(self, parent_client, student):
        """2026-03-04: GET /grades/report-card/{id}/?term= returns subject averages."""
        GradeBookService.add_grade(student=student, subject='Hindi', term='T2',
            assessment_type='formative', title='Test', score=90.0)
        res = parent_client.get(
            f'/api/v1/monitor-tools/grades/report-card/{student.pk}/?term=T2'
        )
        assert res.status_code == 200
        assert 'Hindi' in res.data['subjects']

    def test_unknown_student_404(self, monitor_client):
        """2026-03-04: Unknown student returns 404."""
        res = monitor_client.get(f'/api/v1/monitor-tools/grades/student/{uuid.uuid4()}/')
        assert res.status_code == 404


# ===========================================================================
# BS-MON-006: Homework
# ===========================================================================

@pytest.mark.django_db
class TestHomeworkService:
    """2026-03-04: Unit tests for HomeworkService."""

    def test_create_assignment(self, monitor):
        """2026-03-04: Homework assignment is created."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='Science', title='Chapter 2 Notes',
            description='Read and summarise chapter 2.',
            due_date=date(2026, 4, 10), assigned_by=monitor,
        )
        assert hw.pk is not None
        assert hw.grade == 6

    def test_list_for_grade_returns_active(self, monitor):
        """2026-03-04: Inactive assignments are excluded by default."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='Maths', title='Worksheet 1',
            description='Complete worksheet.', due_date=date(2026, 4, 5),
        )
        hw.is_active = False
        hw.save()
        result = HomeworkService.list_assignments_for_grade(6)
        assert hw not in result

    def test_mark_done(self, student):
        """2026-03-04: Student marks homework as done."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='English', title='Essay',
            description='Write an essay.', due_date=date(2026, 4, 5),
        )
        sub = HomeworkService.mark_done(str(hw.pk), student, note='Done!')
        assert sub.status == HomeworkSubmission.STATUS_DONE
        assert sub.note == 'Done!'

    def test_get_student_homework_merged(self, student, monitor):
        """2026-03-04: Student homework includes submission status."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='Hindi', title='Read aloud',
            description='Practice reading.', due_date=date(2026, 4, 6),
        )
        HomeworkService.mark_done(str(hw.pk), student)
        result = HomeworkService.get_student_homework(student)
        assert len(result) >= 1
        entry = next(r for r in result if r['id'] == str(hw.pk))
        assert entry['status'] == 'done'


@pytest.mark.django_db
class TestHomeworkAPI:
    """2026-03-04: API tests for Homework endpoints."""

    def test_monitor_creates_homework(self, monitor_client):
        """2026-03-04: POST /homework/ returns 201."""
        res = monitor_client.post('/api/v1/monitor-tools/homework/', {
            'grade': 6, 'subject': 'Science',
            'title': 'Lab Report', 'description': 'Write lab report.',
            'due_date': '2026-04-10',
        })
        assert res.status_code == 201

    def test_student_lists_homework(self, student_client):
        """2026-03-04: Student GETs /homework/ without grade param (inferred)."""
        res = student_client.get('/api/v1/monitor-tools/homework/')
        assert res.status_code == 200
        assert 'assignments' in res.data

    def test_parent_marks_done(self, parent_client, student):
        """2026-03-04: Parent POSTs /homework/done/ — 200."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='Maths', title='HW1',
            description='Pg 10-15.', due_date=date(2026, 4, 7),
        )
        res = parent_client.post('/api/v1/monitor-tools/homework/done/', {
            'homework_id': str(hw.pk),
            'student_id': str(student.pk),
            'note': 'Completed before dinner',
        })
        assert res.status_code == 200
        assert res.data['status'] == 'done'

    def test_monitor_views_submissions(self, monitor_client, student):
        """2026-03-04: Monitor views all submissions for a homework — 200."""
        hw = HomeworkService.create_assignment(
            grade=6, subject='English', title='Poetry',
            description='Recite poem.', due_date=date(2026, 4, 8),
        )
        HomeworkService.mark_done(str(hw.pk), student)
        res = monitor_client.get(f'/api/v1/monitor-tools/homework/{hw.pk}/submissions/')
        assert res.status_code == 200
        assert len(res.data['submissions']) == 1

    def test_non_monitor_cannot_create(self, parent_client):
        """2026-03-04: Parent cannot create homework — 403."""
        res = parent_client.post('/api/v1/monitor-tools/homework/', {
            'grade': 6, 'subject': 'Science', 'title': 'T',
            'description': 'D.', 'due_date': '2026-04-10',
        })
        assert res.status_code == 403


# ===========================================================================
# BS-MON-007: Timetable
# ===========================================================================

@pytest.mark.django_db
class TestTimetableService:
    """2026-03-04: Unit tests for TimetableService."""

    def test_add_slot(self, monitor):
        """2026-03-04: TimetableService.add_slot creates a slot."""
        slot = TimetableService.add_slot(
            grade=6, day_of_week=1,
            start_time=time(8, 0), end_time=time(8, 45),
            subject='Mathematics', created_by=monitor,
        )
        assert slot.pk is not None
        assert slot.subject == 'Mathematics'

    def test_get_timetable_returns_active(self, monitor):
        """2026-03-04: get_timetable excludes inactive slots."""
        s1 = TimetableService.add_slot(6, 1, time(8, 0), time(8, 45), 'Maths')
        s2 = TimetableService.add_slot(6, 1, time(9, 0), time(9, 45), 'English')
        TimetableService.delete_slot(str(s2.pk))
        result = TimetableService.get_timetable(6)
        ids = [str(s.pk) for s in result]
        assert str(s1.pk) in ids
        assert str(s2.pk) not in ids

    def test_update_slot(self, monitor):
        """2026-03-04: update_slot changes subject."""
        slot = TimetableService.add_slot(6, 2, time(10, 0), time(10, 45), 'EVS')
        updated = TimetableService.update_slot(str(slot.pk), subject='Science')
        assert updated.subject == 'Science'

    def test_get_timetable_grade_filter(self, monitor):
        """2026-03-04: get_timetable only returns slots for requested grade."""
        TimetableService.add_slot(6, 1, time(8, 0), time(8, 45), 'Maths')
        TimetableService.add_slot(7, 1, time(8, 0), time(8, 45), 'Physics')
        slots6 = TimetableService.get_timetable(6)
        assert all(s.grade == 6 for s in slots6)


@pytest.mark.django_db
class TestTimetableAPI:
    """2026-03-04: API tests for Timetable endpoints."""

    def test_monitor_creates_slot(self, monitor_client):
        """2026-03-04: POST /timetable/ returns 201."""
        res = monitor_client.post('/api/v1/monitor-tools/timetable/', {
            'grade': 6, 'day_of_week': 1,
            'start_time': '08:00:00', 'end_time': '08:45:00',
            'subject': 'Mathematics',
        })
        assert res.status_code == 201
        assert res.data['subject'] == 'Mathematics'

    def test_student_views_timetable(self, student_client):
        """2026-03-04: Student GETs /timetable/ (grade inferred from token)."""
        res = student_client.get('/api/v1/monitor-tools/timetable/')
        assert res.status_code == 200
        assert 'slots' in res.data

    def test_monitor_updates_slot(self, monitor_client):
        """2026-03-04: PATCH /timetable/{id}/ updates subject."""
        slot = TimetableService.add_slot(6, 3, time(11, 0), time(11, 45), 'EVS')
        res = monitor_client.patch(
            f'/api/v1/monitor-tools/timetable/{slot.pk}/',
            {'subject': 'Environmental Science'},
        )
        assert res.status_code == 200
        assert res.data['subject'] == 'Environmental Science'

    def test_monitor_deletes_slot(self, monitor_client):
        """2026-03-04: DELETE /timetable/{id}/ returns 204."""
        slot = TimetableService.add_slot(6, 4, time(12, 0), time(12, 45), 'Hindi')
        res = monitor_client.delete(f'/api/v1/monitor-tools/timetable/{slot.pk}/')
        assert res.status_code == 204
        slot.refresh_from_db()
        assert not slot.is_active

    def test_today_schedule(self, student_client):
        """2026-03-04: GET /timetable/today/ returns today's classes."""
        res = student_client.get('/api/v1/monitor-tools/timetable/today/')
        assert res.status_code == 200
        assert 'slots' in res.data

    def test_non_monitor_cannot_create_slot(self, parent_client):
        """2026-03-04: Parent cannot create timetable slot — 403."""
        res = parent_client.post('/api/v1/monitor-tools/timetable/', {
            'grade': 6, 'day_of_week': 1,
            'start_time': '08:00:00', 'end_time': '08:45:00', 'subject': 'Art',
        })
        assert res.status_code == 403
