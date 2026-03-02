"""
2026-02-27: Migration adding weekly_stars to StudentGameProfile
and creating WeeklyLeaderboardSnapshot model (BS-GAM-005).
"""

import uuid
import django.db.models.deletion
from django.db import migrations, models
from django.db.models import Index


class Migration(migrations.Migration):
    """2026-02-27: Leaderboard schema additions."""

    dependencies = [
        ('gamification_service', '0002_seed_badges'),  # 2026-02-27: After badge seed
        ('auth_service', '0001_initial'),  # 2026-02-27: Student model dependency
    ]

    operations = [
        # 2026-02-27: Add weekly_stars field to StudentGameProfile
        migrations.AddField(
            model_name='studentgameprofile',
            name='weekly_stars',
            field=models.IntegerField(default=0),
        ),

        # 2026-02-27: Create WeeklyLeaderboardSnapshot model
        migrations.CreateModel(
            name='WeeklyLeaderboardSnapshot',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='leaderboard_snapshots',
                    to='auth_service.student',
                )),
                ('grade', models.IntegerField()),
                ('stars_this_week', models.IntegerField(default=0)),
                ('week_start', models.DateField()),
                ('display_name', models.CharField(max_length=150)),
            ],
            options={
                'ordering': ['-week_start', '-stars_this_week'],
            },
        ),

        # 2026-02-27: Unique constraint per (student, week)
        migrations.AlterUniqueTogether(
            name='weeklyleaderboardsnapshot',
            unique_together={('student', 'week_start')},
        ),

        # 2026-02-27: Index for fast class board queries (grade + week_start)
        migrations.AddIndex(
            model_name='weeklyleaderboardsnapshot',
            index=models.Index(fields=['grade', 'week_start'], name='lb_grade_week_idx'),
        ),
    ]
