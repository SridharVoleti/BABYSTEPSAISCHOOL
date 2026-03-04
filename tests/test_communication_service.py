"""
2026-03-04: Tests for Communication Service (BS-COM-001/002/003, BS-PAR-006).

Covers:
  BS-COM-001: Messaging — thread creation, send, mark read, access control
  BS-COM-002: Announcements — create, list (grade-aware), access control
  BS-COM-003: Weekly reports — generate (mocked LLM), list
  BS-PAR-006: Term reports — generate, list, detail
"""

import uuid
from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.auth_service.models import Parent, Student
from services.communication_service.models import (
    Announcement, Message, MessageThread, TermReport, WeeklyProgressReport,
)
from services.communication_service.services import (
    AnnouncementService, MessagingService, TermReportService, WeeklyReportService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def monitor(db):
    """2026-03-04: Staff user (monitor)."""
    return User.objects.create_user(username='comm_monitor', password='pass', is_staff=True, first_name='Monitor')


@pytest.fixture
def monitor_client(monitor):
    client = APIClient()
    token = RefreshToken.for_user(monitor)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_user(db):
    user = User.objects.create_user(username='comm_parent', password='pass')
    return Parent.objects.create(
        user=user, phone='+919900002200', full_name='Comm Parent',
        is_phone_verified=True, is_profile_complete=True,
    )


@pytest.fixture
def student(db, parent_user):
    user = User.objects.create_user(username='comm_student', password='pass')
    return Student.objects.create(
        user=user, parent=parent_user, full_name='Comm Student',
        dob=date(2013, 1, 1), grade=6,
    )


@pytest.fixture
def parent_client(parent_user):
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    token['role'] = 'parent'
    token['parent_id'] = str(parent_user.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def student_client(student):
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    token['role'] = 'student'
    token['student_id'] = str(student.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


# ===========================================================================
# BS-COM-001: Messaging
# ===========================================================================

@pytest.mark.django_db
class TestMessagingService:
    """2026-03-04: Unit tests for MessagingService."""

    def test_create_thread(self, student, parent_user, monitor):
        """2026-03-04: get_or_create_thread creates a new thread."""
        thread = MessagingService.get_or_create_thread(student, parent_user, monitor, 'Help needed')
        assert thread.pk is not None
        assert thread.subject == 'Help needed'

    def test_get_existing_thread(self, student, parent_user, monitor):
        """2026-03-04: Second call returns same thread."""
        t1 = MessagingService.get_or_create_thread(student, parent_user, monitor)
        t2 = MessagingService.get_or_create_thread(student, parent_user, monitor)
        assert t1.pk == t2.pk

    def test_send_message(self, student, parent_user, monitor):
        """2026-03-04: Sending a message creates a Message record."""
        thread = MessagingService.get_or_create_thread(student, parent_user, monitor)
        msg = MessagingService.send_message(thread, 'parent', 'Hello monitor!')
        assert msg.sender_type == 'parent'
        assert msg.body == 'Hello monitor!'
        assert not msg.is_read

    def test_send_to_closed_thread_raises(self, student, parent_user, monitor):
        """2026-03-04: Cannot send to a closed thread."""
        thread = MessagingService.get_or_create_thread(student, parent_user, monitor)
        thread.is_closed = True
        thread.save()
        with pytest.raises(ValueError, match='closed'):
            MessagingService.send_message(thread, 'parent', 'Hello?')

    def test_mark_messages_read(self, student, parent_user, monitor):
        """2026-03-04: mark_messages_read marks incoming messages read."""
        thread = MessagingService.get_or_create_thread(student, parent_user, monitor)
        MessagingService.send_message(thread, 'monitor', 'Hi parent!')
        count = MessagingService.mark_messages_read(thread, 'parent')
        assert count == 1
        assert Message.objects.filter(thread=thread, is_read=False).count() == 0

    def test_list_threads_for_parent(self, student, parent_user, monitor):
        """2026-03-04: list_threads filters by parent."""
        MessagingService.get_or_create_thread(student, parent_user, monitor)
        threads = MessagingService.list_threads(parent=parent_user)
        assert len(threads) == 1


@pytest.mark.django_db
class TestMessagingAPI:
    """2026-03-04: API tests for Messaging endpoints."""

    def test_parent_creates_thread(self, parent_client, student, monitor):
        """2026-03-04: Parent POSTs /comms/threads/ — 201."""
        res = parent_client.post('/api/v1/comms/threads/', {
            'student_id': str(student.pk),
            'monitor_id': monitor.pk,
            'subject': 'Question about homework',
        })
        assert res.status_code == 201
        assert res.data['subject'] == 'Question about homework'

    def test_parent_lists_own_threads(self, parent_client, student, monitor):
        """2026-03-04: Parent sees their threads in GET /comms/threads/."""
        MessagingService.get_or_create_thread(student, student.parent, monitor)
        res = parent_client.get('/api/v1/comms/threads/')
        assert res.status_code == 200
        assert len(res.data['threads']) >= 1

    def test_send_message(self, parent_client, student, monitor):
        """2026-03-04: Parent sends a message to a thread."""
        thread = MessagingService.get_or_create_thread(student, student.parent, monitor)
        res = parent_client.post(f'/api/v1/comms/threads/{thread.pk}/send/', {'body': 'Hello!'})
        assert res.status_code == 201
        assert res.data['sender_type'] == 'parent'

    def test_thread_detail(self, parent_client, student, monitor):
        """2026-03-04: Parent views thread messages."""
        thread = MessagingService.get_or_create_thread(student, student.parent, monitor)
        MessagingService.send_message(thread, 'monitor', 'Test reply')
        res = parent_client.get(f'/api/v1/comms/threads/{thread.pk}/')
        assert res.status_code == 200
        assert len(res.data['messages']) == 1

    def test_mark_read(self, parent_client, student, monitor):
        """2026-03-04: POST /threads/{id}/read/ marks messages as read."""
        thread = MessagingService.get_or_create_thread(student, student.parent, monitor)
        MessagingService.send_message(thread, 'monitor', 'Hi parent')
        res = parent_client.post(f'/api/v1/comms/threads/{thread.pk}/read/')
        assert res.status_code == 200
        assert res.data['marked_read'] == 1

    def test_wrong_parent_cannot_view_thread(self, parent_client, monitor, db):
        """2026-03-04: Parent cannot view another parent's thread."""
        other_user = User.objects.create_user(username='other_p', password='pass')
        other_parent = Parent.objects.create(
            user=other_user, phone='+919100000001', full_name='Other',
            is_phone_verified=True, is_profile_complete=True,
        )
        other_student = Student.objects.create(
            user=User.objects.create_user(username='other_s', password='pass'),
            parent=other_parent, full_name='Other Student',
            dob=date(2013, 1, 1), grade=6,
        )
        thread = MessagingService.get_or_create_thread(other_student, other_parent, monitor)
        res = parent_client.get(f'/api/v1/comms/threads/{thread.pk}/')
        assert res.status_code == 403


# ===========================================================================
# BS-COM-002: Announcements
# ===========================================================================

@pytest.mark.django_db
class TestAnnouncementService:
    """2026-03-04: Unit tests for AnnouncementService."""

    def test_create_announcement(self, monitor):
        """2026-03-04: AnnouncementService.create stores announcement."""
        ann = AnnouncementService.create(
            title='Test', body='Body', priority='high', created_by=monitor
        )
        assert ann.pk is not None
        assert ann.priority == 'high'

    def test_list_active_excludes_inactive(self, monitor):
        """2026-03-04: Inactive announcements not returned."""
        ann = AnnouncementService.create(title='X', body='Y', created_by=monitor)
        ann.is_active = False
        ann.save()
        active = AnnouncementService.list_active()
        assert ann not in active


@pytest.mark.django_db
class TestAnnouncementAPI:
    """2026-03-04: API tests for Announcements."""

    def test_monitor_creates_announcement(self, monitor_client):
        """2026-03-04: POST /comms/announcements/ returns 201."""
        res = monitor_client.post('/api/v1/comms/announcements/', {
            'title': 'Sports Day', 'body': 'Annual sports day on March 15.',
            'priority': 'high',
        })
        assert res.status_code == 201

    def test_student_lists_announcements(self, student_client):
        """2026-03-04: Student can GET /comms/announcements/."""
        res = student_client.get('/api/v1/comms/announcements/')
        assert res.status_code == 200
        assert 'announcements' in res.data

    def test_parent_cannot_create(self, parent_client):
        """2026-03-04: Parent cannot POST — 403."""
        res = parent_client.post('/api/v1/comms/announcements/', {
            'title': 'T', 'body': 'B',
        })
        assert res.status_code == 403

    def test_unauthenticated_rejected(self):
        """2026-03-04: Unauthenticated GET returns 401."""
        client = APIClient()
        res = client.get('/api/v1/comms/announcements/')
        assert res.status_code == 401


# ===========================================================================
# BS-COM-003: Weekly Progress Reports
# ===========================================================================

@pytest.mark.django_db
class TestWeeklyReportService:
    """2026-03-04: Unit tests for WeeklyReportService."""

    @patch('services.communication_service.services.get_llm_provider')
    def test_generate_creates_report(self, mock_llm, student):
        """2026-03-04: generate_report stores a WeeklyProgressReport."""
        mock_llm.return_value.chat.return_value.text = 'Great week!'
        week_start = date(2026, 3, 2)
        report = WeeklyReportService.generate_report(
            student=student, week_start=week_start,
            attendance_days=5, lessons_completed=4, avg_star_rating=4.2,
        )
        assert report.summary_text == 'Great week!'
        assert report.attendance_days == 5
        assert report.week_end == date(2026, 3, 8)

    @patch('services.communication_service.services.get_llm_provider')
    def test_llm_failure_uses_fallback(self, mock_llm, student):
        """2026-03-04: LLM exception → fallback summary string."""
        mock_llm.return_value.chat.side_effect = Exception('LLM down')
        report = WeeklyReportService.generate_report(
            student=student, week_start=date(2026, 3, 2),
            lessons_completed=3,
        )
        assert 'completed 3 lessons' in report.summary_text

    @patch('services.communication_service.services.get_llm_provider')
    def test_highlights_for_high_rating(self, mock_llm, student):
        """2026-03-04: avg_star_rating ≥ 4 generates highlight."""
        mock_llm.return_value.chat.return_value.text = 'Nice'
        report = WeeklyReportService.generate_report(
            student=student, week_start=date(2026, 3, 2), avg_star_rating=4.5,
        )
        assert any('4.5' in h for h in report.highlights)

    @patch('services.communication_service.services.get_llm_provider')
    def test_idempotent_update_or_create(self, mock_llm, student):
        """2026-03-04: Regenerating same week overwrites, not duplicates."""
        mock_llm.return_value.chat.return_value.text = 'v1'
        WeeklyReportService.generate_report(student=student, week_start=date(2026, 3, 2))
        mock_llm.return_value.chat.return_value.text = 'v2'
        WeeklyReportService.generate_report(student=student, week_start=date(2026, 3, 2))
        count = WeeklyProgressReport.objects.filter(student=student, week_start=date(2026, 3, 2)).count()
        assert count == 1


@pytest.mark.django_db
class TestWeeklyReportAPI:
    """2026-03-04: API tests for Weekly Reports."""

    @patch('services.communication_service.services.get_llm_provider')
    def test_monitor_generates_report(self, mock_llm, monitor_client, student):
        """2026-03-04: POST /comms/weekly-reports/generate/ returns 201."""
        mock_llm.return_value.chat.return_value.text = 'Excellent week!'
        res = monitor_client.post('/api/v1/comms/weekly-reports/generate/', {
            'student_id': str(student.pk),
            'week_start': '2026-03-02',
            'attendance_days': 5,
            'lessons_completed': 3,
        })
        assert res.status_code == 201
        assert res.data['summary_text'] == 'Excellent week!'

    @patch('services.communication_service.services.get_llm_provider')
    def test_parent_lists_reports(self, mock_llm, parent_client, student):
        """2026-03-04: Parent lists their child's weekly reports."""
        mock_llm.return_value.chat.return_value.text = 'Summary'
        WeeklyReportService.generate_report(student=student, week_start=date(2026, 3, 2))
        res = parent_client.get(f'/api/v1/comms/weekly-reports/{student.pk}/')
        assert res.status_code == 200
        assert len(res.data['reports']) == 1

    def test_parent_cannot_generate(self, parent_client, student):
        """2026-03-04: Parent cannot trigger generation — 403."""
        res = parent_client.post('/api/v1/comms/weekly-reports/generate/', {
            'student_id': str(student.pk), 'week_start': '2026-03-02',
        })
        assert res.status_code == 403


# ===========================================================================
# BS-PAR-006: Term Reports
# ===========================================================================

@pytest.mark.django_db
class TestTermReportService:
    """2026-03-04: Unit tests for TermReportService."""

    def test_generate_stores_report(self, student, monitor):
        """2026-03-04: generate() creates a TermReport with report_data."""
        report = TermReportService.generate(
            student=student, academic_year='2025-2026', term='T1', generated_by=monitor
        )
        assert report.pk is not None
        assert 'student' in report.report_data
        assert report.report_data['term'] == 'T1'

    def test_idempotent(self, student, monitor):
        """2026-03-04: Regenerating same term overwrites, not duplicates."""
        TermReportService.generate(student=student, academic_year='2025-2026', term='T1')
        TermReportService.generate(student=student, academic_year='2025-2026', term='T1')
        count = TermReport.objects.filter(student=student, term='T1').count()
        assert count == 1

    def test_list_reports(self, student, monitor):
        """2026-03-04: list_reports returns all generated reports for student."""
        TermReportService.generate(student=student, academic_year='2025-2026', term='T1')
        TermReportService.generate(student=student, academic_year='2025-2026', term='T2')
        reports = TermReportService.list_reports(student)
        assert len(reports) == 2

    def test_get_report(self, student, monitor):
        """2026-03-04: get_report returns correct report or None."""
        TermReportService.generate(student=student, academic_year='2025-2026', term='T3')
        r = TermReportService.get_report(student, '2025-2026', 'T3')
        assert r is not None
        assert r.term == 'T3'
        assert TermReportService.get_report(student, '2025-2026', 'T1') is None


@pytest.mark.django_db
class TestTermReportAPI:
    """2026-03-04: API tests for Term Reports."""

    def test_monitor_generates_term_report(self, monitor_client, student):
        """2026-03-04: POST /comms/term-reports/generate/ returns 201."""
        res = monitor_client.post('/api/v1/comms/term-reports/generate/', {
            'student_id': str(student.pk),
            'academic_year': '2025-2026',
            'term': 'T1',
        })
        assert res.status_code == 201
        assert res.data['term'] == 'T1'

    def test_parent_views_term_reports(self, parent_client, student, monitor):
        """2026-03-04: Parent lists term reports for child."""
        TermReportService.generate(student=student, academic_year='2025-2026', term='T1')
        res = parent_client.get(f'/api/v1/comms/term-reports/{student.pk}/')
        assert res.status_code == 200
        assert len(res.data['reports']) == 1

    def test_parent_views_specific_term_report(self, parent_client, student):
        """2026-03-04: GET /term-reports/{id}/2025-2026/T2/ returns correct report."""
        TermReportService.generate(student=student, academic_year='2025-2026', term='T2')
        res = parent_client.get(f'/api/v1/comms/term-reports/{student.pk}/2025-2026/T2/')
        assert res.status_code == 200
        assert res.data['term'] == 'T2'

    def test_parent_cannot_generate(self, parent_client, student):
        """2026-03-04: Parent cannot trigger term report generation — 403."""
        res = parent_client.post('/api/v1/comms/term-reports/generate/', {
            'student_id': str(student.pk),
            'academic_year': '2025-2026', 'term': 'T1',
        })
        assert res.status_code == 403

    def test_missing_report_404(self, parent_client, student):
        """2026-03-04: Non-existent term report returns 404."""
        res = parent_client.get(f'/api/v1/comms/term-reports/{student.pk}/2025-2026/T3/')
        assert res.status_code == 404

    def test_wrong_parent_denied(self, parent_client, monitor, db):
        """2026-03-04: Parent cannot view another child's report — 403."""
        other_user = User.objects.create_user(username='other_p2', password='pass')
        other_parent = Parent.objects.create(
            user=other_user, phone='+919100000002', full_name='Other2',
            is_phone_verified=True, is_profile_complete=True,
        )
        other_student = Student.objects.create(
            user=User.objects.create_user(username='other_s2', password='pass'),
            parent=other_parent, full_name='Other2 Student',
            dob=date(2013, 1, 1), grade=7,
        )
        TermReportService.generate(student=other_student, academic_year='2025-2026', term='T1')
        res = parent_client.get(f'/api/v1/comms/term-reports/{other_student.pk}/')
        assert res.status_code == 403
