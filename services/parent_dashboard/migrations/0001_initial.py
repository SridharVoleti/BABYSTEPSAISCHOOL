"""
2026-02-19: Initial migration for parent_dashboard app.

Creates: ParentalControls table.
"""

import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-19: Create ParentalControls table."""

    initial = True  # 2026-02-19: First migration

    dependencies = [
        # 2026-02-19: Depends on Student model in auth_service
        ('auth_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ParentalControls',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('student', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='parental_controls',
                    to='auth_service.student',
                )),
                ('daily_time_limit_minutes', models.IntegerField(
                    default=120,
                    help_text='Daily time limit in minutes (15-480)',
                )),
                ('schedule_enabled', models.BooleanField(default=False)),
                ('schedule_start_time', models.TimeField(blank=True, null=True)),
                ('schedule_end_time', models.TimeField(blank=True, null=True)),
                ('ai_log_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Parental Controls',
                'verbose_name_plural': 'Parental Controls',
            },
        ),
    ]
