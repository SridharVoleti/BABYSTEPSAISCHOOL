# 2025-10-31: Curriculum Loader Service - API Views
# Author: BabySteps Development Team
# Purpose: REST API endpoints for curriculum access
# Last Modified: 2025-10-31

"""
Curriculum Loader API Views

This module provides REST API endpoints for:
- Listing available curriculums
- Retrieving specific lessons
- Retrieving question banks
- Navigating lessons (next/previous)
"""

from rest_framework import status  # 2025-10-31: Import REST framework status codes
from rest_framework.decorators import api_view  # 2025-10-31: Import API view decorator
from rest_framework.response import Response  # 2025-10-31: Import Response class
import logging  # 2025-10-31: Import logging

from .loader import curriculum_loader  # 2025-10-31: Import curriculum loader singleton

# 2025-10-31: Configure logger for this module
logger = logging.getLogger(__name__)


@api_view(['GET'])
def curriculum_list(request):
    """
    2025-10-31: API endpoint to list all available curriculums
    
    GET /api/curriculum/list
    
    Returns:
        JSON response with list of curriculums
    """
    try:
        # 2025-10-31: Scan curriculum structure
        curriculums = curriculum_loader.scan_curriculum_structure()
        
        logger.info(f"Curriculum list requested, found {len(curriculums)} curriculums")
        
        return Response({
            'success': True,
            'count': len(curriculums),
            'curriculums': curriculums
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error listing curriculums: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_lesson(request, class_number, subject, month, week, day):
    """
    2025-10-31: API endpoint to retrieve a specific lesson
    
    GET /api/curriculum/class/{class}/subject/{subject}/month/{month}/week/{week}/day/{day}
    
    Args:
        class_number: Class number (1-12)
        subject: Subject name (e.g., 'EVS', 'Math')
        month: Month number (1-12)
        week: Week number (1-52)
        day: Day number (1-7)
    
    Returns:
        JSON response with lesson content
    """
    try:
        # 2025-10-31: Parse parameters
        class_num = int(class_number)
        month_num = int(month)
        week_num = int(week)
        day_num = int(day)
        
        # 2025-10-31: Get use_cache parameter from query string
        use_cache = request.GET.get('use_cache', 'true').lower() == 'true'
        
        logger.info(
            f"Lesson requested: Class {class_num}, {subject}, "
            f"Month {month_num}, Week {week_num}, Day {day_num}"
        )
        
        # 2025-10-31: Load lesson
        lesson = curriculum_loader.load_lesson(
            class_num, subject, month_num, week_num, day_num, use_cache
        )
        
        if lesson is None:
            logger.warning(f"Lesson not found")
            return Response({
                'success': False,
                'error': 'Lesson not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"Lesson loaded successfully: {lesson.get('metadata', {}).get('lesson_id')}")
        
        return Response({
            'success': True,
            'lesson': lesson
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return Response({
            'success': False,
            'error': f'Invalid parameters: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error loading lesson: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_question_bank(request, class_number, subject, month, week, day):
    """
    2025-10-31: API endpoint to retrieve a specific question bank
    
    GET /api/curriculum/class/{class}/subject/{subject}/month/{month}/week/{week}/day/{day}/qb
    
    Args:
        class_number: Class number (1-12)
        subject: Subject name (e.g., 'EVS', 'Math')
        month: Month number (1-12)
        week: Week number (1-52)
        day: Day number (1-7)
    
    Returns:
        JSON response with question bank content
    """
    try:
        # 2025-10-31: Parse parameters
        class_num = int(class_number)
        month_num = int(month)
        week_num = int(week)
        day_num = int(day)
        
        # 2025-10-31: Get use_cache parameter from query string
        use_cache = request.GET.get('use_cache', 'true').lower() == 'true'
        
        logger.info(
            f"Question bank requested: Class {class_num}, {subject}, "
            f"Month {month_num}, Week {week_num}, Day {day_num}"
        )
        
        # 2025-10-31: Load question bank
        qb = curriculum_loader.load_question_bank(
            class_num, subject, month_num, week_num, day_num, use_cache
        )
        
        if qb is None:
            logger.warning(f"Question bank not found")
            return Response({
                'success': False,
                'error': 'Question bank not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(f"Question bank loaded successfully")
        
        return Response({
            'success': True,
            'question_bank': qb
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.error(f"Invalid parameters: {e}")
        return Response({
            'success': False,
            'error': f'Invalid parameters: {e}'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error loading question bank: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_next_lesson(request, class_number, subject):
    """
    2025-10-31: API endpoint to get the next lesson in sequence
    
    GET /api/curriculum/class/{class}/subject/{subject}/next?current_month={m}&current_week={w}&current_day={d}
    
    Args:
        class_number: Class number (1-12)
        subject: Subject name (e.g., 'EVS', 'Math')
    
    Query Parameters:
        current_month: Current month number
        current_week: Current week number
        current_day: Current day number
    
    Returns:
        JSON response with next lesson content
    """
    try:
        # 2025-10-31: Parse parameters
        class_num = int(class_number)
        current_month = int(request.GET.get('current_month', 1))
        current_week = int(request.GET.get('current_week', 1))
        current_day = int(request.GET.get('current_day', 1))
        
        # 2025-10-31: Calculate next lesson coordinates
        next_day = current_day + 1
        next_week = current_week
        next_month = current_month
        
        # 2025-10-31: Handle day overflow (assuming 5 days per week)
        if next_day > 5:
            next_day = 1
            next_week += 1
        
        # 2025-10-31: Handle week overflow (assuming 4 weeks per month)
        if next_week > 4:
            next_week = 1
            next_month += 1
        
        # 2025-10-31: Handle month overflow (assuming 10 months)
        if next_month > 10:
            return Response({
                'success': False,
                'error': 'No more lessons available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        logger.info(
            f"Next lesson requested after: Month {current_month}, Week {current_week}, Day {current_day}"
        )
        logger.info(
            f"Next lesson coordinates: Month {next_month}, Week {next_week}, Day {next_day}"
        )
        
        # 2025-10-31: Load next lesson
        lesson = curriculum_loader.load_lesson(
            class_num, subject, next_month, next_week, next_day
        )
        
        if lesson is None:
            return Response({
                'success': False,
                'error': 'Next lesson not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'success': True,
            'lesson': lesson,
            'coordinates': {
                'month': next_month,
                'week': next_week,
                'day': next_day
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error loading next lesson: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def clear_cache(request):
    """
    2025-10-31: API endpoint to clear curriculum cache
    
    POST /api/curriculum/cache/clear
    
    Body (optional):
        {
            "cache_key": "specific_cache_key"  // Optional, clears all if not provided
        }
    
    Returns:
        JSON response confirming cache clear
    """
    try:
        # 2025-10-31: Get cache_key from request body
        cache_key = request.data.get('cache_key', None)
        
        # 2025-10-31: Clear cache
        curriculum_loader.clear_cache(cache_key)
        
        if cache_key:
            logger.info(f"Cache cleared for key: {cache_key}")
            message = f"Cache cleared for key: {cache_key}"
        else:
            logger.info("All caches cleared")
            message = "All caches cleared"
        
        return Response({
            'success': True,
            'message': message
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
