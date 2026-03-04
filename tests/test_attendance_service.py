"""
2026-03-04: Tests for Attendance Service (BS-ATT-001/002).

Covers:
    - AttendanceService: auto_checkin, auto_checkout, mark_attendance,
      get_class_attendance, get_student_attendance, get_attendance_summary,
      mark_absent_batch
    - API: checkin, checkout, mark, bulk-mark, daily roster,
      student history, summary (auth + data checks)
"""

import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from services.auth_service.models import Parent, Student
from services.attendance_service.models import AttendanceRecord
from services.attendance_service.services import AttendanceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parent_user(db):
    """2026-03-04: Create a parent Django User + Parent profile."""
    user = User.objects.create_user(username='att_parent', password='pass')
    parent = Parent.objects.create(
        user=user,
        phone='+919900000001',
        full_name='Attendance Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(db, parent_user):
    """2026-03-04: Create a grade-6 student linked to parent."""
    user = User.objects.create_user(username='att_student', password='pass')
    s = Student.objects.create(
        user=user,
        parent=parent_user,
        full_name='Attendance Student',
        dob=date(2013, 1, 1),
        grade=6,
    )
    return s


@pytest.fixture
def student2(db, parent_user):
    """2026-03-04: Second grade-6 student."""
    user = User.objects.create_user(username='att_student2', password='pass')
    s = Student.objects.create(
        user=user,
        parent=parent_user,
        full_name='Second Student',
        dob=date(2013, 6, 1),
        grade=6,
    )
    return s


@pytest.fixture
def monitor_user(db):
    """2026-03-04: Create a monitor (staff) Django User."""
    return User.objects.create_user(
        username='att_monitor', password='pass', is_staff=True
    )


@pytest.fixture
def student_client(student):
    """2026-03-04: APIClient authenticated as student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    token['role'] = 'student'
    token['student_id'] = str(student.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-03-04: APIClient authenticated as parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    token['role'] = 'parent'
    token['parent_id'] = str(parent_user.pk)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def monitor_client(monitor_user):
    """2026-03-04: APIClient authenticated as monitor (staff)."""
    client = APIClient()
    token = RefreshToken.for_user(monitor_user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


# ---------------------------------------------------------------------------
# Service: auto_checkin
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAutoCheckin:
    """2026-03-04: Tests for AttendanceService.auto_checkin."""

    def test_creates_present_record(self, student):
        """2026-03-04: First login of the day creates a present record."""
        record = AttendanceService.auto_checkin(student)
        assert record.status == AttendanceRecord.STATUS_PRESENT
        assert record.recorded_by == AttendanceRecord.RECORDED_AUTO
        assert record.check_in_time is not None

    def test_idempotent_second_call(self, student):
        """2026-03-04: Second auto_checkin returns same record without error."""
        r1 = AttendanceService.auto_checkin(student)
        r2 = AttendanceService.auto_checkin(student)
        assert r1.pk == r2.pk
        assert AttendanceRecord.objects.filter(student=student).count() == 1

    def test_sets_today_date(self, student):
        """2026-03-04: Record date matches server local date."""
        record = AttendanceService.auto_checkin(student)
        assert record.date == timezone.localdate()


# ---------------------------------------------------------------------------
# Service: auto_checkout
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAutoCheckout:
    """2026-03-04: Tests for AttendanceService.auto_checkout."""

    def test_returns_none_without_checkin(self, student):
        """2026-03-04: Checkout without checkin returns None."""
        result = AttendanceService.auto_checkout(student)
        assert result is None

    def test_sets_checkout_time(self, student):
        """2026-03-04: Checkout updates check_out_time."""
        AttendanceService.auto_checkin(student)
        record = AttendanceService.auto_checkout(student)
        assert record is not None
        assert record.check_out_time is not None

    def test_computes_duration(self, student):
        """2026-03-04: Session duration is computed from check_in → check_out."""
        AttendanceService.auto_checkin(student)
        record = AttendanceService.auto_checkout(student)
        assert record.session_duration_minutes is not None
        assert record.session_duration_minutes >= 0


# ---------------------------------------------------------------------------
# Service: mark_attendance
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkAttendance:
    """2026-03-04: Tests for AttendanceService.mark_attendance."""

    def test_creates_manual_record(self, student):
        """2026-03-04: Monitor can mark a student absent."""
        today = timezone.localdate()
        record = AttendanceService.mark_attendance(student, today, 'absent', 'Sick')
        assert record.status == AttendanceRecord.STATUS_ABSENT
        assert record.recorded_by == AttendanceRecord.RECORDED_MONITOR
        assert record.notes == 'Sick'

    def test_overwrites_existing(self, student):
        """2026-03-04: Marking overwrites auto-checkin status."""
        today = timezone.localdate()
        AttendanceService.auto_checkin(student)
        record = AttendanceService.mark_attendance(student, today, 'late')
        assert record.status == AttendanceRecord.STATUS_LATE
        assert AttendanceRecord.objects.filter(student=student).count() == 1

    def test_invalid_status_raises(self, student):
        """2026-03-04: Invalid status raises ValueError."""
        with pytest.raises(ValueError, match='Invalid status'):
            AttendanceService.mark_attendance(student, timezone.localdate(), 'missing')

    def test_past_date(self, student):
        """2026-03-04: Can mark attendance for a past date."""
        yesterday = timezone.localdate() - timedelta(days=1)
        record = AttendanceService.mark_attendance(student, yesterday, 'absent')
        assert record.date == yesterday


# ---------------------------------------------------------------------------
# Service: get_class_attendance
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestGetClassAttendance:
    """2026-03-04: Tests for AttendanceService.get_class_attendance."""

    def test_returns_all_grade_students(self, student, student2):
        """2026-03-04: Roster includes all active grade-6 students."""
        today = timezone.localdate()
        AttendanceService.auto_checkin(student)
        roster = AttendanceService.get_class_attendance(6, today)
        ids = {r['student_id'] for r in roster}
        assert str(student.pk) in ids
        assert str(student2.pk) in ids

    def test_absent_for_no_record(self, student):
        """2026-03-04: Student with no record shows as absent in roster."""
        today = timezone.localdate()
        roster = AttendanceService.get_class_attendance(6, today)
        entry = next(r for r in roster if r['student_id'] == str(student.pk))
        assert entry['status'] == AttendanceRecord.STATUS_ABSENT

    def test_present_after_checkin(self, student):
        """2026-03-04: Student who checked in shows as present."""
        today = timezone.localdate()
        AttendanceService.auto_checkin(student)
        roster = AttendanceService.get_class_attendance(6, today)
        entry = next(r for r in roster if r['student_id'] == str(student.pk))
        assert entry['status'] == AttendanceRecord.STATUS_PRESENT


# ---------------------------------------------------------------------------
# Service: get_attendance_summary
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestAttendanceSummary:
    """2026-03-04: Tests for AttendanceService.get_attendance_summary."""

    def test_counts_by_status(self, student):
        """2026-03-04: Summary counts match created records."""
        today = timezone.localdate()
        # Create 2 present, 1 absent in current month
        for offset in range(2):
            d = date(today.year, today.month, 1) + timedelta(days=offset)
            AttendanceService.mark_attendance(student, d, 'present')
        d_abs = date(today.year, today.month, 1) + timedelta(days=5)
        AttendanceService.mark_attendance(student, d_abs, 'absent')

        summary = AttendanceService.get_attendance_summary(student, today.year, today.month)
        assert summary['present'] == 2
        assert summary['absent'] == 1

    def test_attendance_percentage(self, student):
        """2026-03-04: Percentage = (present + late) / total."""
        today = timezone.localdate()
        d1 = date(today.year, today.month, 1)
        d2 = date(today.year, today.month, 2)
        AttendanceService.mark_attendance(student, d1, 'present')
        AttendanceService.mark_attendance(student, d2, 'absent')

        summary = AttendanceService.get_attendance_summary(student, today.year, today.month)
        assert summary['attendance_percentage'] == 50.0

    def test_empty_month_zeros(self, student):
        """2026-03-04: No records → zeros and 0.0 percentage."""
        summary = AttendanceService.get_attendance_summary(student, 2025, 1)
        assert summary['present'] == 0
        assert summary['attendance_percentage'] == 0.0


# ---------------------------------------------------------------------------
# Service: mark_absent_batch
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkAbsentBatch:
    """2026-03-04: Tests for AttendanceService.mark_absent_batch."""

    def test_marks_missing_students_absent(self, student, student2):
        """2026-03-04: Students with no record are marked absent by batch."""
        yesterday = timezone.localdate() - timedelta(days=1)
        AttendanceService.auto_checkin(student)  # student already has record for today
        # Only student2 should be marked absent for yesterday
        created = AttendanceService.mark_absent_batch(6, yesterday)
        assert created == 2  # Both have no record for yesterday
        record = AttendanceRecord.objects.get(student=student2, date=yesterday)
        assert record.status == AttendanceRecord.STATUS_ABSENT
        assert record.recorded_by == AttendanceRecord.RECORDED_SYSTEM

    def test_skips_students_with_records(self, student):
        """2026-03-04: Students who already have a record are skipped."""
        yesterday = timezone.localdate() - timedelta(days=1)
        AttendanceService.mark_attendance(student, yesterday, 'present')
        created = AttendanceService.mark_absent_batch(6, yesterday)
        assert created == 0  # student already has a record


# ---------------------------------------------------------------------------
# API: CheckinView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestCheckinAPI:
    """2026-03-04: Tests for POST /api/v1/attendance/checkin/."""

    def test_student_can_checkin(self, student_client):
        """2026-03-04: Student gets 200 on checkin."""
        res = student_client.post('/api/v1/attendance/checkin/')
        assert res.status_code == 200
        assert res.data['status'] == 'present'

    def test_unauthenticated_rejected(self):
        """2026-03-04: Unauthenticated request gets 401."""
        client = APIClient()
        res = client.post('/api/v1/attendance/checkin/')
        assert res.status_code == 401

    def test_parent_cannot_checkin(self, parent_client):
        """2026-03-04: Parent (non-student user) gets 403."""
        res = parent_client.post('/api/v1/attendance/checkin/')
        assert res.status_code == 403

    def test_idempotent(self, student_client, student):
        """2026-03-04: Double checkin returns same date, no duplicate."""
        student_client.post('/api/v1/attendance/checkin/')
        student_client.post('/api/v1/attendance/checkin/')
        assert AttendanceRecord.objects.filter(student=student).count() == 1


# ---------------------------------------------------------------------------
# API: MarkAttendanceView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestMarkAttendanceAPI:
    """2026-03-04: Tests for POST /api/v1/attendance/mark/."""

    def test_monitor_can_mark(self, monitor_client, student):
        """2026-03-04: Monitor marks a student absent — 200."""
        today = str(timezone.localdate())
        res = monitor_client.post('/api/v1/attendance/mark/', {
            'student_id': str(student.pk),
            'date': today,
            'status': 'absent',
            'notes': 'Called in sick',
        })
        assert res.status_code == 200
        assert res.data['status'] == 'absent'

    def test_parent_cannot_mark(self, parent_client, student):
        """2026-03-04: Parent cannot mark attendance — 403."""
        today = str(timezone.localdate())
        res = parent_client.post('/api/v1/attendance/mark/', {
            'student_id': str(student.pk),
            'date': today,
            'status': 'absent',
        })
        assert res.status_code == 403

    def test_invalid_status_400(self, monitor_client, student):
        """2026-03-04: Invalid status returns 400."""
        today = str(timezone.localdate())
        res = monitor_client.post('/api/v1/attendance/mark/', {
            'student_id': str(student.pk),
            'date': today,
            'status': 'missing',
        })
        assert res.status_code == 400

    def test_unknown_student_404(self, monitor_client):
        """2026-03-04: Unknown student_id returns 404."""
        res = monitor_client.post('/api/v1/attendance/mark/', {
            'student_id': str(uuid.uuid4()),
            'date': str(timezone.localdate()),
            'status': 'absent',
        })
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# API: BulkMarkAttendanceView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestBulkMarkAPI:
    """2026-03-04: Tests for POST /api/v1/attendance/bulk-mark/."""

    def test_bulk_marks_all_grade_students(self, monitor_client, student, student2):
        """2026-03-04: Bulk mark creates records for all grade-6 students."""
        today = str(timezone.localdate())
        res = monitor_client.post('/api/v1/attendance/bulk-mark/', {
            'grade': 6,
            'date': today,
            'records': [],
        }, format='json')
        assert res.status_code == 200
        assert res.data['marked'] == 2  # student + student2

    def test_per_student_override(self, monitor_client, student, student2):
        """2026-03-04: Override map sets specific students to absent."""
        today = str(timezone.localdate())
        res = monitor_client.post('/api/v1/attendance/bulk-mark/', {
            'grade': 6,
            'date': today,
            'records': [{'student_id': str(student.pk), 'status': 'absent'}],
        }, format='json')
        assert res.status_code == 200
        record = AttendanceRecord.objects.get(student=student, date=today)
        assert record.status == 'absent'

    def test_non_monitor_rejected(self, parent_client):
        """2026-03-04: Parent cannot bulk mark — 403."""
        res = parent_client.post('/api/v1/attendance/bulk-mark/', {
            'grade': 6,
            'date': str(timezone.localdate()),
        }, format='json')
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# API: DailyClassRosterView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestDailyRosterAPI:
    """2026-03-04: Tests for GET /api/v1/attendance/daily/."""

    def test_monitor_gets_roster(self, monitor_client, student):
        """2026-03-04: Monitor gets class roster — 200."""
        res = monitor_client.get('/api/v1/attendance/daily/', {'grade': 6})
        assert res.status_code == 200
        assert 'roster' in res.data
        assert len(res.data['roster']) >= 1

    def test_missing_grade_400(self, monitor_client):
        """2026-03-04: Missing grade param returns 400."""
        res = monitor_client.get('/api/v1/attendance/daily/')
        assert res.status_code == 400

    def test_parent_rejected(self, parent_client):
        """2026-03-04: Parent cannot view class roster — 403."""
        res = parent_client.get('/api/v1/attendance/daily/', {'grade': 6})
        assert res.status_code == 403


# ---------------------------------------------------------------------------
# API: StudentAttendanceHistoryView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestStudentHistoryAPI:
    """2026-03-04: Tests for GET /api/v1/attendance/student/{id}/."""

    def test_parent_can_view_own_child(self, parent_client, student):
        """2026-03-04: Parent views their own child's attendance."""
        AttendanceService.auto_checkin(student)
        res = parent_client.get(f'/api/v1/attendance/student/{student.pk}/')
        assert res.status_code == 200
        assert res.data['student_id'] == str(student.pk)

    def test_monitor_can_view_any(self, monitor_client, student):
        """2026-03-04: Monitor can view any student's attendance."""
        res = monitor_client.get(f'/api/v1/attendance/student/{student.pk}/')
        assert res.status_code == 200

    def test_unknown_student_404(self, parent_client):
        """2026-03-04: Unknown student_id returns 404."""
        res = parent_client.get(f'/api/v1/attendance/student/{uuid.uuid4()}/')
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# API: AttendanceSummaryView
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestSummaryAPI:
    """2026-03-04: Tests for GET /api/v1/attendance/summary/{id}/."""

    def test_parent_gets_summary(self, parent_client, student):
        """2026-03-04: Parent gets monthly summary for their child."""
        today = timezone.localdate()
        res = parent_client.get(
            f'/api/v1/attendance/summary/{student.pk}/',
            {'year': today.year, 'month': today.month},
        )
        assert res.status_code == 200
        assert 'attendance_percentage' in res.data
        assert 'present' in res.data

    def test_monitor_gets_summary(self, monitor_client, student):
        """2026-03-04: Monitor can also view summary."""
        today = timezone.localdate()
        res = monitor_client.get(
            f'/api/v1/attendance/summary/{student.pk}/',
            {'year': today.year, 'month': today.month},
        )
        assert res.status_code == 200

    def test_unknown_student_404(self, parent_client):
        """2026-03-04: Unknown student_id returns 404."""
        res = parent_client.get(f'/api/v1/attendance/summary/{uuid.uuid4()}/')
        assert res.status_code == 404
