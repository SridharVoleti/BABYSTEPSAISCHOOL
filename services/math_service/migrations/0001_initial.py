"""
2026-03-02: Initial migration for Math Service (BS-MTH module).

Creates: MathLesson, MathSession, MathProblemAttempt.
"""

import uuid  # 2026-03-02: UUID defaults

import django.db.models.deletion  # 2026-03-02: CASCADE behaviour
import django.utils.timezone  # 2026-03-02: Timezone-aware timestamps

from django.db import migrations, models  # 2026-03-02: Migration primitives


class Migration(migrations.Migration):
    """2026-03-02: Initial schema for math_service."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-03-02: Student FK
    ]

    operations = [
        # ── MathLesson ────────────────────────────────────────────────────────
        migrations.CreateModel(
            name='MathLesson',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                )),
                ('lesson_id', models.CharField(
                    max_length=50, unique=True,
                    help_text='Unique lesson identifier, e.g. MATH1_W01',
                )),
                ('title', models.CharField(max_length=200)),
                ('class_number', models.IntegerField(
                    help_text='Class/grade number (1-12)',
                )),
                ('week_number', models.IntegerField(
                    help_text='Week number within the class curriculum',
                )),
                ('topic', models.CharField(max_length=200)),
                ('content_json_path', models.CharField(
                    max_length=300,
                    help_text='Relative path from project root to lesson JSON',
                )),
                ('status', models.CharField(
                    choices=[('draft', 'Draft'), ('published', 'Published')],
                    default='draft', max_length=20,
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['class_number', 'week_number'],
            },
        ),

        # ── MathSession ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='MathSession',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='math_sessions',
                    to='auth_service.student',
                )),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessions',
                    to='math_service.mathlesson',
                )),
                ('day_number', models.IntegerField(
                    help_text='Day number within the lesson (1-4)',
                )),
                ('iq_level', models.CharField(
                    choices=[
                        ('foundation', 'Foundation'),
                        ('standard', 'Standard'),
                        ('advanced', 'Advanced'),
                    ],
                    default='standard', max_length=20,
                )),
                ('status', models.CharField(
                    choices=[('active', 'Active'), ('completed', 'Completed')],
                    default='active', max_length=20,
                )),
                ('total_problems', models.IntegerField(default=0)),
                ('problems_correct', models.IntegerField(default=0)),
                ('star_rating', models.IntegerField(
                    blank=True, null=True,
                    help_text='Star rating 0-5, set when session completes',
                )),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),

        # ── MathProblemAttempt ────────────────────────────────────────────────
        migrations.CreateModel(
            name='MathProblemAttempt',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False,
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attempts',
                    to='math_service.mathsession',
                )),
                ('problem_id', models.CharField(
                    max_length=100,
                    help_text='Problem identifier from the JSON content file',
                )),
                ('problem_type', models.CharField(
                    max_length=50,
                    help_text='Problem type: mcq, numeric_fill, word_problem',
                )),
                ('student_answer', models.TextField()),
                ('is_correct', models.BooleanField(default=False)),
                ('hints_used', models.IntegerField(default=0)),
                ('feedback', models.TextField(blank=True, default='')),
                ('time_taken_seconds', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
    ]
