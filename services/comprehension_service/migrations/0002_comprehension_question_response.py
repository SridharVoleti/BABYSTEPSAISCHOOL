# Generated 2026-02-21: Add ComprehensionQuestionResponse model (BS-CMP marks-based)

import django.core.validators
import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-21: Add ComprehensionQuestionResponse table for per-question articulation."""

    dependencies = [
        ('comprehension_service', '0001_initial'),  # 2026-02-21: Previous migration
        ('auth_service', '0001_initial'),  # 2026-02-21: Student FK
        ('teaching_engine', '0001_initial'),  # 2026-02-21: TeachingLesson FK
    ]

    operations = [
        migrations.CreateModel(
            name='ComprehensionQuestionResponse',
            fields=[
                ('id', models.UUIDField(
                    default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                )),
                ('day_number', models.IntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(4),
                    ]
                )),
                ('question_id', models.CharField(max_length=50)),
                ('question_text', models.TextField()),
                ('marks_available', models.IntegerField()),
                ('student_text', models.TextField()),
                ('input_method', models.CharField(
                    choices=[('typed', 'Typed'), ('spoken', 'Spoken')],
                    default='typed',
                    max_length=10,
                )),
                ('key_points_covered', models.JSONField(default=list)),
                ('marks_awarded', models.IntegerField(default=0)),
                ('llm_feedback', models.TextField(default='')),
                ('llm_error', models.BooleanField(default=False)),
                ('attempt_number', models.IntegerField(default=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('student', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comprehension_question_responses',
                    to='auth_service.student',
                )),
                ('lesson', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comprehension_question_responses',
                    to='teaching_engine.teachinglesson',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='comprehensionquestionresponse',
            index=models.Index(
                fields=['student', 'lesson', 'day_number', 'question_id'],
                name='comprehensi_student_qid_idx',
            ),
        ),
    ]
