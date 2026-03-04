"""
2026-03-04: Initial migration for attendance_service (BS-ATT).

Creates AttendanceRecord table with all fields and indexes.
"""

import uuid  # 2026-03-04: UUID default

import django.db.models.deletion  # 2026-03-04: FK deletion behaviour
from django.db import migrations, models  # 2026-03-04: Migration framework


class Migration(migrations.Migration):
    """2026-03-04: Initial schema for attendance_service."""

    initial = True  # 2026-03-04: First migration

    dependencies = [
        ('auth_service', '0001_initial'),  # 2026-03-04: Student FK dependency
    ]

    operations = [
        migrations.CreateModel(
            name='AttendanceRecord',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('date', models.DateField(db_index=True)),
                ('status', models.CharField(
                    choices=[
                        ('present', 'Present'),
                        ('absent', 'Absent'),
                        ('late', 'Late'),
                        ('excused', 'Excused'),
                    ],
                    default='present',
                    max_length=10,
                )),
                ('check_in_time', models.DateTimeField(blank=True, null=True)),
                ('check_out_time', models.DateTimeField(blank=True, null=True)),
                ('session_duration_minutes', models.IntegerField(blank=True, null=True)),
                ('recorded_by', models.CharField(
                    choices=[
                        ('auto', 'Auto (login)'),
                        ('monitor', 'Monitor'),
                        ('system', 'System'),
                    ],
                    default='auto',
                    max_length=10,
                )),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attendance_records',
                    to='auth_service.student',
                    db_index=True,
                )),
            ],
            options={
                'ordering': ['-date', 'student'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='attendancerecord',
            unique_together={('student', 'date')},
        ),
        migrations.AddIndex(
            model_name='attendancerecord',
            index=models.Index(fields=['date', 'student'], name='att_date_student_idx'),
        ),
    ]
