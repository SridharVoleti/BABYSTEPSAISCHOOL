"""
2026-02-27: Initial migration for Story Mode Service (BS-GAM-003).

Creates: NarrativeScene, StudentStoryProgress.
"""

import uuid  # 2026-02-27: UUID field defaults

import django.db.models.deletion  # 2026-02-27: Cascade behaviour

from django.db import migrations, models  # 2026-02-27: Migration primitives


class Migration(migrations.Migration):
    """2026-02-27: Initial schema for story_mode_service."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-02-27: Student model dependency
    ]

    operations = [
        # ── NarrativeScene catalog ────────────────────────────────────────────
        migrations.CreateModel(
            name='NarrativeScene',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('scene_id', models.SlugField(
                    max_length=80,
                    unique=True,
                )),
                ('subject', models.CharField(
                    max_length=50,
                )),
                ('scene_type', models.CharField(
                    choices=[
                        ('concept', 'Concept'),
                        ('bonus', 'Bonus'),
                        ('chapter_finale', 'Chapter Finale'),
                    ],
                    max_length=20,
                )),
                ('concept_slot', models.IntegerField()),
                ('narrative_text', models.TextField()),
                ('bonus_text', models.TextField(
                    blank=True,
                    default='',
                )),
                ('illustration_ref', models.CharField(
                    blank=True,
                    default='',
                    max_length=100,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['subject', 'concept_slot'],
            },
        ),

        # ── StudentStoryProgress ──────────────────────────────────────────────
        migrations.CreateModel(
            name='StudentStoryProgress',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='story_progress',
                    to='auth_service.student',
                )),
                ('total_quests_completed', models.IntegerField(default=0)),
                ('unlocked_scene_ids', models.JSONField(default=list)),
                ('last_unlocked_at', models.DateTimeField(
                    blank=True,
                    null=True,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
