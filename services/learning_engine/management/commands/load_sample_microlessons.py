# 2025-12-18: Management Command to Load Sample Micro-Lessons
# Author: BabySteps Development Team
# Purpose: Load sample micro-lesson data for testing and development
# Last Modified: 2025-12-18

"""
Load Sample Micro-Lessons Command

Usage:
    python manage.py load_sample_microlessons

This command loads sample micro-lesson JSON files into the database
for testing the learning engine functionality.
"""

# 2025-12-18: Import JSON for parsing lesson files
import json

# 2025-12-18: Import Path for file operations
from pathlib import Path

# 2025-12-18: Import Django management base command
from django.core.management.base import BaseCommand

# 2025-12-18: Import timezone for timestamps
from django.utils import timezone

# 2025-12-18: Import MicroLesson model
from services.learning_engine.models import MicroLesson


class Command(BaseCommand):
    """
    2025-12-18: Django management command to load sample micro-lessons.
    """
    
    # 2025-12-18: Command help text
    help = 'Load sample micro-lesson JSON files into the database'
    
    def add_arguments(self, parser):
        """2025-12-18: Add command line arguments."""
        # 2025-12-18: Optional path to sample data directory
        parser.add_argument(
            '--path',
            type=str,
            default=None,
            help='Path to sample data directory (default: services/learning_engine/sample_data/)'
        )
        # 2025-12-18: Flag to clear existing data
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing micro-lessons before loading'
        )
    
    def handle(self, *args, **options):
        """2025-12-18: Execute the command."""
        # 2025-12-18: Determine sample data path
        if options['path']:
            sample_dir = Path(options['path'])
        else:
            sample_dir = Path(__file__).parent.parent.parent / 'sample_data'
        
        # 2025-12-18: Check if directory exists
        if not sample_dir.exists():
            self.stderr.write(self.style.ERROR(f'Sample data directory not found: {sample_dir}'))
            return
        
        # 2025-12-18: Clear existing data if requested
        if options['clear']:
            deleted_count = MicroLesson.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'Cleared {deleted_count} existing micro-lessons'))
        
        # 2025-12-18: Find all JSON files
        json_files = list(sample_dir.glob('*.json'))
        
        if not json_files:
            self.stderr.write(self.style.WARNING(f'No JSON files found in {sample_dir}'))
            return
        
        # 2025-12-18: Load each JSON file
        loaded_count = 0
        error_count = 0
        
        for json_file in json_files:
            try:
                # 2025-12-18: Read and parse JSON
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 2025-12-18: Create or update micro-lesson
                lesson, created = MicroLesson.objects.update_or_create(
                    lesson_id=data['lesson_id'],
                    defaults={
                        'title': data['title'],
                        'learning_objective': data['learning_objective'],
                        'subject': data['subject'],
                        'class_number': data['class_number'],
                        'chapter_id': data['chapter_id'],
                        'chapter_name': data['chapter_name'],
                        'sequence_in_chapter': data['sequence_in_chapter'],
                        'duration_minutes': data['duration_minutes'],
                        'worked_examples': data['worked_examples'],
                        'practice_questions': data['practice_questions'],
                        'practice_themes': data['practice_themes'],
                        'visual_assets': data['visual_assets'],
                        'teacher_narration': data.get('teacher_narration', {}),
                        'textbook_reading': data.get('textbook_reading', {}),
                        'misconceptions': data.get('misconceptions', []),
                        'prerequisites': data.get('prerequisites', []),
                        'qa_status': data.get('qa_status', 'pending'),
                        'qa_notes': data.get('qa_notes', ''),
                        'version': data.get('version', '1.0'),
                        'language': data.get('language', 'en'),
                        'localization_variants': data.get('localization_variants', {}),
                        'is_published': data.get('is_published', False),
                    }
                )
                
                # 2025-12-18: Set QA passed timestamp if applicable
                if lesson.qa_status == 'passed' and not lesson.qa_passed_at:
                    lesson.qa_passed_at = timezone.now()
                    lesson.save()
                
                # 2025-12-18: Set published timestamp if applicable
                if lesson.is_published and not lesson.published_at:
                    lesson.published_at = timezone.now()
                    lesson.save()
                
                # 2025-12-18: Validate structure
                is_valid, errors = lesson.validate_structure()
                
                # 2025-12-18: Report result
                action = 'Created' if created else 'Updated'
                if is_valid:
                    self.stdout.write(self.style.SUCCESS(
                        f'{action}: {lesson.lesson_id} - {lesson.title} ✓'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'{action}: {lesson.lesson_id} - {lesson.title} (validation errors: {errors})'
                    ))
                
                loaded_count += 1
                
            except Exception as e:
                self.stderr.write(self.style.ERROR(
                    f'Error loading {json_file.name}: {str(e)}'
                ))
                error_count += 1
        
        # 2025-12-18: Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Loaded {loaded_count} micro-lessons successfully'
        ))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(
                f'{error_count} files had errors'
            ))
