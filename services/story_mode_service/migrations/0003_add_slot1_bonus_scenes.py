"""
2026-03-02: Add slot-1 bonus scenes for all 5 subjects (BS-GAM-003).

Seeds the 5 bonus scenes at concept_slot=1 (one per subject) that were
missing from the original 0002 seed migration.
"""
from django.db import migrations  # 2026-03-02: Migration base class

# 2026-03-02: New slot-1 bonus scenes added to scene_catalog after initial seed
SLOT1_BONUS_SCENES = [
    {
        'scene_id': 'english_q001_bonus',
        'subject': 'English',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A radiant golden door appears behind the first bookshelf — visible "
            "only to those who earned five stars. Inside, Varna reveals the "
            "Secret Scroll Room, where the rarest stories in all of India "
            "are preserved in shimmering light."
        ),
        'bonus_text': (
            "You have unlocked the Secret Scroll Room with a perfect five-star score! "
            "Varna grants you the Golden Quill — a mark of excellence awarded only "
            "to the most dedicated language learners."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'math_q001_bonus',
        'subject': 'Math',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A hidden chamber glows with golden light beyond the kingdom gates — "
            "only five-star scholars may enter. Aryabhatta reveals the Chamber "
            "of Ancient Calculations, where the world's first mathematical "
            "discoveries are preserved in luminous equations."
        ),
        'bonus_text': (
            "You have entered the Chamber of Ancient Calculations! Aryabhatta "
            "shares the secret behind the discovery of zero and the decimal "
            "system. You receive the Bronze Abacus of Champions — awarded only "
            "to the finest mathematical minds."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'science_q001_bonus',
        'subject': 'Science',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A secret path through glowing ferns appears only for five-star "
            "scientists. Kanada leads Meena to the Ancient Atom Garden, where "
            "each flower represents a different element discovered by Indian "
            "scholars thousands of years ago."
        ),
        'bonus_text': (
            "You have discovered the Ancient Atom Garden! Kanada reveals how "
            "ancient Indian sages first proposed the concept of the atom, "
            "centuries before modern science. You receive the Atom Amulet — "
            "proof that you think like a true scientist."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'hindi_q001_bonus',
        'subject': 'Hindi',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A gleaming door of carved Devanagari script opens for five-star "
            "scholars only, leading to the Akshara Treasury where the rarest "
            "Hindi manuscripts are stored. Kavita sings a special song of "
            "welcome for Ravi's exceptional achievement."
        ),
        'bonus_text': (
            "You have unlocked the Akshara Treasury! The greatest Hindi poets "
            "and writers appear to share their wisdom with you. Kavita presents "
            "the Golden Akshara — awarded only to the most dedicated Hindi scholars."
        ),
        'illustration_ref': '',
    },
    {
        'scene_id': 'telugu_q001_bonus',
        'subject': 'Telugu',
        'scene_type': 'bonus',
        'concept_slot': 1,
        'narrative_text': (
            "A hidden grove surrounded by jasmine and golden lotus opens only "
            "for five-star learners — the Nannaya Nivasam, named after Telugu's "
            "first great poet. Akshara bows gently, welcoming Lakshmi to this "
            "secret sanctuary of Telugu literature."
        ),
        'bonus_text': (
            "You have entered the Nannaya Nivasam! The first poets of Telugu "
            "literature share their stories and verses with you here. Akshara "
            "presents the Pearl of Andhra — the rarest honour in Andhra Vanam."
        ),
        'illustration_ref': '',
    },
]


def add_slot1_bonus_scenes(apps, schema_editor):
    """2026-03-02: Insert the 5 slot-1 bonus scenes into NarrativeScene."""
    NarrativeScene = apps.get_model('story_mode_service', 'NarrativeScene')
    for scene_data in SLOT1_BONUS_SCENES:
        NarrativeScene.objects.get_or_create(
            scene_id=scene_data['scene_id'],
            defaults={
                'subject': scene_data['subject'],
                'scene_type': scene_data['scene_type'],
                'concept_slot': scene_data['concept_slot'],
                'narrative_text': scene_data['narrative_text'],
                'bonus_text': scene_data['bonus_text'],
                'illustration_ref': scene_data['illustration_ref'],
            },
        )


def remove_slot1_bonus_scenes(apps, schema_editor):
    """2026-03-02: Remove slot-1 bonus scenes on migration reversal."""
    NarrativeScene = apps.get_model('story_mode_service', 'NarrativeScene')
    scene_ids = [s['scene_id'] for s in SLOT1_BONUS_SCENES]
    NarrativeScene.objects.filter(scene_id__in=scene_ids).delete()


class Migration(migrations.Migration):
    """2026-03-02: Add missing slot-1 bonus scenes for all 5 subjects."""

    dependencies = [
        ('story_mode_service', '0002_seed_scenes'),  # 2026-03-02: Base scenes must exist
    ]

    operations = [
        migrations.RunPython(add_slot1_bonus_scenes, remove_slot1_bonus_scenes),
    ]
