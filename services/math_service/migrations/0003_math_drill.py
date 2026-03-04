# 2026-03-03: Migration — add MathDrillSession and MathDrillAttempt models (AMT-APE-005).
# Manual migration for Mental Maths Drills feature.

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """2026-03-03: Adds MathDrillSession and MathDrillAttempt tables."""

    dependencies = [
        ('math_service', '0002_math_tutoring_session'),  # 2026-03-03: Depends on tutoring migration
        ('auth_service', '0001_initial'),  # 2026-03-03: Student FK
    ]

    operations = [
        migrations.CreateModel(
            name='MathDrillSession',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='drill_sessions',
                    to='auth_service.student',
                )),
                ('drill_type', models.CharField(
                    choices=[
                        ('tables', 'Multiplication Tables'),
                        ('squares', 'Squares'),
                        ('cubes', 'Cubes'),
                    ],
                    max_length=20,
                )),
                ('number_range_min', models.IntegerField(default=1)),
                ('number_range_max', models.IntegerField(default=12)),
                ('time_limit_seconds', models.IntegerField()),
                ('total_questions', models.IntegerField(default=10)),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('completed', 'Completed'),
                        ('expired', 'Expired'),
                    ],
                    default='active',
                    max_length=20,
                )),
                ('score', models.IntegerField(default=0)),
                ('star_rating', models.IntegerField(
                    blank=True,
                    help_text='Star rating 0-5, set when session completes or expires',
                    null=True,
                )),
                ('questions', models.JSONField(
                    default=list,
                    help_text='Generated questions list with correct_answer (server-side only)',
                )),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='MathDrillAttempt',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts',
                    to='math_service.mathdrillsession',
                )),
                ('question_index', models.IntegerField(
                    help_text='0-based index of the question in the session questions list',
                )),
                ('student_answer', models.CharField(max_length=50)),
                ('is_correct', models.BooleanField(default=False)),
                ('response_time_ms', models.IntegerField(
                    blank=True,
                    help_text='Time taken to answer in milliseconds (optional)',
                    null=True,
                )),
                ('answered_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['answered_at'],
                'unique_together': {('session', 'question_index')},
            },
        ),
    ]
