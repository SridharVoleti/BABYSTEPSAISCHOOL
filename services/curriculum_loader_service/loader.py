# 2025-10-31: Curriculum Loader Service - Core Loader Module
# Author: BabySteps Development Team
# Purpose: Load, parse, and validate curriculum JSON files
# Last Modified: 2025-10-31

"""
Curriculum Loader Module

This module provides functionality to:
- Scan curriculum folder structure
- Load lesson and question bank JSON files
- Parse and validate JSON content
- Cache parsed content for performance
- Handle errors gracefully
"""

import os  # 2025-10-31: Import for file system operations
import json  # 2025-10-31: Import for JSON parsing
import hashlib  # 2025-10-31: Import for content hashing
from pathlib import Path  # 2025-10-31: Import for path operations
from typing import Dict, List, Optional, Tuple  # 2025-10-31: Import type hints
from datetime import datetime, timedelta  # 2025-10-31: Import for datetime operations
import logging  # 2025-10-31: Import for logging

from django.conf import settings  # 2025-10-31: Import Django settings
from django.core.cache import cache  # 2025-10-31: Import Django cache
from django.utils import timezone  # 2025-10-31: Import Django timezone utilities

from .models import (  # 2025-10-31: Import curriculum models
    CurriculumMetadata,
    LessonFile,
    QuestionBankFile,
    CurriculumCache
)

# 2025-10-31: Configure logger for this module
logger = logging.getLogger(__name__)


