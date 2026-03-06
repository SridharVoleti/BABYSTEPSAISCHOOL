"""
2026-03-06: Initial migration for mentor_dashboard_service (BS-MNT).

Creates:
  - MentorAssignment (mentor ↔ student assignments)
  - ComprehensionReview (mentor override scores)
  - WeeklySummary (AI-generated weekly narrative)
"""

import uuid  # 2026-03-06: UUID field default

import django.core.validators  # 2026-03-06: Validators
import django.db.models.deletion  # 2026-03-06: CASCADE etc.
from django.conf import settings  # 2026-03-06: AUTH_USER_MODEL
from django.db import migrations, models  # 2026-03-06: Migration framework


class Migration(migrations.Migration):
    """2026-03-06: Initial schema migration."""

    initial = True  # 2026-03-06: First migration for this app

    dependencies = [
        # 2026-03-06: Depends on auth_service for Student FK
        ('auth_service', '0001_initial'),
        # 2026-03-06: Depends on comprehension_service for ComprehensionQuestionResponse FK
        ('comprehension_service', '0002_comprehension_question_response'),
        # 2026-03-06: Depends on Django's built-in User model
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 2026-03-06: MentorAssignment table
        migrations.CreateModel(
            name='MentorAssignment',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('assigned_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('mentor', models.ForeignKey(
                    limit_choices_to={'is_staff': True},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mentor_assignments',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mentor_assignments',
                    to='auth_service.student',
                )),
            ],
            options={
                'ordering': ['-assigned_at'],
                'unique_together': {('mentor', 'student')},
            },
        ),
        # 2026-03-06: ComprehensionReview table
        migrations.CreateModel(
            name='ComprehensionReview',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('mentor_score', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(5),
                    ]
                )),
                ('mentor_notes', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(auto_now_add=True)),
                ('response', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mentor_reviews',
                    to='comprehension_service.comprehensionquestionresponse',
                )),
                ('reviewed_by', models.ForeignKey(
                    limit_choices_to={'is_staff': True},
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comprehension_reviews',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-reviewed_at'],
                'unique_together': {('response', 'reviewed_by')},
            },
        ),
        # 2026-03-06: WeeklySummary table
        migrations.CreateModel(
            name='WeeklySummary',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('week_start', models.DateField()),
                ('summary_text', models.TextField()),
                ('strengths', models.JSONField(default=list)),
                ('areas_for_improvement', models.JSONField(default=list)),
                ('lessons_completed', models.IntegerField(default=0)),
                ('avg_star_rating', models.FloatField(default=0.0)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='mentor_weekly_summaries',
                    to='auth_service.student',
                )),
                ('generated_by', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='generated_summaries',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-week_start'],
                'unique_together': {('student', 'week_start')},
            },
        ),
    ]
