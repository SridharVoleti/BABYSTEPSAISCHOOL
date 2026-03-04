"""
2026-03-04: Initial migration for communication_service.

Creates MessageThread, Message, Announcement, WeeklyProgressReport, TermReport.
"""

import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-03-04: Initial schema."""

    initial = True

    dependencies = [
        ('auth_service', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # ------------------------------------------------ MessageThread
        migrations.CreateModel(
            name='MessageThread',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(blank=True, default='', max_length=200)),
                ('is_closed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='message_threads', to='auth_service.student',
                )),
                ('parent', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='message_threads', to='auth_service.parent',
                )),
                ('monitor', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='message_threads', to=settings.AUTH_USER_MODEL,
                    limit_choices_to={'is_staff': True},
                )),
            ],
            options={'ordering': ['-updated_at']},
        ),
        # ------------------------------------------------ Message
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('sender_type', models.CharField(
                    choices=[('parent', 'Parent'), ('monitor', 'Monitor')], max_length=10
                )),
                ('body', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('thread', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='messages', to='communication_service.messagethread',
                )),
            ],
            options={'ordering': ['created_at']},
        ),
        # ------------------------------------------------ Announcement
        migrations.CreateModel(
            name='Announcement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('body', models.TextField()),
                ('audience', models.CharField(
                    choices=[('all', 'All'), ('grade', 'Specific Grade'), ('parents', 'Parents Only')],
                    default='all', max_length=10,
                )),
                ('grades', models.JSONField(blank=True, default=list)),
                ('priority', models.CharField(
                    choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High')],
                    default='normal', max_length=10,
                )),
                ('is_active', models.BooleanField(default=True)),
                ('publish_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='announcements', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        # ------------------------------------------------ WeeklyProgressReport
        migrations.CreateModel(
            name='WeeklyProgressReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('week_start', models.DateField()),
                ('week_end', models.DateField()),
                ('summary_text', models.TextField()),
                ('highlights', models.JSONField(default=list)),
                ('areas_of_improvement', models.JSONField(default=list)),
                ('attendance_days', models.IntegerField(default=0)),
                ('lessons_completed', models.IntegerField(default=0)),
                ('avg_star_rating', models.FloatField(blank=True, null=True)),
                ('delivered_whatsapp', models.BooleanField(default=False)),
                ('delivered_email', models.BooleanField(default=False)),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='weekly_reports', to='auth_service.student',
                )),
            ],
            options={'ordering': ['-week_start']},
        ),
        migrations.AlterUniqueTogether(
            name='weeklyprogressreport',
            unique_together={('student', 'week_start')},
        ),
        # ------------------------------------------------ TermReport
        migrations.CreateModel(
            name='TermReport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('academic_year', models.CharField(max_length=9)),
                ('term', models.CharField(
                    choices=[('T1', 'Term 1'), ('T2', 'Term 2'), ('T3', 'Term 3')], max_length=2
                )),
                ('report_data', models.JSONField()),
                ('generated_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='term_reports', to='auth_service.student',
                )),
                ('generated_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='term_reports_generated', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-generated_at']},
        ),
        migrations.AlterUniqueTogether(
            name='termreport',
            unique_together={('student', 'academic_year', 'term')},
        ),
    ]
