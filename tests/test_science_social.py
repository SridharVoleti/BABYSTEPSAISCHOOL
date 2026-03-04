"""
2026-03-03: Tests for Science & Social Science features (BS-SCI / BS-SST).

Purpose:
    Verify:
    - Assertion-Reason question evaluation via AdaptiveEngine.check_answer
    - TeachingService.get_subject_proficiency service method
    - SubjectProficiencyView API (GET /api/v1/teaching/proficiency/)
    - Science and Social Week 1 JSON content files load correctly
    - seed_science_social management command creates lesson records

~35 tests organised in 4 classes:
    - TestAssertionReasonEvaluation   : AR answer checking via adaptive engine
    - TestSubjectProficiencyService   : service-layer proficiency aggregation
    - TestSubjectProficiencyAPI       : HTTP endpoint behaviour
    - TestScienceSocialContent        : JSON content + seed command integration
"""

import json  # 2026-03-03: JSON parsing
import os    # 2026-03-03: File path checks
import pytest  # 2026-03-03: Pytest framework
from datetime import date  # 2026-03-03: DOB
from io import StringIO  # 2026-03-03: Capture management command output

from django.contrib.auth import get_user_model  # 2026-03-03: User model
from django.core.management import call_command  # 2026-03-03: Run management commands
from rest_framework.test import APIClient  # 2026-03-03: DRF test client

from services.auth_service.models import Parent, Student  # 2026-03-03: Auth models
from services.teaching_engine.adaptive import AdaptiveEngine  # 2026-03-03: Answer checker
from services.teaching_engine.content_loader import TeachingContentLoader  # 2026-03-03: Content loader
from services.teaching_engine.models import (  # 2026-03-03: Teaching models
    TeachingLesson, StudentLessonProgress, DayProgress,
)
from services.teaching_engine.services import TeachingService  # 2026-03-03: Under test

User = get_user_model()  # 2026-03-03: Django User model

# ── File paths ─────────────────────────────────────────────────────────────

SCI_JSON = 'json/teaching/class6/Science/week1.json'       # 2026-03-03: Science content
SCI_PRACTICE = 'json/teaching/class6/Science/week1_practice.json'  # 2026-03-03: Science practice
SST_JSON = 'json/teaching/class6/Social/week1.json'        # 2026-03-03: Social content
SST_PRACTICE = 'json/teaching/class6/Social/week1_practice.json'   # 2026-03-03: Social practice


