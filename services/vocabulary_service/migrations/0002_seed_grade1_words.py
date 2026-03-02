# 2026-02-20: Data migration to seed Grade 1 vocabulary words (BS-LNG).
# Seeds English, Hindi, Telugu grade1 from json/vocabulary/ JSON files.
# Idempotent — get_or_create is used throughout.

import os  # 2026-02-20: File path operations
import json  # 2026-02-20: JSON file loading

from django.db import migrations  # 2026-02-20: Migration base
from django.conf import settings  # 2026-02-20: BASE_DIR for JSON path


def seed_grade1_words(apps, schema_editor):
    """
    2026-02-20: Seed Grade 1 vocabulary words for English, Hindi, Telugu.

    Uses historical models (apps.get_model) per Django migration best practice.
    Reads from json/vocabulary/{Language}/grade1.json files.
    """
    Language = apps.get_model('read_along_service', 'Language')  # 2026-02-20: Historical model
    VocabularyWord = apps.get_model('vocabulary_service', 'VocabularyWord')  # 2026-02-20: Historical model

    base_dir = str(settings.BASE_DIR)  # 2026-02-20: Project root

    seed_targets = [  # 2026-02-20: Languages to seed
        ('English', 1),
        ('Hindi', 1),
        ('Telugu', 1),
    ]

    for language_name, grade in seed_targets:
        # 2026-02-20: Build path to seed JSON
        json_path = os.path.join(
            base_dir, 'json', 'vocabulary', language_name, f'grade{grade}.json'
        )

        if not os.path.exists(json_path):
            continue  # 2026-02-20: Skip if file doesn't exist (non-blocking)

        # 2026-02-20: Fetch Language from DB
        try:
            language = Language.objects.get(name=language_name, is_active=True)
        except Language.DoesNotExist:
            continue  # 2026-02-20: Skip if language not seeded yet

        # 2026-02-20: Load JSON and create words (idempotent)
        with open(json_path, 'r', encoding='utf-8') as f:
            words_data = json.load(f)

        for entry in words_data:
            VocabularyWord.objects.get_or_create(
                language=language,
                grade=grade,
                frequency_rank=entry['rank'],
                defaults={
                    'word': entry['word'],
                    'romanization': entry.get('romanization', ''),
                    'word_type': entry.get('word_type', 'other'),
                    'image_keyword': entry.get('image_keyword', ''),
                },
            )


def unseed_grade1_words(apps, schema_editor):
    """2026-02-20: Reverse: remove seeded Grade 1 words for English/Hindi/Telugu."""
    Language = apps.get_model('read_along_service', 'Language')  # 2026-02-20: Historical model
    VocabularyWord = apps.get_model('vocabulary_service', 'VocabularyWord')  # 2026-02-20: Historical model

    for language_name in ('English', 'Hindi', 'Telugu'):
        try:
            language = Language.objects.get(name=language_name)
            VocabularyWord.objects.filter(language=language, grade=1).delete()
        except Language.DoesNotExist:
            pass  # 2026-02-20: Nothing to delete


class Migration(migrations.Migration):
    """2026-02-20: Seed Grade 1 vocabulary words for English, Hindi, Telugu."""

    dependencies = [
        ('vocabulary_service', '0001_initial'),  # 2026-02-20: Tables must exist
        ('read_along_service', '0002_seed_languages'),  # 2026-02-20: Languages must be seeded
    ]

    operations = [
        migrations.RunPython(seed_grade1_words, unseed_grade1_words),  # 2026-02-20: Seed + reverse
    ]
