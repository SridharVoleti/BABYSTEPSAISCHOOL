"""
2026-02-27: Seed migration for NarrativeScene catalog (BS-GAM-003).

Seeds 20 scenes (4 per subject × 5 subjects).
"""
from django.db import migrations  # 2026-02-27: Migration base class


def seed_scenes(apps, schema_editor):
    """2026-02-27: Create initial NarrativeScene records."""
    from services.story_mode_service.scene_catalog import SCENE_CATALOG  # 2026-02-27: Catalog data
    NarrativeScene = apps.get_model('story_mode_service', 'NarrativeScene')
    for scene_data in SCENE_CATALOG:
        NarrativeScene.objects.get_or_create(
            scene_id=scene_data['scene_id'],
            defaults={
                'subject': scene_data['subject'],
                'scene_type': scene_data['scene_type'],
                'concept_slot': scene_data['concept_slot'],
                'narrative_text': scene_data['narrative_text'],
                'bonus_text': scene_data.get('bonus_text', ''),
                'illustration_ref': scene_data.get('illustration_ref', ''),
            }
        )


def unseed_scenes(apps, schema_editor):
    """2026-02-27: Remove seeded scenes on migration reversal."""
    NarrativeScene = apps.get_model('story_mode_service', 'NarrativeScene')
    NarrativeScene.objects.all().delete()


class Migration(migrations.Migration):
    """2026-02-27: Seed NarrativeScene catalog."""

    dependencies = [
        ('story_mode_service', '0001_initial'),  # 2026-02-27: Tables must exist first
    ]

    operations = [
        migrations.RunPython(seed_scenes, unseed_scenes),
    ]
