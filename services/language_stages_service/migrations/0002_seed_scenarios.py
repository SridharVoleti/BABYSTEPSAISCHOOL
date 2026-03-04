"""
2026-03-02: Seed 20 conversation scenarios for Language Stages Service (BS-LNG-005).
"""

from django.db import migrations  # 2026-03-02: Migration primitives

from services.language_stages_service.scenario_catalog import SCENARIO_CATALOG  # 2026-03-02: Catalog


def seed_scenarios(apps, schema_editor):
    """2026-03-02: Create all 20 conversation scenarios from catalog."""
    ConversationScenario = apps.get_model(  # 2026-03-02: Historical model
        'language_stages_service', 'ConversationScenario'
    )
    for data in SCENARIO_CATALOG:  # 2026-03-02: Iterate catalog
        ConversationScenario.objects.get_or_create(
            scenario_number=data['scenario_number'],
            defaults={
                'title': data['title'],
                'ai_persona': data['ai_persona'],
                'difficulty': data['difficulty'],
                'min_turns': data['min_turns'],
                'max_turns': data['max_turns'],
                'unlock_after_scenario': data.get('unlock_after_scenario'),
                'context_description': data['context_description'],
                'opening_prompt_template': data['opening_prompt_template'],
            },
        )


def unseed_scenarios(apps, schema_editor):
    """2026-03-02: Remove all seeded scenarios (reverse migration)."""
    ConversationScenario = apps.get_model(
        'language_stages_service', 'ConversationScenario'
    )
    ConversationScenario.objects.filter(
        scenario_number__in=[d['scenario_number'] for d in SCENARIO_CATALOG]
    ).delete()


class Migration(migrations.Migration):
    """2026-03-02: Seed 20 universal conversation scenarios."""

    dependencies = [
        ('language_stages_service', '0001_initial'),  # 2026-03-02: Tables must exist
    ]

    operations = [
        migrations.RunPython(seed_scenarios, unseed_scenarios),  # 2026-03-02: Seed
    ]
