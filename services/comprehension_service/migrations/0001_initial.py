# Generated 2026-02-19: Initial migration for ComprehensionEvaluation (BS-CMP)

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-19: Create ComprehensionEvaluation table."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-02-19: Student FK
        ('teaching_engine', '0001_initial'),  # 2026-02-19: TeachingLesson FK
    ]

    operations = [
        migrations.CreateModel(
            name='ComprehensionEvaluation',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('day_number', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(4),
                    ]
                )),
                ('student_text', models.TextField()),
                ('is_parroting', models.BooleanField(default=False)),
                ('score_understanding', models.IntegerField(default=0)),
                ('score_accuracy', models.IntegerField(default=0)),
                ('score_own_words', models.IntegerField(default=0)),
                ('score_depth', models.IntegerField(default=0)),
                ('score_clarity', models.IntegerField(default=0)),
                ('comprehension_score', models.FloatField(default=0.0)),
                ('llm_feedback', models.TextField(default='')),
                ('llm_error', models.BooleanField(default=False)),
                ('practice_stars', models.IntegerField(default=0)),
                ('application_score', models.FloatField(default=50.0)),
                ('retention_score', models.FloatField(default=50.0)),
                ('weighted_score', models.FloatField(default=0.0)),
                ('weighted_star_rating', models.IntegerField(
                    default=0,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(5),
                    ],
                )),
                ('attempt_number', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comprehension_evals',
                    to='auth_service.student',
                )),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comprehension_evals',
                    to='teaching_engine.teachinglesson',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='comprehensionevaluation',
            index=models.Index(
                fields=['student', 'lesson', 'day_number'],
                name='comprehensi_student_c2ed58_idx',
            ),
        ),
    ]
