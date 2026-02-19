# 2026-02-19: Initial migration for Read-Along & Mimic Engine (BS-RAM)
# Creates Language and ReadAlongSession tables.

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-19: Create Language and ReadAlongSession tables."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-02-19: Student FK
        ('teaching_engine', '0001_initial'),  # 2026-02-19: TeachingLesson FK
    ]

    operations = [
        # 2026-02-19: Language table — admin-manageable language registry
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('bcp47_tag', models.CharField(max_length=10)),
                ('display_name', models.CharField(max_length=100)),
                ('script', models.CharField(max_length=30)),
                ('tts_rate', models.FloatField(default=0.85)),
                ('is_active', models.BooleanField(default=True)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['sort_order', 'name'],
            },
        ),
        # 2026-02-19: ReadAlongSession table — per-student attempt records
        migrations.CreateModel(
            name='ReadAlongSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('day_number', models.IntegerField(validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(4),
                ])),
                ('language', models.CharField(max_length=30)),
                ('bcp47_tag', models.CharField(max_length=10)),
                ('sentence_scores', models.JSONField(default=list)),
                ('overall_score', models.FloatField(default=0.0)),
                ('star_rating', models.IntegerField(
                    default=0,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(5),
                    ],
                )),
                ('sentences_attempted', models.IntegerField(default=0)),
                ('sentences_total', models.IntegerField(default=0)),
                ('attempt_number', models.IntegerField(default=1)),
                ('status', models.CharField(
                    choices=[
                        ('in_progress', 'In Progress'),
                        ('completed', 'Completed'),
                        ('abandoned', 'Abandoned'),
                    ],
                    default='in_progress',
                    max_length=20,
                )),
                ('time_spent_seconds', models.IntegerField(default=0)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='read_along_sessions',
                    to='auth_service.student',
                )),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='read_along_sessions',
                    to='teaching_engine.teachinglesson',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        # 2026-02-19: Unique constraint on ReadAlongSession
        migrations.AddConstraint(
            model_name='readalongSession'.lower(),
            constraint=models.UniqueConstraint(
                fields=['student', 'lesson', 'day_number', 'language', 'attempt_number'],
                name='unique_read_along_attempt',
            ),
        ),
    ]
