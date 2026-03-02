"""
2026-02-20: Seed 20 badge catalog entries for Gamification Engine (BS-GAM).

Uses get_or_create for idempotency — safe to run multiple times.
"""

from django.db import migrations


def seed_badges(apps, schema_editor):
    """2026-02-20: Insert 20 badge rows from BADGE_CATALOG."""
    from services.gamification_service.badge_catalog import BADGE_CATALOG  # 2026-02-20: Catalog

    Badge = apps.get_model('gamification_service', 'Badge')  # 2026-02-20: Model reference

    for entry in BADGE_CATALOG:
        Badge.objects.get_or_create(
            badge_id=entry['badge_id'],
            defaults={
                'name': entry['name'],
                'description': entry['description'],
                'icon': entry['icon'],
                'category': entry['category'],
                'rarity': entry['rarity'],
            },
        )


def unseed_badges(apps, schema_editor):
    """2026-02-20: Reverse: remove all seeded badge rows."""
    from services.gamification_service.badge_catalog import BADGE_CATALOG  # 2026-02-20: Catalog

    Badge = apps.get_model('gamification_service', 'Badge')  # 2026-02-20: Model reference
    ids = [entry['badge_id'] for entry in BADGE_CATALOG]
    Badge.objects.filter(badge_id__in=ids).delete()


class Migration(migrations.Migration):
    """2026-02-20: Seed badge catalog data."""

    dependencies = [
        ('gamification_service', '0001_initial'),  # 2026-02-20: Schema must exist first
    ]

    operations = [
        migrations.RunPython(seed_badges, reverse_code=unseed_badges),
    ]
