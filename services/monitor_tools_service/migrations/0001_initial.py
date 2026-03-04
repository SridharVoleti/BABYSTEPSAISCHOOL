"""
2026-03-04: Initial migration for monitor_tools_service.

Creates GradeBookEntry, HomeworkAssignment, HomeworkSubmission, TimetableSlot.
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
        # ------------------------------------------------ GradeBookEntry
        migrations.CreateModel(
            name='GradeBookEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('subject', models.CharField(db_index=True, max_length=50)),
                ('term', models.CharField(choices=[('T1', 'Term 1'), ('T2', 'Term 2'), ('T3', 'Term 3')], max_length=2)),
                ('assessment_type', models.CharField(
                    choices=[('formative', 'Formative'), ('summative', 'Summative'), ('project', 'Project')],
                    default='formative', max_length=12,
                )),
                ('title', models.CharField(max_length=100)),
                ('score', models.FloatField()),
                ('max_score', models.FloatField(default=100.0)),
                ('letter_grade', models.CharField(blank=True, default='', max_length=3)),
                ('remarks', models.TextField(blank=True, default='')),
                ('date_recorded', models.DateField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    db_index=True, on_delete=django.db.models.deletion.CASCADE,
                    related_name='grade_entries', to='auth_service.student',
                )),
                ('recorded_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='grade_entries_recorded', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['-date_recorded', 'subject']},
        ),
        migrations.AddIndex(
            model_name='gradebookentry',
            index=models.Index(fields=['student', 'subject', 'term'], name='grade_student_subj_term_idx'),
        ),

        # ------------------------------------------------ HomeworkAssignment
        migrations.CreateModel(
            name='HomeworkAssignment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('grade', models.IntegerField(db_index=True)),
                ('subject', models.CharField(max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('due_date', models.DateField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('assigned_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='homework_assigned', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['due_date', 'subject']},
        ),

        # ------------------------------------------------ HomeworkSubmission
        migrations.CreateModel(
            name='HomeworkSubmission',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(
                    choices=[('pending', 'Pending'), ('done', 'Done'), ('missed', 'Missed')],
                    default='pending', max_length=10,
                )),
                ('note', models.TextField(blank=True, default='')),
                ('submitted_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('homework', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='submissions', to='monitor_tools_service.homeworkassignment',
                )),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='homework_submissions', to='auth_service.student',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterUniqueTogether(
            name='homeworksubmission',
            unique_together={('homework', 'student')},
        ),

        # ------------------------------------------------ TimetableSlot
        migrations.CreateModel(
            name='TimetableSlot',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('grade', models.IntegerField(db_index=True)),
                ('day_of_week', models.IntegerField(choices=[
                    (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'),
                    (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'),
                ])),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('subject', models.CharField(max_length=50)),
                ('teacher_name', models.CharField(blank=True, default='', max_length=100)),
                ('room', models.CharField(blank=True, default='', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(
                    null=True, on_delete=django.db.models.deletion.SET_NULL,
                    related_name='timetable_slots_created', to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={'ordering': ['grade', 'day_of_week', 'start_time']},
        ),
        migrations.AddIndex(
            model_name='timetableslot',
            index=models.Index(fields=['grade', 'day_of_week'], name='tt_grade_day_idx'),
        ),
    ]
