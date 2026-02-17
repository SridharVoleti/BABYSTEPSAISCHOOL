"""
2026-02-17: AI Teaching Engine content loader.

Purpose:
    Load and cache teaching lesson content from JSON files.
    Provides IQ-level filtered access to daily content, revision prompts,
    and weekly assessments. Uses in-memory caching for performance.
"""

import json  # 2026-02-17: JSON parsing
import hashlib  # 2026-02-17: SHA256 for cache invalidation
import os  # 2026-02-17: File path operations

from django.conf import settings  # 2026-02-17: Project settings


class TeachingContentLoader:
    """
    2026-02-17: Loads and caches teaching lesson JSON content.

    Content files are stored at json/teaching/class{N}/{Subject}/week{W}.json.
    Uses an in-memory dict cache keyed by lesson_id. Cache is invalidated
    when the file's SHA256 hash changes.
    """

    _cache = {}  # 2026-02-17: In-memory content cache {lesson_id: {hash, data}}

    @classmethod
    def _get_file_hash(cls, file_path):
        """2026-02-17: Compute SHA256 hash of a file for cache invalidation."""
        with open(file_path, 'r', encoding='utf-8') as f:  # 2026-02-17: Read file
            content = f.read()  # 2026-02-17: Read full content
        return hashlib.sha256(content.encode('utf-8')).hexdigest()  # 2026-02-17: Hash

    @classmethod
    def _resolve_path(cls, content_json_path):
        """2026-02-17: Resolve relative path to absolute path from project root."""
        base_dir = settings.BASE_DIR  # 2026-02-17: Project root
        return os.path.join(base_dir, content_json_path)  # 2026-02-17: Full path

    @classmethod
    def load_lesson(cls, content_json_path):
        """
        2026-02-17: Load full lesson JSON from file path.

        Args:
            content_json_path: Relative path from project root to content JSON.

        Returns:
            dict: Full lesson data from JSON file.

        Raises:
            FileNotFoundError: If the content file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        abs_path = cls._resolve_path(content_json_path)  # 2026-02-17: Resolve path
        file_hash = cls._get_file_hash(abs_path)  # 2026-02-17: Current hash

        # 2026-02-17: Check cache
        cached = cls._cache.get(content_json_path)  # 2026-02-17: Lookup
        if cached and cached['hash'] == file_hash:  # 2026-02-17: Cache hit
            return cached['data']  # 2026-02-17: Return cached data

        # 2026-02-17: Cache miss or stale - reload
        with open(abs_path, 'r', encoding='utf-8') as f:  # 2026-02-17: Open file
            data = json.load(f)  # 2026-02-17: Parse JSON

        cls._cache[content_json_path] = {  # 2026-02-17: Update cache
            'hash': file_hash,
            'data': data,
        }
        return data  # 2026-02-17: Return fresh data

    @classmethod
    def get_day_content(cls, content_json_path, day_number, iq_level):
        """
        2026-02-17: Get IQ-filtered content for a specific day.

        Args:
            content_json_path: Relative path to lesson JSON.
            day_number: Day number (1-4).
            iq_level: One of 'foundation', 'standard', 'advanced'.

        Returns:
            dict: Day content with IQ-appropriate teaching_content, plus
                  vocabulary, dialogue_flow, activities, practice_questions.

        Raises:
            ValueError: If day_number is not 1-4 or iq_level is invalid.
        """
        if day_number < 1 or day_number > 4:  # 2026-02-17: Validate day
            raise ValueError(f"day_number must be 1-4, got {day_number}")
        if iq_level not in ('foundation', 'standard', 'advanced'):  # 2026-02-17: Validate IQ
            raise ValueError(f"iq_level must be foundation/standard/advanced, got {iq_level}")

        data = cls.load_lesson(content_json_path)  # 2026-02-17: Load full lesson
        micro_lessons = data.get('micro_lessons', [])  # 2026-02-17: Get micro-lessons

        # 2026-02-17: Find the matching day
        day_data = None  # 2026-02-17: Will hold matching day
        for ml in micro_lessons:  # 2026-02-17: Search by day number
            if ml.get('day') == day_number:  # 2026-02-17: Match
                day_data = ml  # 2026-02-17: Found
                break  # 2026-02-17: Stop search

        if day_data is None:  # 2026-02-17: Day not found
            raise ValueError(f"Day {day_number} not found in lesson")

        # 2026-02-17: Extract IQ-appropriate teaching content
        teaching_content = day_data.get('teaching_content', {})  # 2026-02-17: All IQ levels
        iq_content = teaching_content.get(iq_level, teaching_content.get('standard', {}))  # 2026-02-17: Fallback to standard

        return {  # 2026-02-17: Return filtered content
            'micro_lesson_id': day_data.get('micro_lesson_id'),
            'title': day_data.get('title'),
            'duration_minutes': day_data.get('duration_minutes'),
            'teaching_content': iq_content,
            'vocabulary': day_data.get('vocabulary', []),
            'dialogue_flow': day_data.get('dialogue_flow', []),
            'activities': day_data.get('activities', []),
            'practice_questions': day_data.get('practice_questions', []),
            'character': data.get('character', ''),
        }

    @classmethod
    def get_revision_prompts(cls, content_json_path, day_number, iq_level):
        """
        2026-02-17: Get revision prompts for a specific day and IQ level.

        Day 1 has no revision prompts (returns empty list).
        Days 2-4 have IQ-specific revision prompts.

        Args:
            content_json_path: Relative path to lesson JSON.
            day_number: Day number (1-4).
            iq_level: One of 'foundation', 'standard', 'advanced'.

        Returns:
            list: List of revision prompt strings. Empty for Day 1.
        """
        if day_number == 1:  # 2026-02-17: No revision for Day 1
            return []

        data = cls.load_lesson(content_json_path)  # 2026-02-17: Load lesson
        micro_lessons = data.get('micro_lessons', [])  # 2026-02-17: Get days

        # 2026-02-17: Find matching day
        for ml in micro_lessons:  # 2026-02-17: Search
            if ml.get('day') == day_number:  # 2026-02-17: Match
                revision = ml.get('revision_prompts', {})  # 2026-02-17: Get prompts
                return revision.get(iq_level, revision.get('standard', []))  # 2026-02-17: IQ-filtered

        return []  # 2026-02-17: Day not found, return empty

    @classmethod
    def get_assessment(cls, content_json_path):
        """
        2026-02-17: Get weekly assessment data for a lesson.

        Args:
            content_json_path: Relative path to lesson JSON.

        Returns:
            dict: Assessment data with questions, thresholds, time limit.
        """
        data = cls.load_lesson(content_json_path)  # 2026-02-17: Load lesson
        return data.get('weekly_assessment', {})  # 2026-02-17: Return assessment

    @classmethod
    def clear_cache(cls):
        """2026-02-17: Clear the in-memory content cache."""
        cls._cache.clear()  # 2026-02-17: Reset cache
