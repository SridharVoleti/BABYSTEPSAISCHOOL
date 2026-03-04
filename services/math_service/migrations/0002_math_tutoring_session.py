# 2026-03-02: Migration — add MathTutoringSession model (BS-AMT-001).
# Generated manually for the AI Math Tutor teaching phase.

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """2026-03-02: Adds MathTutoringSession table."""

    dependencies = [
        ('math_service', '0001_initial'),  # 2026-03-02: Depends on base migration
    ]

    operations = [
        migrations.CreateModel(
            name='MathTutoringSession',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4,
                    editable=False,
                    primary_key=True,
                    serialize=False,
                )),
                ('math_session', models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='tutoring',
                    to='math_service.mathsession',
                )),
                ('messages', models.JSONField(
                    default=list,
                    help_text='Ordered list of {role: tutor|student, text, ts} dicts',
                )),
                ('teaching_complete', models.BooleanField(
                    default=False,
                    help_text='Set True when student signals ready to practice',
                )),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'math_tutoring_session',
            },
        ),
    ]
