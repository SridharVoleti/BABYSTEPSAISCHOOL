"""
2026-02-20: Initial migration for Gamification Engine (BS-GAM).

Creates: Badge, StudentBadge, CoinLedger, StudentGameProfile, FreezeLedger.
"""

import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-20: Initial schema for gamification service."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-02-20: Student model
    ]

    operations = [
        # ── Badge catalog ────────────────────────────────────────────────────
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('badge_id', models.SlugField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('icon', models.CharField(max_length=10)),
                ('category', models.CharField(
                    choices=[
                        ('streak', 'Streak'),
                        ('stars', 'Stars'),
                        ('vocabulary', 'Vocabulary'),
                        ('reading', 'Reading'),
                        ('learning', 'Learning'),
                    ],
                    max_length=20,
                )),
                ('rarity', models.CharField(
                    choices=[
                        ('common', 'Common'),
                        ('uncommon', 'Uncommon'),
                        ('rare', 'Rare'),
                        ('epic', 'Epic'),
                    ],
                    default='common',
                    max_length=20,
                )),
            ],
            options={
                'ordering': ['category', 'rarity', 'name'],
            },
        ),

        # ── StudentBadge (earned badges) ─────────────────────────────────────
        migrations.CreateModel(
            name='StudentBadge',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='badges',
                    to='auth_service.student',
                )),
                ('badge', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='student_badges',
                    to='gamification_service.badge',
                )),
                ('earned_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-earned_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='studentbadge',
            constraint=models.UniqueConstraint(
                fields=['student', 'badge'],
                name='unique_student_badge',
            ),
        ),

        # ── CoinLedger ───────────────────────────────────────────────────────
        migrations.CreateModel(
            name='CoinLedger',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='coin_ledger',
                    to='auth_service.student',
                )),
                ('amount', models.IntegerField()),
                ('event_type', models.CharField(
                    choices=[
                        ('lesson_complete', 'Lesson Complete'),
                        ('practice_stars', 'Practice Stars'),
                        ('vocab_session', 'Vocabulary Session'),
                        ('read_along', 'Read-Along'),
                        ('badge_bonus', 'Badge Bonus'),
                        ('freeze_spend', 'Freeze Spend'),
                        ('other', 'Other'),
                    ],
                    max_length=30,
                )),
                ('reference_id', models.UUIDField(blank=True, null=True)),
                ('description', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),

        # ── StudentGameProfile ───────────────────────────────────────────────
        migrations.CreateModel(
            name='StudentGameProfile',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='game_profile',
                    to='auth_service.student',
                )),
                ('coin_balance', models.IntegerField(default=0)),
                ('total_stars_earned', models.IntegerField(default=0)),
                ('freezes_available', models.IntegerField(default=0)),
                ('total_badges_earned', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),

        # ── FreezeLedger ─────────────────────────────────────────────────────
        migrations.CreateModel(
            name='FreezeLedger',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='freeze_ledger',
                    to='auth_service.student',
                )),
                ('event_type', models.CharField(
                    choices=[
                        ('earned', 'Earned'),
                        ('applied', 'Applied'),
                    ],
                    max_length=10,
                )),
                ('reason', models.CharField(max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
