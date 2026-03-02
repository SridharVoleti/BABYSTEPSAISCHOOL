"""
2026-02-20: Management command to seed vocabulary words from JSON files (BS-LNG).

Purpose:
    Reads json/vocabulary/{LanguageName}/grade{N}.json files and creates
    VocabularyWord records (idempotent via get_or_create).
    Run after initial migrate and whenever new grade/language JSON files are added.

Usage:
    python manage.py seed_vocabulary
    python manage.py seed_vocabulary --language Hindi --grade 1
"""

import json  # 2026-02-20: JSON file loading
import os  # 2026-02-20: File path operations

from django.core.management.base import BaseCommand, CommandError  # 2026-02-20: Base command
from django.conf import settings  # 2026-02-20: BASE_DIR

from services.read_along_service.language_registry import get_language  # 2026-02-20: Language lookup
from services.vocabulary_service.models import VocabularyWord  # 2026-02-20: Target model


def seed_from_json(language_name: str, grade: int, base_dir: str) -> tuple:
    """
    2026-02-20: Seed VocabularyWord records from a JSON file.

    Reads json/vocabulary/{language_name}/grade{grade}.json, creates
    VocabularyWord rows using get_or_create (idempotent).

    Args:
        language_name: Language name matching Language.name in DB (e.g. 'Hindi').
        grade: Grade number (1-12).
        base_dir: Project base directory (settings.BASE_DIR).

    Returns:
        tuple: (created_count, skipped_count) — rows created vs already existed.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        ValueError: If language not found in DB.
    """
    # 2026-02-20: Build path to seed JSON
    json_path = os.path.join(
        base_dir, 'json', 'vocabulary', language_name, f'grade{grade}.json'
    )

    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Seed file not found: {json_path}")

    # 2026-02-20: Load Language from DB
    try:
        language = get_language(language_name)
    except Exception as exc:
        raise ValueError(f"Language '{language_name}' not found in DB: {exc}")

    # 2026-02-20: Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)

    created_count = 0
    skipped_count = 0

    for entry in words_data:  # 2026-02-20: Iterate word list
        _, created = VocabularyWord.objects.get_or_create(
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
        if created:
            created_count += 1
        else:
            skipped_count += 1

    return created_count, skipped_count


class Command(BaseCommand):
    """2026-02-20: Seed vocabulary words from JSON files."""

    help = 'Seed vocabulary words from json/vocabulary/{Language}/grade{N}.json files'  # 2026-02-20: Help text

    def add_arguments(self, parser):
        """2026-02-20: Optional --language and --grade filters."""
        parser.add_argument(
            '--language',
            type=str,
            default=None,
            help='Language name to seed (default: all)',
        )
        parser.add_argument(
            '--grade',
            type=int,
            default=None,
            help='Grade number to seed (default: 1)',
        )

    def handle(self, *args, **options):
        """2026-02-20: Run the seed command."""
        base_dir = str(settings.BASE_DIR)  # 2026-02-20: Project root

        # 2026-02-20: Default to grade 1 if not specified
        grades = [options['grade']] if options['grade'] else [1]

        # 2026-02-20: Default to English/Hindi/Telugu if no language specified
        if options['language']:
            languages = [options['language']]
        else:
            languages = ['English', 'Hindi', 'Telugu']

        total_created = 0
        total_skipped = 0

        for language_name in languages:
            for grade in grades:
                try:
                    created, skipped = seed_from_json(language_name, grade, base_dir)
                    total_created += created
                    total_skipped += skipped
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Seeded {created} new words for {language_name}/grade{grade} "
                            f"({skipped} already existed)"
                        )
                    )
                except FileNotFoundError as exc:
                    self.stdout.write(self.style.WARNING(str(exc)))
                except ValueError as exc:
                    self.stdout.write(self.style.ERROR(str(exc)))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone: {total_created} created, {total_skipped} skipped."
            )
        )
