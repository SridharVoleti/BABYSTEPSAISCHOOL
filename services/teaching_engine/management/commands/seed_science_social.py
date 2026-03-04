"""
2026-03-03: Management command to seed Science and Social Science lesson records (BS-SCI/BS-SST).

Purpose:
    Creates (or updates) TeachingLesson DB records for Class 6 Science and Social Science
    Week 1 lessons. Idempotent via update_or_create — safe to run multiple times.

Usage:
    python manage.py seed_science_social
"""

from django.core.management.base import BaseCommand  # 2026-03-03: Base command class

from services.teaching_engine.models import TeachingLesson  # 2026-03-03: Target model


# 2026-03-03: Lesson definitions to seed
LESSON_DEFINITIONS = [
    {
        'lesson_id': 'SCI6_ENV_CH01_W01',
        'title': 'Our Environment — Air, Water, Soil and Forests',
        'subject': 'Science',
        'class_number': 6,
        'chapter_id': 'SCI6_ENV_CH01',
        'chapter_title': 'Our Environment',
        'week_number': 1,
        'character_name': 'Dr. Saina the Science Explorer',
        'learning_objectives': [
            'Identify the main components of air and their approximate percentages',
            'Explain the water cycle stages: evaporation, condensation, precipitation',
            'Distinguish between the three soil layers and two major rock types',
            'Describe a food chain and explain ecosystem services of forests',
            'Apply scientific vocabulary: atmosphere, evaporation, humus, biodiversity',
        ],
        'content_json_path': 'json/teaching/class6/Science/week1.json',
        'status': 'published',
    },
    {
        'lesson_id': 'SST6_EARTH_CH01_W01',
        'title': 'The Earth in the Solar System',
        'subject': 'Social',
        'class_number': 6,
        'chapter_id': 'SST6_EARTH_CH01',
        'chapter_title': 'The Earth in the Solar System',
        'week_number': 1,
        'character_name': 'Explorer Arjun',
        'learning_objectives': [
            'Name the eight planets of the solar system in order from the Sun',
            'Explain the three layers of the Earth\'s interior with their characteristics',
            'Identify the seven continents and five oceans on a map',
            'Explain latitude and longitude and their use in locating places',
            'Apply geographic vocabulary: orbit, mantle, continent, equator, meridian',
        ],
        'content_json_path': 'json/teaching/class6/Social/week1.json',
        'status': 'published',
    },
]


class Command(BaseCommand):
    """
    2026-03-03: Seeds Science and Social Science teaching lesson records.

    Creates TeachingLesson records for:
    - Class 6 Science Week 1 (Our Environment)
    - Class 6 Social Science Week 1 (The Earth in the Solar System)

    Uses update_or_create for idempotency.
    """

    help = 'Seed Class 6 Science and Social Science Week 1 lesson records'  # 2026-03-03: Help text

    def handle(self, *args, **options):
        """2026-03-03: Execute the seed command."""
        self.stdout.write(self.style.MIGRATE_HEADING(  # 2026-03-03: Header message
            'Seeding Science and Social Science lesson records...'
        ))

        created_count = 0  # 2026-03-03: Track new records
        updated_count = 0  # 2026-03-03: Track updated records

        for definition in LESSON_DEFINITIONS:  # 2026-03-03: Process each lesson
            lesson_id = definition['lesson_id']  # 2026-03-03: Read without mutating module-level list
            defaults = {k: v for k, v in definition.items() if k != 'lesson_id'}  # 2026-03-03: Exclude pk

            lesson, created = TeachingLesson.objects.update_or_create(  # 2026-03-03: Idempotent create
                lesson_id=lesson_id,
                defaults=defaults,
            )

            if created:  # 2026-03-03: Count result
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  Created: [{lesson_id}] {lesson.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  Updated: [{lesson_id}] {lesson.title}')
                )

        self.stdout.write(  # 2026-03-03: Summary
            self.style.SUCCESS(
                f'\nDone. Created: {created_count}, Updated: {updated_count} lesson(s).'
            )
        )
