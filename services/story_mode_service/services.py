"""
2026-02-27: Business logic for Story Mode Service (BS-GAM-003).

Implements narrative quest unlocking as students master concepts.
Each mastered concept unlocks a scene in the student's story,
building a personalised educational narrative.
"""
import logging  # 2026-02-27: Structured application logging

from django.utils import timezone  # 2026-02-27: Timezone-aware datetimes

from services.auth_service.models import Student  # 2026-02-27: Student profile
from services.teaching_engine.models import (  # 2026-02-27: Mastery + lesson models
    ConceptMastery,
    TeachingLesson,
)

from .models import NarrativeScene, StudentStoryProgress  # 2026-02-27: Story models

logger = logging.getLogger(__name__)

# 2026-02-27: Mapping from subject to narrative "land" name
SUBJECT_LANDS = {
    'English': "Saraswati's Library",
    'Math': "Aryabhatta's Kingdom",
    'Science': "Vaisheshika Valley",
    'Hindi': "Devanagari Dham",
    'Telugu': "Andhra Vanam",
}


class StoryModeService:
    """2026-02-27: Service for unlocking narrative scenes as students learn."""

    @classmethod
    def unlock_scene(cls, student, mastery):
        """
        2026-02-27: Unlock narrative scene(s) after a concept is mastered.

        Counts mastered concepts in the lesson's subject to determine
        concept_slot. Finds the matching NarrativeScene and appends it
        to StudentStoryProgress.unlocked_scene_ids. If 5★, also unlocks
        bonus scene. Every 10th mastery in the subject → chapter_finale.

        Args:
            student: Student model instance.
            mastery: ConceptMastery model instance (already saved to DB).

        Returns:
            list[dict]: Newly unlocked scenes (may be empty if no scene found).
        """
        # 2026-02-27: Extract fields from mastery object
        lesson = mastery.lesson
        stars = mastery.best_star_rating
        newly_unlocked = []

        # 2026-02-27: Count mastered concepts in this subject for this student
        subject = lesson.subject
        mastered_count = ConceptMastery.objects.filter(
            student=student,
            lesson__subject=subject,
            is_mastered=True,
        ).count()
        concept_slot = mastered_count  # 2026-02-27: Slot = count after mastery

        # 2026-02-27: Find matching concept scene
        concept_scene = NarrativeScene.objects.filter(
            subject=subject,
            concept_slot=concept_slot,
            scene_type='concept',
        ).first()

        # 2026-02-27: Get or create progress
        progress, _ = StudentStoryProgress.objects.get_or_create(student=student)
        unlocked_ids = list(progress.unlocked_scene_ids or [])

        if concept_scene and concept_scene.scene_id not in unlocked_ids:
            unlocked_ids.append(concept_scene.scene_id)
            newly_unlocked.append({
                'scene_id': concept_scene.scene_id,
                'scene_type': concept_scene.scene_type,
                'narrative_text': concept_scene.narrative_text,
                'subject': concept_scene.subject,
                'land': SUBJECT_LANDS.get(subject, subject),
            })

        # 2026-02-27: 5★ unlocks bonus scene at this concept_slot
        if stars == 5:
            bonus_scene = NarrativeScene.objects.filter(
                subject=subject,
                concept_slot=concept_slot,
                scene_type='bonus',
            ).first()
            if bonus_scene and bonus_scene.scene_id not in unlocked_ids:
                unlocked_ids.append(bonus_scene.scene_id)
                newly_unlocked.append({
                    'scene_id': bonus_scene.scene_id,
                    'scene_type': bonus_scene.scene_type,
                    'narrative_text': bonus_scene.narrative_text,
                    'bonus_text': bonus_scene.bonus_text,
                    'subject': bonus_scene.subject,
                    'land': SUBJECT_LANDS.get(subject, subject),
                })

        # 2026-02-27: Update quest counter and timestamp before finale check
        if newly_unlocked:
            progress.total_quests_completed += len(newly_unlocked)
            progress.last_unlocked_at = timezone.now()

        # 2026-02-27: Every 10th mastery in this subject → chapter_finale
        # Checked on mastered_count (not quest count) so it fires even without concept scene
        if mastered_count > 0 and mastered_count % 10 == 0:
            finale_scene = NarrativeScene.objects.filter(
                subject=subject,
                scene_type='chapter_finale',
            ).first()
            if finale_scene and finale_scene.scene_id not in unlocked_ids:
                unlocked_ids.append(finale_scene.scene_id)
                newly_unlocked.append({
                    'scene_id': finale_scene.scene_id,
                    'scene_type': finale_scene.scene_type,
                    'narrative_text': finale_scene.narrative_text,
                    'subject': finale_scene.subject,
                    'land': SUBJECT_LANDS.get(subject, subject),
                })
                # 2026-02-27: Finale is an additional quest
                if not progress.last_unlocked_at:
                    progress.last_unlocked_at = timezone.now()
                progress.total_quests_completed += 1

        progress.unlocked_scene_ids = unlocked_ids
        progress.save()

        if newly_unlocked:
            logger.info(
                f"Story: Student {student.id} unlocked {len(newly_unlocked)} scene(s) "
                f"in {subject} (slot {concept_slot}, {stars}★)"
            )

        return newly_unlocked

    @classmethod
    def get_progress(cls, student):
        """
        2026-02-27: Get student's story progress summary.

        Args:
            student: Student model instance.

        Returns:
            dict: total_quests, current_land, recent_scenes (last 3).
        """
        progress, _ = StudentStoryProgress.objects.get_or_create(student=student)
        unlocked_ids = progress.unlocked_scene_ids or []

        # 2026-02-27: Get last 3 unlocked scenes
        recent_ids = unlocked_ids[-3:] if len(unlocked_ids) >= 3 else unlocked_ids
        recent_scenes = []
        for scene_id in reversed(recent_ids):
            scene = NarrativeScene.objects.filter(scene_id=scene_id).first()
            if scene:
                recent_scenes.append({
                    'scene_id': scene.scene_id,
                    'scene_type': scene.scene_type,
                    'narrative_text': scene.narrative_text,
                    'subject': scene.subject,
                    'land': SUBJECT_LANDS.get(scene.subject, scene.subject),
                })

        # 2026-02-27: Current land — based on most recent scene's subject
        current_land = None
        if unlocked_ids:
            last_scene = NarrativeScene.objects.filter(scene_id=unlocked_ids[-1]).first()
            if last_scene:
                current_land = SUBJECT_LANDS.get(last_scene.subject, last_scene.subject)

        return {
            'total_quests_completed': progress.total_quests_completed,
            'total_scenes_unlocked': len(unlocked_ids),
            'current_land': current_land,
            'recent_scenes': recent_scenes,
            'last_unlocked_at': (
                progress.last_unlocked_at.isoformat()
                if progress.last_unlocked_at else None
            ),
        }

    @classmethod
    def get_scene(cls, scene_id):
        """
        2026-02-27: Get detail for a specific narrative scene.

        Args:
            scene_id: str scene identifier slug.

        Returns:
            dict or None: Scene detail dict, or None if not found.
        """
        scene = NarrativeScene.objects.filter(scene_id=scene_id).first()
        if not scene:
            return None
        return {
            'scene_id': scene.scene_id,
            'subject': scene.subject,
            'scene_type': scene.scene_type,
            'concept_slot': scene.concept_slot,
            'narrative_text': scene.narrative_text,
            'bonus_text': scene.bonus_text,
            'illustration_ref': scene.illustration_ref,
            'land': SUBJECT_LANDS.get(scene.subject, scene.subject),
        }
