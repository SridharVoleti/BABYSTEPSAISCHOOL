"""
2026-02-27: Initial migration for Spaced Repetition Service (BS-SPC).

Creates: SpacedRepetitionRecord, ReviewSession, ReviewResponse, PacingRecord.
"""

import uuid  # 2026-02-27: UUID for primary keys
import django.db.models.deletion  # 2026-02-27: FK deletion behaviour
from django.db import migrations, models  # 2026-02-27: Migration primitives


class Migration(migrations.Migration):
    """2026-02-27: Initial schema for spaced repetition service."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-02-27: Student model
        ('teaching_engine', '0001_initial'),  # 2026-02-27: ConceptMastery model
    ]

    operations = [
        # ── ReviewSession ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='ReviewSession',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='review_sessions',
                    to='auth_service.student',
                )),
                ('status', models.CharField(
                    choices=[
                        ('in_progress', 'In Progress'),
                        ('completed', 'Completed'),
                    ],
                    default='in_progress',
                    max_length=20,
                )),
                ('concepts_reviewed', models.IntegerField(default=0)),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],  # 2026-02-27: Most recent first
            },
        ),

        # ── SpacedRepetitionRecord ────────────────────────────────────────────
        migrations.CreateModel(
            name='SpacedRepetitionRecord',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='spc_records',
                    to='auth_service.student',
                )),
                ('mastery', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='spc_record',
                    to='teaching_engine.conceptmastery',
                )),
                ('leitner_box', models.IntegerField(default=1)),
                ('next_review_date', models.DateField()),
                ('last_reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('consecutive_5star_reviews', models.IntegerField(default=0)),
                ('phase', models.CharField(
                    choices=[
                        ('spaced_repetition', 'Spaced Repetition'),
                        ('maintenance', 'Maintenance'),
                    ],
                    default='spaced_repetition',
                    max_length=20,
                )),
                ('review_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['next_review_date'],  # 2026-02-27: Soonest due first
            },
        ),
        migrations.AlterUniqueTogether(
            name='spacedrepetitionrecord',
            unique_together={('student', 'mastery')},
        ),

        # ── ReviewResponse ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='ReviewResponse',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='responses',
                    to='spaced_repetition_service.reviewsession',
                )),
                ('mastery', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='review_responses',
                    to='teaching_engine.conceptmastery',
                )),
                ('stars_awarded', models.IntegerField()),
                ('explanation_seconds', models.IntegerField(default=0)),
                ('outcome', models.CharField(
                    choices=[
                        ('advanced', 'Advanced'),
                        ('reset', 'Reset'),
                    ],
                    max_length=10,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['created_at'],  # 2026-02-27: Chronological order
            },
        ),

        # ── PacingRecord ──────────────────────────────────────────────────────
        migrations.CreateModel(
            name='PacingRecord',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='pacing_record',
                    to='auth_service.student',
                )),
                ('academic_year_start', models.DateField()),
                ('intensive_end_date', models.DateField()),
                ('total_concepts', models.IntegerField(default=0)),
                ('daily_target', models.IntegerField(default=1)),
                ('iq_adjustment_factor', models.FloatField(default=1.0)),
                ('phase', models.CharField(
                    choices=[
                        ('intensive', 'Intensive'),
                        ('spaced_repetition', 'Spaced Repetition'),
                    ],
                    default='intensive',
                    max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
