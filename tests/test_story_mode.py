"""
2026-02-27: Tests for the Story Mode Engine (BS-STY).

Purpose:
    Verify quest unlocking, bonus scene logic, subject-land mapping,
    chapter finale trigger, progress shape, recent_scenes limit,
    get_scene lookup, and all Story Mode API endpoints. Covers
    auth/authz, 200/404 responses, and fresh-student state.
"""

import pytest  # 2026-02-27: Pytest framework
from datetime import date  # 2026-02-27: Date for student DOB

from django.contrib.auth import get_user_model  # 2026-02-27: User model
from rest_framework.test import APIClient  # 2026-02-27: DRF test client
from rest_framework_simplejwt.tokens import RefreshToken  # 2026-02-27: JWT tokens

from services.auth_service.models import Parent, Student  # 2026-02-27: Auth models
from services.teaching_engine.models import (  # 2026-02-27: Teaching models
    TeachingLesson, ConceptMastery,
)
from services.story_mode_service.models import (  # 2026-02-27: Story models
    NarrativeScene, StudentStoryProgress,
)
from services.story_mode_service.services import (  # 2026-02-27: Story services
    StoryModeService, SUBJECT_LANDS,
)

User = get_user_model()  # 2026-02-27: Django User model


# ── Fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def parent_user(db):
    """2026-02-27: Create a parent user for story mode tests."""
    user = User.objects.create_user(username='story_parent', password='testpass123')
    parent = Parent.objects.create(
        user=user, phone='+919000001001', full_name='Story Parent',
        is_phone_verified=True, is_profile_complete=True,
    )
    return parent


@pytest.fixture
def student(parent_user, db):
    """2026-02-27: Create a grade-1 student for story mode tests."""
    user = User.objects.create_user(username='story_student', password='testpass123')
    return Student.objects.create(
        parent=parent_user, user=user, full_name='Story Student',
        dob=date(2016, 5, 10), age_group='6-12', grade=1,
        login_method='pin', language_1='English', language_2='Telugu',
    )


@pytest.fixture
def student_client(student):
    """2026-02-27: Authenticated API client for the student."""
    client = APIClient()
    token = RefreshToken.for_user(student.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def parent_client(parent_user):
    """2026-02-27: Authenticated API client for the parent."""
    client = APIClient()
    token = RefreshToken.for_user(parent_user.user)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(token.access_token)}')
    return client


@pytest.fixture
def lesson(db):
    """2026-02-27: Create a published English TeachingLesson."""
    return TeachingLesson.objects.create(
        lesson_id='ENG1_STORY_W01',
        title='Story Lesson Week 1',
        subject='English',
        class_number=1,
        week_number=1,
        status='published',
    )


@pytest.fixture
def mastery(student, lesson, db):
    """2026-02-27: Create a 4-star mastered ConceptMastery for day 1."""
    return ConceptMastery.objects.create(
        student=student, lesson=lesson, day_number=1,
        best_star_rating=4, attempts_count=1, is_mastered=True,
    )


@pytest.fixture
def narrative_scene(db):
    """2026-02-27: Get or create the NarrativeScene used by API tests (idempotent for seeded DB)."""
    scene, _ = NarrativeScene.objects.get_or_create(
        scene_id='english_q001',
        defaults={
            'subject': 'English',
            'scene_type': 'concept',
            'concept_slot': 1,
            'narrative_text': 'A test narrative.',
            'bonus_text': '',
            'illustration_ref': '',
        },
    )
    return scene


