# 2025-10-31: Curriculum Loader Service - URL Configuration
# Author: BabySteps Development Team
# Purpose: URL routing for curriculum API endpoints
# Last Modified: 2025-10-31

"""
Curriculum Loader URL Configuration

Defines URL patterns for curriculum API endpoints.
"""

from django.urls import path  # 2025-10-31: Import path function
from . import views  # 2025-10-31: Import views module

# 2025-10-31: Define app name for namespacing
app_name = 'curriculum'

# 2025-10-31: Define URL patterns
urlpatterns = [
    # 2025-10-31: List all available curriculums
    path('list/', views.curriculum_list, name='curriculum_list'),
    
    # 2025-10-31: Get specific lesson
    path(
        'class/<int:class_number>/subject/<str:subject>/month/<int:month>/week/<int:week>/day/<int:day>/',
        views.get_lesson,
        name='get_lesson'
    ),
    
    # 2025-10-31: Get question bank for specific lesson
    path(
        'class/<int:class_number>/subject/<str:subject>/month/<int:month>/week/<int:week>/day/<int:day>/qb/',
        views.get_question_bank,
        name='get_question_bank'
    ),
    
    # 2025-10-31: Get next lesson in sequence
    path(
        'class/<int:class_number>/subject/<str:subject>/next/',
        views.get_next_lesson,
        name='get_next_lesson'
    ),
    
    # 2025-10-31: Clear cache
    path('cache/clear/', views.clear_cache, name='clear_cache'),
]
