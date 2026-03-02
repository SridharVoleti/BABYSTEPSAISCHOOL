"""
2026-03-02: Migration to rename leitner_box → box and add completed_concepts.

Renames SpacedRepetitionRecord.leitner_box to box (shorter, cleaner name)
and adds PacingRecord.completed_concepts for denormalized mastery count.
"""

from django.db import migrations, models  # 2026-03-02: Migration primitives


class Migration(migrations.Migration):
    """2026-03-02: Rename leitner_box to box; add completed_concepts to PacingRecord."""

    dependencies = [
        ('spaced_repetition_service', '0001_initial'),  # 2026-03-02: Base schema
    ]

    operations = [
        # 2026-03-02: Rename leitner_box → box on SpacedRepetitionRecord
        migrations.RenameField(
            model_name='spacedrepetitionrecord',
            old_name='leitner_box',
            new_name='box',
        ),
        # 2026-03-02: Add completed_concepts to PacingRecord (denormalized counter)
        migrations.AddField(
            model_name='pacingrecord',
            name='completed_concepts',
            field=models.IntegerField(default=0),
        ),
    ]