# ── Shared fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-03-03: Create a parent for the test student."""
    user = User.objects.create_user(username='ss_parent', password='testpass123')
    return Parent.objects.create(
        user=user,
        phone='+919111111001',
        full_name='SS Parent',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def student(parent_user, db):
    """2026-03-03: Create a Class 6 student."""
    user = User.objects.create_user(username='ss_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user,
        user=user,
        full_name='SS Student',
        dob=date(2013, 5, 15),
        age_group='13-18',
        grade=6,
        login_method='pin',
    )


@pytest.fixture
def parent_user2(db):
    """2026-03-03: A second parent for negative-role API tests."""
    user = User.objects.create_user(username='ss_parent2', password='testpass123')
    return Parent.objects.create(
        user=user,
        phone='+919111111002',
        full_name='SS Parent2',
        is_phone_verified=True,
        is_profile_complete=True,
    )


@pytest.fixture
def api_client():
    """2026-03-03: DRF APIClient."""
    return APIClient()


@pytest.fixture
def auth_client(api_client, student):
    """2026-03-03: APIClient authenticated as the test student."""
    api_client.force_authenticate(user=student.user)
    return api_client


@pytest.fixture
def parent_auth_client(api_client, parent_user2):
    """2026-03-03: APIClient authenticated as a parent (not a student)."""
    api_client.force_authenticate(user=parent_user2.user)
    return api_client


@pytest.fixture
def sci_lesson(db):
    """2026-03-03: Published Science Class 6 Week 1 lesson record."""
    return TeachingLesson.objects.create(
        lesson_id='SCI6_ENV_CH01_W01',
        title='Our Environment — Air, Water, Soil and Forests',
        subject='Science',
        class_number=6,
        week_number=1,
        content_json_path=SCI_JSON,
        status='published',
    )


@pytest.fixture
def sst_lesson(db):
    """2026-03-03: Published Social Science Class 6 Week 1 lesson record."""
    return TeachingLesson.objects.create(
        lesson_id='SST6_EARTH_CH01_W01',
        title='The Earth in the Solar System',
        subject='Social',
        class_number=6,
        week_number=1,
        content_json_path=SST_JSON,
        status='published',
    )


def _make_lesson_progress(student, lesson, current_day=1, db=None):
    """2026-03-03: Create StudentLessonProgress for a student + lesson."""
    return StudentLessonProgress.objects.create(
        student=student,
        lesson=lesson,
        iq_level='standard',
        current_day=current_day,
        day_statuses={'1': 'teaching'},
    )


def _make_day_complete(lesson_progress, day_number, star_rating=4):
    """2026-03-03: Create a completed DayProgress record with given star rating."""
    return DayProgress.objects.create(
        lesson_progress=lesson_progress,
        day_number=day_number,
        status='day_complete',
        questions_attempted=10,
        questions_correct=8,
        mastery_star_rating=star_rating,
    )


# ══════════════════════════════════════════════════════════════════════════
# TestAssertionReasonEvaluation — AR answer checking via adaptive engine
# ══════════════════════════════════════════════════════════════════════════

class TestAssertionReasonEvaluation:
    """2026-03-03: Verify AdaptiveEngine.check_answer handles assertion_reason correctly."""

    AR_QUESTION = {
        'id': 'AR_TEST_01',
        'type': 'assertion_reason',
        'question': 'Select the correct option.',
        'assertion': 'Nitrogen is the most abundant gas in air.',
        'reason': 'Nitrogen makes up approximately 78% of the atmosphere.',
        'options': [
            'Both A and R are true, and R is the correct explanation of A',
            'Both A and R are true, but R is not the correct explanation of A',
            'A is true but R is false',
            'A is false but R is true',
        ],
        'correct_answer': 0,
        'explanation': 'Nitrogen (78%) is the most abundant. R correctly explains A.',
    }

    def test_ar_correct_answer_index_0(self):
        """2026-03-03: Integer 0 matches correct_answer 0."""
        is_correct, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 0)
        assert is_correct is True

    def test_ar_correct_answer_string_zero(self):
        """2026-03-03: String '0' also matches correct_answer 0 via str() comparison."""
        is_correct, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, '0')
        assert is_correct is True

    def test_ar_wrong_answer_index_1(self):
        """2026-03-03: Index 1 is incorrect when correct is 0."""
        is_correct, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 1)
        assert is_correct is False

    def test_ar_wrong_answer_index_2(self):
        """2026-03-03: Index 2 is incorrect."""
        is_correct, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 2)
        assert is_correct is False

    def test_ar_wrong_answer_index_3(self):
        """2026-03-03: Index 3 is incorrect."""
        is_correct, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 3)
        assert is_correct is False

    def test_ar_returns_correct_answer_value(self):
        """2026-03-03: Returned correct_answer is the integer index from the question."""
        _, correct_answer, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 1)
        assert correct_answer == 0

    def test_ar_returns_explanation(self):
        """2026-03-03: Explanation text is passed through correctly."""
        _, _, explanation = AdaptiveEngine.check_answer(self.AR_QUESTION, 0)
        assert 'Nitrogen' in explanation

    def test_ar_distinct_from_mcq_by_type(self):
        """2026-03-03: AR handled by dedicated branch — MCQ with same answer also works."""
        mcq_question = dict(self.AR_QUESTION, type='mcq')
        is_correct_mcq, _, _ = AdaptiveEngine.check_answer(mcq_question, 0)
        is_correct_ar, _, _ = AdaptiveEngine.check_answer(self.AR_QUESTION, 0)
        assert is_correct_mcq is True   # 2026-03-03: MCQ path — direct ==
        assert is_correct_ar is True    # 2026-03-03: AR path — str comparison


# ══════════════════════════════════════════════════════════════════════════
# TestSubjectProficiencyService — service-layer proficiency aggregation
# ══════════════════════════════════════════════════════════════════════════

