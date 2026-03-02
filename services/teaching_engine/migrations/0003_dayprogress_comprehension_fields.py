# Generated 2026-02-19: Add comprehension_score, weighted_star_rating to DayProgress (BS-CMP)

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-19: Add BS-CMP comprehension fields to DayProgress and update STATUS_CHOICES."""

    dependencies = [
        ('teaching_engine', '0002_mastery_practice_models'),  # 2026-02-19: Previous migration
    ]

    operations = [
        # 2026-02-19: Add comprehension_score field
        migrations.AddField(
            model_name='dayprogress',
            name='comprehension_score',
            field=models.FloatField(default=0.0),
        ),
        # 2026-02-19: Add weighted_star_rating field
        migrations.AddField(
            model_name='dayprogress',
            name='weighted_star_rating',
            field=models.IntegerField(
                default=0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
            ),
        ),
        # 2026-02-19: Update STATUS_CHOICES to include comprehension_check and day_complete
        migrations.AlterField(
            model_name='dayprogress',
            name='status',
            field=models.CharField(
                choices=[
                    ('not_started', 'Not Started'),
                    ('revision', 'In Revision'),
                    ('teaching', 'In Teaching'),
                    ('practice', 'In Practice'),
                    ('mastery_practice', 'Mastery Practice'),
                    ('comprehension_check', 'Comprehension Check'),
                    ('day_complete', 'Day Complete'),
                    ('completed', 'Completed'),
                ],
                default='not_started',
                max_length=20,
            ),
        ),
    ]
