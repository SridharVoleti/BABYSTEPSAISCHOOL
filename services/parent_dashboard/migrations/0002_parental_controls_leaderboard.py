"""
2026-02-27: Migration adding leaderboard_opt_in to ParentalControls (BS-GAM-005).
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-27: Add leaderboard_opt_in field to ParentalControls."""

    dependencies = [
        ('parent_dashboard', '0001_initial'),  # 2026-02-27: After initial migration
    ]

    operations = [
        migrations.AddField(
            model_name='parentalcontrols',
            name='leaderboard_opt_in',
            field=models.BooleanField(
                default=False,
                help_text='Allow child to appear on class and regional leaderboards',
            ),
        ),
    ]