class CurriculumLoader:
    """
    2025-10-31: Main class for loading and managing curriculum content
    Implements Singleton pattern to ensure single instance
    """
    
    # 2025-10-31: Class variable to store singleton instance
    _instance = None
    
    def __new__(cls):
        """2025-10-31: Implement Singleton pattern"""
        if cls._instance is None:
            cls._instance = super(CurriculumLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """2025-10-31: Initialize curriculum loader"""
        if self._initialized:
            return
        
        # 2025-10-31: Set base curriculum path
        self.base_path = Path(settings.BASE_DIR) / 'curriculam'
        
        # 2025-10-31: Cache configuration
        self.cache_timeout = 3600  # 2025-10-31: 1 hour cache timeout
        self.use_cache = True  # 2025-10-31: Enable caching by default
        
        # 2025-10-31: Validation configuration
        self.strict_validation = True  # 2025-10-31: Enable strict validation
        
        # 2025-10-31: Mark as initialized
        self._initialized = True
        
        logger.info(f"CurriculumLoader initialized with base path: {self.base_path}")
    
    def scan_curriculum_structure(self) -> List[Dict]:
        """
        2025-10-31: Scan curriculum folder structure and return metadata
        
        Returns:
            List of dictionaries containing curriculum metadata
        """
        logger.info("Starting curriculum structure scan")
        
        # 2025-10-31: Initialize results list
        curriculum_list = []
        
        # 2025-10-31: Check if base path exists
        if not self.base_path.exists():
            logger.error(f"Curriculum base path does not exist: {self.base_path}")
            return curriculum_list
        
        # 2025-10-31: Iterate through class folders
        for class_folder in sorted(self.base_path.iterdir()):
            if not class_folder.is_dir():
                continue
            
            # 2025-10-31: Extract class number from folder name (e.g., "class1" -> 1)
            class_name = class_folder.name
            if not class_name.startswith('class'):
                continue
            
            try:
                class_number = int(class_name.replace('class', ''))
            except ValueError:
                logger.warning(f"Invalid class folder name: {class_name}")
                continue
            
            # 2025-10-31: Iterate through subject folders
            for subject_folder in sorted(class_folder.iterdir()):
                if not subject_folder.is_dir():
                    continue
                
                subject_name = subject_folder.name
                
                # 2025-10-31: Count lessons and question banks
                lesson_count, qb_count, month_count, week_count = self._count_curriculum_files(
                    subject_folder
                )
                
                # 2025-10-31: Create curriculum metadata dictionary
                curriculum_data = {
                    'class_number': class_number,
                    'subject': subject_name,
                    'curriculum_path': str(subject_folder.relative_to(self.base_path)),
                    'total_lessons': lesson_count,
                    'total_question_banks': qb_count,
                    'total_months': month_count,
                    'total_weeks': week_count,
                    'is_active': lesson_count > 0,  # 2025-10-31: Active if has lessons
                }
                
                curriculum_list.append(curriculum_data)
                
                logger.info(
                    f"Found curriculum: Class {class_number} - {subject_name} "
                    f"({lesson_count} lessons, {qb_count} QBs)"
                )
        
        logger.info(f"Curriculum scan complete. Found {len(curriculum_list)} curriculums")
        return curriculum_list
    
    def _count_curriculum_files(self, subject_folder: Path) -> Tuple[int, int, int, int]:
        """
        2025-10-31: Count lesson files, question banks, months, and weeks in subject folder
        
        Args:
            subject_folder: Path to subject folder
        
        Returns:
            Tuple of (lesson_count, qb_count, month_count, week_count)
        """
        lesson_count = 0
        qb_count = 0
        months = set()
        weeks = set()
        
        # 2025-10-31: Iterate through month folders
        for month_folder in subject_folder.iterdir():
            if not month_folder.is_dir() or not month_folder.name.startswith('Month'):
                continue
            
            # 2025-10-31: Extract month number
            try:
                month_num = int(month_folder.name.replace('Month', ''))
                months.add(month_num)
            except ValueError:
                continue
            
            # 2025-10-31: Iterate through week folders
            for week_folder in month_folder.iterdir():
                if not week_folder.is_dir() or not week_folder.name.startswith('Week_'):
                    continue
                
                # 2025-10-31: Extract week number
                try:
                    week_num = int(week_folder.name.replace('Week_', ''))
                    weeks.add(week_num)
                except ValueError:
                    continue
                
                # 2025-10-31: Count lesson files
                lessons_folder = week_folder / 'Lessons'
                if lessons_folder.exists():
                    lesson_count += len(list(lessons_folder.glob('*.json')))
                
                # 2025-10-31: Count question bank files
                qb_folder = week_folder / 'Questions_Banks'
                if qb_folder.exists():
                    qb_count += len(list(qb_folder.glob('*.json')))
        
        return lesson_count, qb_count, len(months), len(weeks)
    
    def load_lesson(
        self,
        class_number: int,
        subject: str,
        month: int,
        week: int,
        day: int,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        2025-10-31: Load a specific lesson JSON file
        
        Args:
            class_number: Class number (1-12)
            subject: Subject name (e.g., 'EVS', 'Math')
            month: Month number (1-12)
            week: Week number (1-52)
            day: Day number (1-7)
            use_cache: Whether to use cached content if available
        
        Returns:
            Parsed lesson JSON as dictionary, or None if not found
        """
        logger.info(
            f"Loading lesson: Class {class_number}, {subject}, "
            f"Month {month}, Week {week}, Day {day}"
        )
        
        # 2025-10-31: Generate cache key
        cache_key = f"lesson_c{class_number}_{subject}_m{month}_w{week}_d{day}"
        
        # 2025-10-31: Try to get from cache first
        if use_cache and self.use_cache:
            cached_content = self._get_from_cache(cache_key)
            if cached_content:
                logger.info(f"Lesson loaded from cache: {cache_key}")
                return cached_content
        
        # 2025-10-31: Construct file path
        lesson_path = self._construct_lesson_path(
            class_number, subject, month, week, day
        )
        
        if not lesson_path or not lesson_path.exists():
            logger.warning(f"Lesson file not found: {lesson_path}")
            return None
        
        # 2025-10-31: Load and parse JSON file
        try:
            with open(lesson_path, 'r', encoding='utf-8') as f:
                lesson_content = json.load(f)
            
            # 2025-10-31: Validate lesson content
            if self.strict_validation:
                validation_errors = self._validate_lesson_json(lesson_content)
                if validation_errors:
                    logger.warning(
                        f"Lesson validation errors for {lesson_path}: {validation_errors}"
                    )
            
            # 2025-10-31: Store in cache
            if self.use_cache:
                self._store_in_cache(cache_key, lesson_content, lesson_path)
            
            logger.info(f"Lesson loaded successfully: {lesson_path.name}")
            return lesson_content
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {lesson_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading lesson {lesson_path}: {e}")
            return None
    
    def load_question_bank(
        self,
        class_number: int,
        subject: str,
        month: int,
        week: int,
        day: int,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        2025-10-31: Load a specific question bank JSON file
        
        Args:
            class_number: Class number (1-12)
            subject: Subject name (e.g., 'EVS', 'Math')
            month: Month number (1-12)
            week: Week number (1-52)
            day: Day number (1-7)
            use_cache: Whether to use cached content if available
        
        Returns:
            Parsed question bank JSON as dictionary, or None if not found
        """
        logger.info(
            f"Loading question bank: Class {class_number}, {subject}, "
            f"Month {month}, Week {week}, Day {day}"
        )
        
        # 2025-10-31: Generate cache key
        cache_key = f"qb_c{class_number}_{subject}_m{month}_w{week}_d{day}"
        
        # 2025-10-31: Try to get from cache first
        if use_cache and self.use_cache:
            cached_content = self._get_from_cache(cache_key)
            if cached_content:
                logger.info(f"Question bank loaded from cache: {cache_key}")
                return cached_content
        
        # 2025-10-31: Construct file path
        qb_path = self._construct_qb_path(
            class_number, subject, month, week, day
        )
        
        if not qb_path or not qb_path.exists():
            logger.warning(f"Question bank file not found: {qb_path}")
            return None
        
        # 2025-10-31: Load and parse JSON file
        try:
            with open(qb_path, 'r', encoding='utf-8') as f:
                qb_content = json.load(f)
            
            # 2025-10-31: Store in cache
            if self.use_cache:
                self._store_in_cache(cache_key, qb_content, qb_path)
            
            logger.info(f"Question bank loaded successfully: {qb_path.name}")
            return qb_content
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {qb_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading question bank {qb_path}: {e}")
            return None
    
    def _construct_lesson_path(
        self,
        class_number: int,
        subject: str,
        month: int,
        week: int,
        day: int
    ) -> Optional[Path]:
        """
        2025-10-31: Construct file path for lesson JSON
        
        Returns:
            Path object or None if path cannot be constructed
        """
        # 2025-10-31: Construct path components
        class_folder = f"class{class_number}"
        month_folder = f"Month{month}"
        week_folder = f"Week_{week}"
        
        # 2025-10-31: Construct full path
        subject_path = self.base_path / class_folder / subject / month_folder / week_folder / 'Lessons'
        
        if not subject_path.exists():
            return None
        
        # 2025-10-31: Find lesson file (pattern: *_C{class}_M{month}_W{week}_D{day}.json)
        pattern = f"*_C{class_number}_M{month}_W{week}_D{day}.json"
        lesson_files = list(subject_path.glob(pattern))
        
        if not lesson_files:
            return None
        
        # 2025-10-31: Return first matching file
        return lesson_files[0]
    
    def _construct_qb_path(
        self,
        class_number: int,
        subject: str,
        month: int,
        week: int,
        day: int
    ) -> Optional[Path]:
        """
        2025-10-31: Construct file path for question bank JSON
        
        Returns:
            Path object or None if path cannot be constructed
        """
        # 2025-10-31: Construct path components
        class_folder = f"class{class_number}"
        month_folder = f"Month{month}"
        week_folder = f"Week_{week}"
        
        # 2025-10-31: Construct full path
        qb_path = self.base_path / class_folder / subject / month_folder / week_folder / 'Questions_Banks'
        
        if not qb_path.exists():
            return None
        
        # 2025-10-31: Find question bank file (pattern: *_C{class}_M{month}_W{week}_D{day}_QB.json)
        pattern = f"*_C{class_number}_M{month}_W{week}_D{day}_QB.json"
        qb_files = list(qb_path.glob(pattern))
        
        if not qb_files:
            return None
        
        # 2025-10-31: Return first matching file
        return qb_files[0]
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        2025-10-31: Retrieve content from cache
        
        Args:
            cache_key: Unique cache key
        
        Returns:
            Cached content or None if not found
        """
        try:
            # 2025-10-31: Try Django cache first
            cached_content = cache.get(cache_key)
            if cached_content:
                return cached_content
            
            # 2025-10-31: Try database cache
            try:
                cache_obj = CurriculumCache.objects.get(
                    cache_key=cache_key,
                    is_valid=True
                )
                
                # 2025-10-31: Check if cache has expired
                if cache_obj.expires_at and cache_obj.expires_at < timezone.now():
                    cache_obj.is_valid = False
                    cache_obj.save()
                    return None
                
                # 2025-10-31: Increment hit count
                cache_obj.hit_count += 1
                cache_obj.save(update_fields=['hit_count'])
                
                return cache_obj.json_content
                
            except CurriculumCache.DoesNotExist:
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None
    
    def _store_in_cache(
        self,
        cache_key: str,
        content: Dict,
        file_path: Path
    ) -> None:
        """
        2025-10-31: Store content in cache
        
        Args:
            cache_key: Unique cache key
            content: Content to cache
            file_path: Path to source file
        """
        try:
            # 2025-10-31: Store in Django cache
            cache.set(cache_key, content, self.cache_timeout)
            
            # 2025-10-31: Calculate content hash
            content_str = json.dumps(content, sort_keys=True)
            content_hash = hashlib.sha256(content_str.encode()).hexdigest()
            
            # 2025-10-31: Store in database cache
            # Note: This requires lesson to exist in database
            # For now, just use Django cache
            
            logger.debug(f"Content cached: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
    
    def _validate_lesson_json(self, lesson_content: Dict) -> List[str]:
        """
        2025-10-31: Validate lesson JSON structure
        
        Args:
            lesson_content: Parsed lesson JSON
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # 2025-10-31: Check required top-level keys
        required_keys = ['metadata', 'objectives', 'content_blocks']
        for key in required_keys:
            if key not in lesson_content:
                errors.append(f"Missing required key: {key}")
        
        # 2025-10-31: Validate metadata
        if 'metadata' in lesson_content:
            metadata = lesson_content['metadata']
            required_metadata = ['lesson_id', 'class', 'subject', 'lesson_title']
            for key in required_metadata:
                if key not in metadata:
                    errors.append(f"Missing required metadata key: {key}")
        
        # 2025-10-31: Validate content blocks
        if 'content_blocks' in lesson_content:
            content_blocks = lesson_content['content_blocks']
            if not isinstance(content_blocks, list):
                errors.append("content_blocks must be a list")
            elif len(content_blocks) == 0:
                errors.append("content_blocks cannot be empty")
        
        return errors
    
    def clear_cache(self, cache_key: Optional[str] = None) -> None:
        """
        2025-10-31: Clear cache (specific key or all)
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all
        """
        if cache_key:
            cache.delete(cache_key)
            logger.info(f"Cache cleared for key: {cache_key}")
        else:
            cache.clear()
            CurriculumCache.objects.update(is_valid=False)
            logger.info("All caches cleared")


# 2025-10-31: Create singleton instance
curriculum_loader = CurriculumLoader()
