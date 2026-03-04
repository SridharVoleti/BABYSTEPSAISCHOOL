"""
2026-03-04: Initial migration for pod_service (BS-POD + BS-MON).

Creates: Pod, PodEnrollment, StudentSession, AttentionEvent, MonitorAlert.
"""

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-03-04: Initial schema for pod management and monitoring."""

    initial = True  # 2026-03-04: First migration

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-03-04: Depends on Student model
    ]

    operations = [
        migrations.CreateModel(
            name='Pod',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(help_text='E.g. "Pod Alpha \u2013 Grade 6"', max_length=100)),
                ('grade', models.IntegerField(help_text='Grade level (1-12)')),
                ('subject_focus', models.CharField(blank=True, default='All', help_text='Subject focus, or "All" for multi-subject pods', max_length=100)),
                ('max_size', models.IntegerField(default=5)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['grade', 'name'],
            },
        ),
        migrations.CreateModel(
            name='PodEnrollment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('pod', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enrollments', to='pod_service.pod')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pod_enrollments', to='auth_service.student')),
                ('enrolled_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['enrolled_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='podenrollment',
            constraint=models.UniqueConstraint(fields=('pod', 'student'), name='unique_pod_student'),
        ),
        migrations.CreateModel(
            name='StudentSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='learning_sessions', to='auth_service.student')),
                ('pod_enrollment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='pod_service.podenrollment')),
                ('session_start', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_heartbeat', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('attention_score', models.FloatField(default=1.0, help_text='0.0=not focusing, 1.0=fully focused')),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-session_start'],
            },
        ),
        migrations.CreateModel(
            name='AttentionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attention_events', to='auth_service.student')),
                ('session', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='attention_events', to='pod_service.studentsession')),
                ('event_type', models.CharField(choices=[('not_visible', 'Face Not Visible'), ('not_looking', 'Not Looking at Screen'), ('sleeping', 'Appears to be Sleeping'), ('inactive', 'No Interaction (Inactive)')], max_length=30)),
                ('detected_at', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('ai_response', models.CharField(blank=True, default='', max_length=500)),
                ('escalated', models.BooleanField(default=False)),
                ('escalation_count', models.IntegerField(default=0)),
            ],
            options={
                'ordering': ['-detected_at'],
            },
        ),
        migrations.CreateModel(
            name='MonitorAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='monitor_alerts', to='auth_service.student')),
                ('alert_type', models.CharField(choices=[('parent_alert', 'Parent Alert (WhatsApp)'), ('monitor_flag', 'Monitor Flag (dashboard)'), ('help_request', 'Student Help Request')], max_length=30)),
                ('message', models.TextField()),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
