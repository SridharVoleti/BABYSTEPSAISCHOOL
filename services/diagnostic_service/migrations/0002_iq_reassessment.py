# 2026-02-27: Migration to add IQReassessmentWindow and IQReassessmentEvent models.

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-27: Add rolling IQ reassessment window and event tracking (BS-DIA-003)."""

    dependencies = [
        ('auth_service', '0001_initial'),
        ('diagnostic_service', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IQReassessmentWindow',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('window_number', models.IntegerField()),
                ('avg_stars', models.FloatField(default=0.0)),
                ('avg_reteaching', models.FloatField(default=0.0)),
                ('avg_comprehension', models.FloatField(default=0.0)),
                ('outcome', models.CharField(
                    choices=[
                        ('upgrade', 'Upgrade'),
                        ('downgrade', 'Downgrade'),
                        ('maintain', 'Maintain'),
                    ],
                    default='maintain',
                    max_length=20,
                )),
                ('level_before', models.CharField(
                    choices=[
                        ('foundation', 'Foundation'),
                        ('standard', 'Standard'),
                        ('advanced', 'Advanced'),
                    ],
                    max_length=20,
                )),
                ('level_after', models.CharField(
                    choices=[
                        ('foundation', 'Foundation'),
                        ('standard', 'Standard'),
                        ('advanced', 'Advanced'),
                    ],
                    max_length=20,
                )),
                ('concepts_in_window', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='iq_reassessment_windows',
                    to='auth_service.student',
                )),
            ],
            options={
                'ordering': ['-window_number'],
                'unique_together': {('student', 'window_number')},
            },
        ),
        migrations.CreateModel(
            name='IQReassessmentEvent',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False,
                    primary_key=True, serialize=False,
                )),
                ('old_level', models.CharField(
                    choices=[
                        ('foundation', 'Foundation'),
                        ('standard', 'Standard'),
                        ('advanced', 'Advanced'),
                    ],
                    max_length=20,
                )),
                ('new_level', models.CharField(
                    choices=[
                        ('foundation', 'Foundation'),
                        ('standard', 'Standard'),
                        ('advanced', 'Advanced'),
                    ],
                    max_length=20,
                )),
                ('direction', models.CharField(
                    choices=[
                        ('upgrade', 'Upgrade'),
                        ('downgrade', 'Downgrade'),
                    ],
                    max_length=20,
                )),
                ('triggering_window', models.IntegerField()),
                ('parent_notified', models.BooleanField(default=False)),
                ('parent_notified_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='iq_reassessment_events',
                    to='auth_service.student',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
