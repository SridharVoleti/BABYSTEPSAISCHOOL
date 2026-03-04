"""
2026-03-02: Initial migration for Language Stages Service (BS-LNG-005).

Creates: ConversationScenario, ConversationSession, ConversationTurn,
         StudentConversationProgress.
"""

import uuid  # 2026-03-02: UUID field defaults

import django.core.validators  # 2026-03-02: Validators
import django.db.models.deletion  # 2026-03-02: Cascade behaviour

from django.db import migrations, models  # 2026-03-02: Migration primitives


class Migration(migrations.Migration):
    """2026-03-02: Initial schema for language_stages_service."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-03-02: Student FK
        ('read_along_service', '0001_initial'),  # 2026-03-02: Language FK
    ]

    operations = [
        # ── ConversationScenario ──────────────────────────────────────────────
        migrations.CreateModel(
            name='ConversationScenario',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('scenario_number', models.IntegerField(
                    unique=True,
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(20),
                    ],
                    help_text='Sequence number 1-20; determines unlock order',
                )),
                ('title', models.CharField(max_length=120)),
                ('ai_persona', models.CharField(
                    max_length=80,
                    help_text='Role the AI plays in this scenario',
                )),
                ('context_description', models.TextField(
                    help_text='Paragraph describing the scenario context sent to LLM',
                )),
                ('opening_prompt_template', models.TextField(
                    help_text='Template for AI opening turn. Use {target_language} placeholder.',
                )),
                ('difficulty', models.CharField(
                    choices=[
                        ('beginner', 'Beginner'),
                        ('intermediate', 'Intermediate'),
                        ('advanced', 'Advanced'),
                    ],
                    default='beginner',
                    max_length=20,
                )),
                ('min_turns', models.IntegerField(
                    default=4,
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('max_turns', models.IntegerField(
                    default=10,
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('unlock_after_scenario', models.IntegerField(
                    blank=True,
                    null=True,
                    help_text='Unlocks after scenario N is completed at >= 2 stars. Null = always unlocked.',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['scenario_number'],
            },
        ),

        # ── ConversationSession ───────────────────────────────────────────────
        migrations.CreateModel(
            name='ConversationSession',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='conversation_sessions',
                    to='auth_service.student',
                )),
                ('language', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='conversation_sessions',
                    to='read_along_service.language',
                )),
                ('scenario', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='sessions',
                    to='language_stages_service.conversationscenario',
                )),
                ('status', models.CharField(
                    choices=[
                        ('in_progress', 'In Progress'),
                        ('completed', 'Completed'),
                        ('abandoned', 'Abandoned'),
                    ],
                    default='in_progress',
                    max_length=20,
                )),
                ('complexity_level', models.CharField(
                    choices=[
                        ('beginner', 'Beginner'),
                        ('intermediate', 'Intermediate'),
                        ('advanced', 'Advanced'),
                    ],
                    default='beginner',
                    max_length=20,
                )),
                ('turn_count', models.IntegerField(default=0)),
                ('fluency_star_rating', models.IntegerField(
                    default=0,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(5),
                    ],
                )),
                ('started_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-started_at'],
            },
        ),

        # ── ConversationTurn ──────────────────────────────────────────────────
        migrations.CreateModel(
            name='ConversationTurn',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('session', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='turns',
                    to='language_stages_service.conversationsession',
                )),
                ('turn_number', models.IntegerField(
                    validators=[django.core.validators.MinValueValidator(1)],
                )),
                ('role', models.CharField(
                    choices=[('student', 'Student'), ('ai', 'AI')],
                    max_length=10,
                )),
                ('text', models.TextField()),
                ('turn_quality_score', models.FloatField(
                    blank=True,
                    null=True,
                    help_text='LLM-evaluated quality score (0.0-1.0) for student turns only',
                )),
                ('recast_applied', models.BooleanField(default=False)),
                ('response_time_seconds', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['turn_number'],
            },
        ),
        migrations.AddConstraint(
            model_name='conversationturn',
            constraint=models.UniqueConstraint(
                fields=['session', 'turn_number'],
                name='unique_session_turn_number',
            ),
        ),

        # ── StudentConversationProgress ───────────────────────────────────────
        migrations.CreateModel(
            name='StudentConversationProgress',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='conversation_progress',
                    to='auth_service.student',
                )),
                ('language', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='student_conversation_progress',
                    to='read_along_service.language',
                )),
                ('scenarios_completed', models.IntegerField(default=0)),
                ('best_star_by_scenario', models.JSONField(
                    default=dict,
                    blank=True,
                    help_text='Maps scenario_number → best fluency_star_rating',
                )),
                ('total_turns', models.IntegerField(default=0)),
                ('current_streak_days', models.IntegerField(default=0)),
                ('last_session_date', models.DateField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='studentconversationprogress',
            constraint=models.UniqueConstraint(
                fields=['student', 'language'],
                name='unique_student_language_conversation',
            ),
        ),
    ]