# ── TestStoryModeService ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestStoryModeService:
    """2026-02-27: Unit/integration tests for StoryModeService covering quest
    unlocking, bonus scenes, deduplication, progress counters, subject-land
    mapping, recent_scenes limit, chapter finale, get_scene lookup, and
    auto-creation of StudentStoryProgress."""

    def test_first_quest_unlock(self, student, mastery, db):
        """2026-02-27: unlock_scene for first concept returns a non-empty list of scenes."""
        result = StoryModeService.unlock_scene(student, mastery)
        assert isinstance(result, list)  # 2026-02-27: Always a list
        assert len(result) > 0  # 2026-02-27: At least one scene unlocked

    def test_5star_unlocks_bonus_scene(self, student, lesson, db):
        """2026-02-27: 5-star mastery → newly_unlocked includes a bonus scene."""
        five_star = ConceptMastery.objects.create(
            student=student, lesson=lesson, day_number=2,
            best_star_rating=5, attempts_count=1, is_mastered=True,
        )
        unlocked = StoryModeService.unlock_scene(student, five_star)
        scene_types = [s.get('scene_type') for s in unlocked]
        assert 'bonus' in scene_types  # 2026-02-27: Bonus scene present for 5-star

    def test_non5star_no_bonus(self, student, mastery, db):
        """2026-02-27: 4-star mastery → no bonus scene in newly_unlocked."""
        unlocked = StoryModeService.unlock_scene(student, mastery)
        scene_types = [s.get('scene_type') for s in unlocked]
        assert 'bonus' not in scene_types  # 2026-02-27: No bonus below 5 stars

    def test_no_duplicate_unlocks(self, student, mastery, db):
        """2026-02-27: Calling unlock_scene for the same concept twice → second call returns empty list."""
        StoryModeService.unlock_scene(student, mastery)
        second = StoryModeService.unlock_scene(student, mastery)
        assert second == []  # 2026-02-27: Already unlocked, nothing new

    def test_total_quests_increments(self, student, mastery, db):
        """2026-02-27: After unlocking a quest the StudentStoryProgress.total_quests_completed increases."""
        before = StudentStoryProgress.objects.filter(student=student).first()
        before_count = before.total_quests_completed if before else 0
        StoryModeService.unlock_scene(student, mastery)
        progress = StudentStoryProgress.objects.get(student=student)
        assert progress.total_quests_completed > before_count  # 2026-02-27: Counter incremented

    def test_subject_land_mapping(self, student, mastery, db):
        """2026-02-27: English lesson → unlocked scene has land = "Saraswati's Library"."""
        unlocked = StoryModeService.unlock_scene(student, mastery)
        lands = [s.get('land') for s in unlocked]
        assert SUBJECT_LANDS['English'] in lands  # 2026-02-27: Correct subject-land mapping

    def test_get_progress_shape(self, student, db):
        """2026-02-27: get_progress returns a dict with total_quests_completed, current_land, recent_scenes."""
        progress = StoryModeService.get_progress(student)
        assert 'total_quests_completed' in progress  # 2026-02-27: Required key
        assert 'current_land' in progress  # 2026-02-27: Required key
        assert 'recent_scenes' in progress  # 2026-02-27: Required key

    def test_recent_scenes_limit_3(self, student, lesson, db):
        """2026-02-27: Unlocking 5 scenes → recent_scenes in get_progress has at most 3 entries."""
        for day_num in range(1, 6):
            m = ConceptMastery.objects.create(
                student=student, lesson=lesson, day_number=day_num,
                best_star_rating=3, attempts_count=1, is_mastered=True,
            )
            StoryModeService.unlock_scene(student, m)
        progress = StoryModeService.get_progress(student)
        assert len(progress['recent_scenes']) <= 3  # 2026-02-27: Capped at 3

    def test_chapter_finale_at_10_quests(self, student, db):
        """2026-02-27: After unlocking 10 quests a chapter_finale scene is included."""
        for week_num in range(1, 11):
            extra_lesson = TeachingLesson.objects.create(
                lesson_id=f'ENG1_FINALE_W{week_num:02d}',
                title=f'Finale Lesson {week_num}',
                subject='English',
                class_number=1,
                week_number=week_num,
                status='published',
            )
            m = ConceptMastery.objects.create(
                student=student, lesson=extra_lesson, day_number=1,
                best_star_rating=4, attempts_count=1, is_mastered=True,
            )
            unlocked = StoryModeService.unlock_scene(student, m)

        # 2026-02-27: At exactly 10 quests the finale scene fires
        finale_scenes = [s for s in unlocked if s.get('scene_type') == 'chapter_finale']
        assert len(finale_scenes) >= 1  # 2026-02-27: Chapter finale triggered

    def test_get_scene_returns_detail(self, db):
        """2026-02-27: get_scene('english_q001') returns a dict with the scene's fields."""
        # 2026-03-02: Scene already seeded in DB; use get_or_create to be idempotent
        NarrativeScene.objects.get_or_create(
            scene_id='english_q001',
            defaults={
                'subject': 'English', 'scene_type': 'concept',
                'concept_slot': 1, 'narrative_text': 'A test narrative.',
                'bonus_text': '', 'illustration_ref': '',
            },
        )
        result = StoryModeService.get_scene('english_q001')
        assert result is not None  # 2026-02-27: Scene found
        assert result.get('scene_id') == 'english_q001'  # 2026-02-27: Correct scene

    def test_get_scene_not_found(self, db):
        """2026-02-27: get_scene('nonexistent') returns None for unknown scene_id."""
        result = StoryModeService.get_scene('nonexistent')
        assert result is None  # 2026-02-27: Missing scene → None

    def test_progress_created_if_not_exists(self, student, db):
        """2026-02-27: get_progress auto-creates StudentStoryProgress when none exists."""
        assert not StudentStoryProgress.objects.filter(student=student).exists()
        StoryModeService.get_progress(student)
        assert StudentStoryProgress.objects.filter(student=student).exists()  # 2026-02-27: Auto-created


