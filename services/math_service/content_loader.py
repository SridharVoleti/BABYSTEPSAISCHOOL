"""
2026-03-02: Math problem bank content loader (BS-MTH module).

Purpose:
    Load and cache JSON problem bank files for math lessons.
    Provides IQ-level-filtered access to daily problem sets.
    Uses SHA256-based cache invalidation so content updates
    are picked up without restarting the server.
"""

import json  # 2026-03-02: JSON parsing
import hashlib  # 2026-03-02: Hash for cache invalidation
import os  # 2026-03-02: File path operations

from django.conf import settings  # 2026-03-02: BASE_DIR


# 2026-03-02: Mapping from IQ level to difficulty tier in JSON
_IQ_TO_DIFFICULTY = {
    'foundation': 'easy',
    'standard': 'medium',
    'advanced': 'hard',
}


class MathContentLoader:
    """
    2026-03-02: Loads and caches math lesson JSON content.

    Content files are stored at json/math/class{N}/week{W}.json.
    Uses an in-memory dict cache keyed by relative file path.
    Cache entries are invalidated when the file's SHA256 hash changes.
    """

    _cache: dict = {}  # 2026-03-02: {path: {hash, data}}

    @classmethod
    def _resolve_path(cls, json_path: str) -> str:
        """
        2026-03-02: Resolve relative path to absolute path from project root.

        Args:
            json_path: Relative path from project root.

        Returns:
            str: Absolute filesystem path.
        """
        return os.path.join(settings.BASE_DIR, json_path)  # 2026-03-02: Join with BASE_DIR

    @classmethod
    def _file_hash(cls, abs_path: str) -> str:
        """
        2026-03-02: Compute SHA256 hash of a file for cache invalidation.

        Args:
            abs_path: Absolute filesystem path.

        Returns:
            str: Hex SHA256 digest.
        """
        with open(abs_path, 'r', encoding='utf-8') as f:  # 2026-03-02: Read file
            return hashlib.sha256(f.read().encode('utf-8')).hexdigest()  # 2026-03-02: Hash

    @classmethod
    def load_lesson(cls, json_path: str) -> dict:
        """
        2026-03-02: Load full lesson JSON from a relative file path.

        Checks the in-memory cache first; reloads if hash has changed.

        Args:
            json_path: Relative path from project root to lesson JSON.

        Returns:
            dict: Full lesson data parsed from JSON.

        Raises:
            FileNotFoundError: If the content file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        abs_path = cls._resolve_path(json_path)  # 2026-03-02: Absolute path
        current_hash = cls._file_hash(abs_path)  # 2026-03-02: Current file hash

        cached = cls._cache.get(json_path)  # 2026-03-02: Check cache
        if cached and cached['hash'] == current_hash:  # 2026-03-02: Cache hit
            return cached['data']  # 2026-03-02: Return cached data

        with open(abs_path, 'r', encoding='utf-8') as f:  # 2026-03-02: Load file
            data = json.load(f)  # 2026-03-02: Parse JSON

        cls._cache[json_path] = {'hash': current_hash, 'data': data}  # 2026-03-02: Cache
        return data  # 2026-03-02: Return fresh data

    @classmethod
    def get_day_problems(cls, json_path: str, day: int, iq_level: str) -> list:
        """
        2026-03-02: Return problems for a specific day filtered by IQ level.

        Mapping: foundation→easy, standard→medium, advanced→hard.
        Falls back to medium if the target difficulty is missing.

        Args:
            json_path: Relative path to lesson JSON.
            day: Day number (1-4).
            iq_level: One of 'foundation', 'standard', 'advanced'.

        Returns:
            list: List of problem dicts for that day and difficulty tier.

        Raises:
            ValueError: If day not found in lesson or iq_level invalid.
        """
        if iq_level not in _IQ_TO_DIFFICULTY:  # 2026-03-02: Validate IQ level
            raise ValueError(f"Invalid iq_level: {iq_level}. Must be foundation/standard/advanced.")

        data = cls.load_lesson(json_path)  # 2026-03-02: Load full lesson
        difficulty = _IQ_TO_DIFFICULTY[iq_level]  # 2026-03-02: Map to difficulty tier

        days = data.get('days', [])  # 2026-03-02: Get all days
        day_data = next((d for d in days if d.get('day') == day), None)  # 2026-03-02: Find day

        if day_data is None:  # 2026-03-02: Day not found
            raise ValueError(f"Day {day} not found in lesson at {json_path}")

        problems_by_diff = day_data.get('problems', {})  # 2026-03-02: All difficulty tiers
        # 2026-03-02: Fall back to medium if target tier is missing
        return problems_by_diff.get(difficulty, problems_by_diff.get('medium', []))

    @classmethod
    def get_day_content(cls, json_path: str, day: int) -> dict:
        """
        2026-03-02: Return the teaching content for a specific day (no problems).

        Returns title, teaching_summary, and worked_examples for the AI tutor
        to use when delivering the teaching phase (BS-AMT-001).

        Args:
            json_path: Relative path to lesson JSON.
            day: Day number (1-4).

        Returns:
            dict: {title, teaching_summary, worked_examples, day}

        Raises:
            ValueError: If day not found in lesson.
        """
        data = cls.load_lesson(json_path)  # 2026-03-02: Load full lesson
        days = data.get('days', [])  # 2026-03-02: All days
        day_data = next((d for d in days if d.get('day') == day), None)  # 2026-03-02: Find

        if day_data is None:  # 2026-03-02: Day not found
            raise ValueError(f"Day {day} not found in lesson at {json_path}")

        return {  # 2026-03-02: Teaching content only (no problems)
            'day': day_data.get('day', day),
            'title': day_data.get('title', f'Day {day}'),
            'teaching_summary': day_data.get('teaching_summary', ''),
            'worked_examples': day_data.get('worked_examples', []),
        }

    @classmethod
    def get_problem_by_id(cls, json_path: str, problem_id: str) -> dict | None:
        """
        2026-03-02: Search all days and difficulties for a problem by ID.

        Args:
            json_path: Relative path to lesson JSON.
            problem_id: Unique problem ID string.

        Returns:
            dict | None: Problem dict if found, None otherwise.
        """
        data = cls.load_lesson(json_path)  # 2026-03-02: Load lesson
        for day_data in data.get('days', []):  # 2026-03-02: Each day
            problems = day_data.get('problems', {})  # 2026-03-02: All tiers
            for tier_problems in problems.values():  # 2026-03-02: Each tier
                for problem in tier_problems:  # 2026-03-02: Each problem
                    if problem.get('id') == problem_id:  # 2026-03-02: ID match
                        return problem  # 2026-03-02: Found
        return None  # 2026-03-02: Not found

    @classmethod
    def clear_cache(cls) -> None:
        """2026-03-02: Clear the in-memory content cache (used in tests)."""
        cls._cache.clear()  # 2026-03-02: Reset
