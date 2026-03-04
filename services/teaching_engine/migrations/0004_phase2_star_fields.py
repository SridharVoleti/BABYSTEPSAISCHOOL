# 2026-03-02: Add Phase 2 star components to DayProgress (BS-CMP-003)

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-03-02: Add read_along_score, self_explanation_score, phase2_star_rating to DayProgress."""

    dependencies = [
        ('teaching_engine', '0003_dayprogress_comprehension_fields'),  # 2026-03-02: Previous
    ]

    operations = [
        # 2026-03-02: Read-along overall_score (0.0–1.0) for this lesson+day
        migrations.AddField(
            model_name='dayprogress',
            name='read_along_score',
            field=models.FloatField(
                default=0.0,
                help_text='Best ReadAlongSession.overall_score (0.0-1.0) for this lesson+day',
            ),
        ),
        # 2026-03-02: Self-explanation comprehension mean (0–100) from ComprehensionEvaluation
        migrations.AddField(
            model_name='dayprogress',
            name='self_explanation_score',
            field=models.FloatField(
                default=0.0,
                help_text='ComprehensionEvaluation.comprehension_score mean (0-100)',
            ),
        ),
        # 2026-03-02: Phase 2 weighted star rating (0–5)
        migrations.AddField(
            model_name='dayprogress',
            name='phase2_star_rating',
            field=models.IntegerField(
                default=0,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(5),
                ],
                help_text='Phase 2 weighted composite star rating (0-5)',
            ),
        ),
        # 2026-03-02: Back-fill phase2_star_rating from existing mastery_star_rating
        migrations.RunSQL(
            sql=(
                "UPDATE teaching_engine_dayprogress "
                "SET phase2_star_rating = mastery_star_rating "
                "WHERE mastery_star_rating > 0"
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
