# 2026-02-19: Data migration to seed 14 Indian languages (BS-RAM).
# Runs once on first deploy. Subsequent additions via Django admin.

from django.db import migrations

from services.read_along_service.language_registry import LANGUAGE_SEED  # 2026-02-19: Seed data


def seed_languages(apps, schema_editor):
    """2026-02-19: Insert all 14 seed languages into the Language table."""
    Language = apps.get_model('read_along_service', 'Language')  # 2026-02-19: Get historical model
    for name, attrs in LANGUAGE_SEED.items():  # 2026-02-19: Iterate seed dict
        Language.objects.get_or_create(  # 2026-02-19: Idempotent insert
            name=name,
            defaults={
                'bcp47_tag': attrs['bcp47'],
                'display_name': attrs['display_name'],
                'script': attrs['script'],
                'tts_rate': attrs['tts_rate'],
                'is_active': True,
                'sort_order': attrs['sort_order'],
            },
        )


def unseed_languages(apps, schema_editor):
    """2026-02-19: Reverse: remove the 14 seeded languages."""
    Language = apps.get_model('read_along_service', 'Language')  # 2026-02-19: Get historical model
    Language.objects.filter(name__in=list(LANGUAGE_SEED.keys())).delete()  # 2026-02-19: Delete


class Migration(migrations.Migration):
    """2026-02-19: Seed 14 Indian languages from LANGUAGE_SEED."""

    dependencies = [
        ('read_along_service', '0001_initial'),  # 2026-02-19: Table must exist
    ]

    operations = [
        migrations.RunPython(seed_languages, unseed_languages),  # 2026-02-19: Seed + reverse
    ]