# ── TestAPI ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestAPI:
    """2026-02-27: Integration tests for all Story Mode API endpoints.
    Covers progress GET, scene detail GET, 404 for missing scenes,
    auth/authz enforcement, and response shape validation."""

    def test_progress_get_200(self, student_client, student, db):
        """2026-02-27: GET /api/v1/story/progress/ → 200 OK."""
        response = student_client.get('/api/v1/story/progress/')
        assert response.status_code == 200  # 2026-02-27: Successful response

    def test_progress_has_total_quests(self, student_client, student, db):
        """2026-02-27: GET /api/v1/story/progress/ response body has 'total_quests_completed' key."""
        response = student_client.get('/api/v1/story/progress/')
        assert response.status_code == 200  # 2026-02-27: OK
        assert 'total_quests_completed' in response.json()  # 2026-02-27: Required key present

    def test_scene_detail_200(self, student_client, narrative_scene, db):
        """2026-02-27: GET /api/v1/story/scene/english_q001/ → 200 OK when scene exists in DB."""
        response = student_client.get('/api/v1/story/scene/english_q001/')
        assert response.status_code == 200  # 2026-02-27: Scene found

    def test_scene_not_found_404(self, student_client, db):
        """2026-02-27: GET /api/v1/story/scene/nonexistent/ → 404 Not Found."""
        response = student_client.get('/api/v1/story/scene/nonexistent/')
        assert response.status_code == 404  # 2026-02-27: Scene does not exist

    def test_unauthenticated_401_progress(self, db):
        """2026-02-27: GET /api/v1/story/progress/ without auth token → 401 Unauthorized."""
        client = APIClient()
        response = client.get('/api/v1/story/progress/')
        assert response.status_code == 401  # 2026-02-27: Auth required

    def test_unauthenticated_401_scene(self, narrative_scene, db):
        """2026-02-27: GET scene endpoint without auth token → 401 Unauthorized."""
        client = APIClient()
        response = client.get('/api/v1/story/scene/english_q001/')
        assert response.status_code == 401  # 2026-02-27: Auth required

    def test_parent_403_progress(self, parent_client, db):
        """2026-02-27: Parent user accessing progress endpoint → 403 Forbidden."""
        response = parent_client.get('/api/v1/story/progress/')
        assert response.status_code == 403  # 2026-02-27: Students only

    def test_parent_403_scene(self, parent_client, narrative_scene, db):
        """2026-02-27: Parent user accessing scene endpoint → 403 Forbidden."""
        response = parent_client.get('/api/v1/story/scene/english_q001/')
        assert response.status_code == 403  # 2026-02-27: Students only

    def test_progress_recent_scenes_list(self, student_client, student, db):
        """2026-02-27: GET /api/v1/story/progress/ → response['recent_scenes'] is a list."""
        response = student_client.get('/api/v1/story/progress/')
        assert response.status_code == 200  # 2026-02-27: OK
        assert isinstance(response.json().get('recent_scenes'), list)  # 2026-02-27: Always a list

    def test_progress_current_land_null_when_no_scenes(self, student_client, student, db):
        """2026-02-27: Fresh student with no unlocked scenes → current_land is None."""
        response = student_client.get('/api/v1/story/progress/')
        assert response.status_code == 200  # 2026-02-27: OK
        assert response.json().get('current_land') is None  # 2026-02-27: No land yet