class TestSubjectProficiencyService:
    """2026-03-03: Verify TeachingService.get_subject_proficiency returns correct data."""

    def test_proficiency_no_lessons_returns_empty_list(self, db, student):
        """2026-03-03: No lessons published → lessons list is empty."""
        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        assert result['success'] is True
        assert result['lessons'] == []

    def test_proficiency_lesson_not_started_returns_zero(self, db, student, sci_lesson):
        """2026-03-03: Lesson exists but student has no progress → mastery_percentage 0."""
        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        assert len(result['lessons']) == 1
        lesson_data = result['lessons'][0]
        assert lesson_data['lesson_id'] == 'SCI6_ENV_CH01_W01'
        assert lesson_data['mastery_percentage'] == 0
        assert lesson_data['completed_days'] == 0

    def test_proficiency_one_day_complete_returns_correct_pct(self, db, student, sci_lesson):
        """2026-03-03: 1 day complete with 4-star rating → mastery_percentage 80.0."""
        lp = _make_lesson_progress(student, sci_lesson)
        _make_day_complete(lp, day_number=1, star_rating=4)

        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        lesson_data = result['lessons'][0]
        assert lesson_data['completed_days'] == 1
        # 2026-03-03: (4 / 5) * 100 = 80.0
        assert lesson_data['mastery_percentage'] == 80.0

    def test_proficiency_four_days_complete_five_stars(self, db, student, sci_lesson):
        """2026-03-03: All 4 days at 5 stars → mastery_percentage 100.0."""
        lp = _make_lesson_progress(student, sci_lesson)
        for day in range(1, 5):
            _make_day_complete(lp, day_number=day, star_rating=5)

        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        lesson_data = result['lessons'][0]
        assert lesson_data['completed_days'] == 4
        assert lesson_data['mastery_percentage'] == 100.0

    def test_proficiency_filters_by_subject(self, db, student, sci_lesson, sst_lesson):
        """2026-03-03: Subject filter returns only Science lessons."""
        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        lesson_ids = [l['lesson_id'] for l in result['lessons']]
        assert 'SCI6_ENV_CH01_W01' in lesson_ids
        assert 'SST6_EARTH_CH01_W01' not in lesson_ids

    def test_proficiency_filters_by_class_number(self, db, student, sci_lesson):
        """2026-03-03: Wrong class_number → empty list even if subject matches."""
        result = TeachingService.get_subject_proficiency(student, 'Science', 7)
        assert result['lessons'] == []

    def test_proficiency_response_includes_metadata(self, db, student, sci_lesson):
        """2026-03-03: Response includes subject, class_number, total_days."""
        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        assert result['subject'] == 'Science'
        assert result['class_number'] == 6
        assert result['lessons'][0]['total_days'] == 4

    def test_proficiency_orders_by_week_number(self, db, student):
        """2026-03-03: Multiple lessons returned in week_number ascending order."""
        TeachingLesson.objects.create(
            lesson_id='SCI6_ENV_CH01_W02',
            title='Week 2 Science',
            subject='Science',
            class_number=6,
            week_number=2,
            content_json_path=SCI_JSON,
            status='published',
        )
        TeachingLesson.objects.create(
            lesson_id='SCI6_ENV_CH01_W01',
            title='Week 1 Science',
            subject='Science',
            class_number=6,
            week_number=1,
            content_json_path=SCI_JSON,
            status='published',
        )
        result = TeachingService.get_subject_proficiency(student, 'Science', 6)
        week_numbers = [l['week_number'] for l in result['lessons']]
        assert week_numbers == sorted(week_numbers)


# ══════════════════════════════════════════════════════════════════════════
# TestSubjectProficiencyAPI — HTTP endpoint behaviour
# ══════════════════════════════════════════════════════════════════════════

PROFICIENCY_URL = '/api/v1/teaching/proficiency/'  # 2026-03-03: Endpoint under test


