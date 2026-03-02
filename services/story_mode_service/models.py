"""
2026-02-27: Database models for Story Mode Service (BS-GAM-003).

Defines the narrative scene catalog and per-student story progress
tracking. Scenes are unlocked as students master learning concepts,
building a personalised educational story journey.
"""

import uuid  # 2026-02-27: UUID primary keys

from django.db import models  # 2026-02-27: Django ORM

from services.auth_service.models import Student  # 2026-02-27: Student profile


class NarrativeScene(models.Model):
    """
    2026-02-27: Master catalog of all narrative scenes in the story mode.

    Each scene corresponds to a concept milestone in a subject.
    Scenes are seeded via migration 0002_seed_scenes and can be
    extended through Django admin.
    """

    SCENE_TYPE_CHOICES = [  # 2026-02-27: Narrative scene categories
        ('concept', 'Concept'),
        ('bonus', 'Bonus'),
        ('chapter_finale', 'Chapter Finale'),
    ]

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    scene_id = models.SlugField(  # 2026-02-27: Unique slug, e.g. 'english_q001'
        max_length=80, unique=True
    )
    subject = models.CharField(  # 2026-02-27: Subject area
        max_length=50
    )
    scene_type = models.CharField(  # 2026-02-27: Type of scene
        max_length=20, choices=SCENE_TYPE_CHOICES
    )
    concept_slot = models.IntegerField(  # 2026-02-27: 1-based per-subject sequence
    )
    narrative_text = models.TextField()  # 2026-02-27: 2-3 sentence story narrative
    bonus_text = models.TextField(  # 2026-02-27: Extra text for 5-star bonus scenes
        blank=True, default=''
    )
    illustration_ref = models.CharField(  # 2026-02-27: Optional illustration asset ref
        max_length=100, blank=True, default=''
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Creation timestamp

    class Meta:
        """2026-02-27: NarrativeScene model metadata."""

        ordering = ['subject', 'concept_slot']  # 2026-02-27: Natural reading order

    def __str__(self):
        """2026-02-27: String representation showing subject, scene id and type."""
        return f"{self.subject} | {self.scene_id} ({self.scene_type})"


class StudentStoryProgress(models.Model):
    """
    2026-02-27: Per-student record of story progress and unlocked scenes.

    Tracks which narrative scenes a student has unlocked, the total number
    of quests completed, and when the last unlock occurred. One record per
    student (OneToOne).
    """

    id = models.UUIDField(  # 2026-02-27: UUID primary key
        primary_key=True, default=uuid.uuid4, editable=False
    )
    student = models.OneToOneField(  # 2026-02-27: One progress record per student
        Student,
        on_delete=models.CASCADE,
        related_name='story_progress',
    )
    total_quests_completed = models.IntegerField(  # 2026-02-27: Cumulative quest count
        default=0
    )
    unlocked_scene_ids = models.JSONField(  # 2026-02-27: Ordered list of unlocked scene slugs
        default=list
    )
    last_unlocked_at = models.DateTimeField(  # 2026-02-27: Timestamp of latest unlock
        null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # 2026-02-27: Record creation
    updated_at = models.DateTimeField(auto_now=True)  # 2026-02-27: Last modification

    def __str__(self):
        """2026-02-27: String representation showing student name and quest count."""
        return f"{self.student.full_name} | {self.total_quests_completed} quests"