class TestSubjectProficiencyAPI:
    """2026-03-03: Verify GET /api/v1/teaching/proficiency/ responses."""

    def test_proficiency_unauthenticated_returns_401(self, api_client):
        """2026-03-03: No token → 401 Unauthorized."""
        resp = api_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 401

    def test_proficiency_as_parent_returns_403(self, parent_auth_client):
        """2026-03-03: Parent role has no student_profile → 403 Forbidden."""
        resp = parent_auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 403

    def test_proficiency_missing_subject_returns_400(self, auth_client):
        """2026-03-03: Omitting subject → 400 Bad Request."""
        resp = auth_client.get(PROFICIENCY_URL, {'class_number': '6'})
        assert resp.status_code == 400
        assert 'subject' in resp.data.get('error', '')

    def test_proficiency_missing_class_number_returns_400(self, auth_client):
        """2026-03-03: Omitting class_number → 400 Bad Request."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science'})
        assert resp.status_code == 400
        assert 'class_number' in resp.data.get('error', '')

    def test_proficiency_invalid_class_number_returns_400(self, auth_client):
        """2026-03-03: Non-integer class_number → 400 Bad Request."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': 'abc'})
        assert resp.status_code == 400
        assert 'integer' in resp.data.get('error', '')

    def test_proficiency_science_no_lessons_returns_200(self, auth_client, db):
        """2026-03-03: Valid request with no lessons → 200 with empty lessons list."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 200
        assert resp.data['success'] is True
        assert resp.data['lessons'] == []

    def test_proficiency_social_no_lessons_returns_200(self, auth_client, db):
        """2026-03-03: Social Science with no lessons → 200 with empty list."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Social', 'class_number': '6'})
        assert resp.status_code == 200
        assert resp.data['lessons'] == []

    def test_proficiency_returns_science_lesson(self, auth_client, sci_lesson):
        """2026-03-03: Science lesson exists → appears in response."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 200
        assert len(resp.data['lessons']) == 1
        assert resp.data['lessons'][0]['lesson_id'] == 'SCI6_ENV_CH01_W01'

    def test_proficiency_after_day_complete_shows_progress(self, auth_client, student, sci_lesson, db):
        """2026-03-03: After completing day 1, mastery_percentage > 0."""
        lp = _make_lesson_progress(student, sci_lesson)
        _make_day_complete(lp, day_number=1, star_rating=4)

        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 200
        lesson_data = resp.data['lessons'][0]
        assert lesson_data['completed_days'] == 1
        assert lesson_data['mastery_percentage'] > 0

    def test_proficiency_response_schema_valid(self, auth_client, sci_lesson):
        """2026-03-03: Response contains all expected schema fields."""
        resp = auth_client.get(PROFICIENCY_URL, {'subject': 'Science', 'class_number': '6'})
        assert resp.status_code == 200
        assert 'success' in resp.data
        assert 'subject' in resp.data
        assert 'class_number' in resp.data
        assert 'lessons' in resp.data
        lesson = resp.data['lessons'][0]
        for field in ('lesson_id', 'title', 'week_number', 'completed_days', 'total_days', 'mastery_percentage'):
            assert field in lesson, f"Missing field: {field}"


# ══════════════════════════════════════════════════════════════════════════
# TestScienceSocialContent — JSON content + seed command integration
# ══════════════════════════════════════════════════════════════════════════

class TestScienceSocialContent:
    """2026-03-03: Verify JSON content files are valid and seed command works."""

    def test_science_week1_json_file_exists(self):
        """2026-03-03: Science week1.json file exists on disk."""
        assert os.path.isfile(SCI_JSON), f"File not found: {SCI_JSON}"

    def test_science_week1_json_loads_without_error(self):
        """2026-03-03: Science week1.json is valid JSON and loads cleanly."""
        with open(SCI_JSON, encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert 'lesson_id' in data
        assert data['lesson_id'] == 'SCI6_ENV_CH01_W01'

    def test_science_week1_day1_has_all_three_iq_levels(self):
        """2026-03-03: Day 1 teaching_content has foundation, standard, advanced."""
        with open(SCI_JSON, encoding='utf-8') as f:
            data = json.load(f)
        day1 = data['micro_lessons'][0]
        tc = day1['teaching_content']
        for level in ('foundation', 'standard', 'advanced'):
            assert level in tc, f"Missing IQ level '{level}' in teaching_content"

    def test_science_week1_content_loader_loads_day1(self):
        """2026-03-03: TeachingContentLoader.get_day_content loads day 1 correctly."""
        content = TeachingContentLoader.get_day_content(SCI_JSON, 1, 'standard')
        assert content is not None
        assert 'teaching_content' in content
        assert 'vocabulary' in content
        assert 'practice_questions' in content

    def test_science_practice_bank_exists(self):
        """2026-03-03: Science week1_practice.json exists on disk."""
        assert os.path.isfile(SCI_PRACTICE), f"File not found: {SCI_PRACTICE}"

    def test_science_practice_bank_has_ar_question(self):
        """2026-03-03: Science practice bank contains at least one assertion_reason question."""
        with open(SCI_PRACTICE, encoding='utf-8') as f:
            data = json.load(f)
        ar_found = False
        for day_key in ('day_1', 'day_2', 'day_3', 'day_4'):
            day_data = data.get('practice_bank', {}).get(day_key, {})
            for difficulty in ('easy', 'medium', 'hard'):
                for q in day_data.get('questions', {}).get(difficulty, []):
                    if q.get('type') == 'assertion_reason':
                        ar_found = True
        assert ar_found, "No assertion_reason question found in Science practice bank"

    def test_social_week1_json_file_exists(self):
        """2026-03-03: Social week1.json file exists on disk."""
        assert os.path.isfile(SST_JSON), f"File not found: {SST_JSON}"

    def test_social_week1_json_loads_without_error(self):
        """2026-03-03: Social week1.json is valid JSON."""
        with open(SST_JSON, encoding='utf-8') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data['lesson_id'] == 'SST6_EARTH_CH01_W01'

    def test_social_week1_day1_has_all_three_iq_levels(self):
        """2026-03-03: Social day 1 teaching_content has all IQ variants."""
        with open(SST_JSON, encoding='utf-8') as f:
            data = json.load(f)
        day1 = data['micro_lessons'][0]
        tc = day1['teaching_content']
        for level in ('foundation', 'standard', 'advanced'):
            assert level in tc, f"Missing IQ level '{level}' in Social teaching_content"

    def test_social_practice_bank_has_ar_question(self):
        """2026-03-03: Social practice bank contains at least one assertion_reason question."""
        with open(SST_PRACTICE, encoding='utf-8') as f:
            data = json.load(f)
        ar_found = False
        for day_key in ('day_1', 'day_2', 'day_3', 'day_4'):
            day_data = data.get('practice_bank', {}).get(day_key, {})
            for difficulty in ('easy', 'medium', 'hard'):
                for q in day_data.get('questions', {}).get(difficulty, []):
                    if q.get('type') == 'assertion_reason':
                        ar_found = True
        assert ar_found, "No assertion_reason question found in Social practice bank"

    def test_seed_command_creates_science_lesson(self, db):
        """2026-03-03: seed_science_social command creates the Science lesson record."""
        assert not TeachingLesson.objects.filter(lesson_id='SCI6_ENV_CH01_W01').exists()
        call_command('seed_science_social', stdout=StringIO())
        assert TeachingLesson.objects.filter(lesson_id='SCI6_ENV_CH01_W01').exists()

    def test_seed_command_creates_social_lesson(self, db):
        """2026-03-03: seed_science_social command creates the Social lesson record."""
        assert not TeachingLesson.objects.filter(lesson_id='SST6_EARTH_CH01_W01').exists()
        call_command('seed_science_social', stdout=StringIO())
        assert TeachingLesson.objects.filter(lesson_id='SST6_EARTH_CH01_W01').exists()

    def test_seed_command_is_idempotent(self, db):
        """2026-03-03: Running seed_science_social twice does not create duplicates."""
        call_command('seed_science_social', stdout=StringIO())
        call_command('seed_science_social', stdout=StringIO())
        assert TeachingLesson.objects.filter(subject='Science', class_number=6).count() == 1
        assert TeachingLesson.objects.filter(subject='Social', class_number=6).count() == 1

    def test_seed_command_sets_status_published(self, db):
        """2026-03-03: Seeded lessons have status='published'."""
        call_command('seed_science_social', stdout=StringIO())
        sci = TeachingLesson.objects.get(lesson_id='SCI6_ENV_CH01_W01')
        sst = TeachingLesson.objects.get(lesson_id='SST6_EARTH_CH01_W01')
        assert sci.status == 'published'
        assert sst.status == 'published'
