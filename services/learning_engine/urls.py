# 2025-12-18: Learning Engine URL Configuration
# Author: BabySteps Development Team
# Purpose: URL routing for learning engine API endpoints
# Last Modified: 2025-12-18

"""
Learning Engine URL Configuration

Defines API endpoints for:
- /api/learning/lessons/ - Micro-lesson CRUD
- /api/learning/progress/ - Student progress tracking
- /api/learning/practice/validate/ - Practice answer validation
- /api/learning/dashboard/ - Student dashboard
- /api/learning/calibration/ - Difficulty calibration
"""

# 2025-12-18: Import Django URL utilities
from django.urls import path, include

# 2025-12-18: Import DRF router
from rest_framework.routers import DefaultRouter

# 2025-12-18: Import views
from .views import (
    MicroLessonViewSet,
    MicroLessonProgressViewSet,
    PracticeValidationView,
    StudentDashboardView,
    DifficultyCalibrationViewSet,
    DailyActivityView,
)

# 2025-12-18: Create router and register viewsets
router = DefaultRouter()
router.register(r'lessons', MicroLessonViewSet, basename='microlesson')
router.register(r'progress', MicroLessonProgressViewSet, basename='progress')
router.register(r'calibration', DifficultyCalibrationViewSet, basename='calibration')

# 2025-12-18: URL patterns
urlpatterns = [
    # 2025-12-18: Include router URLs
    path('', include(router.urls)),
    
    # 2025-12-18: Practice validation endpoint
    path('practice/validate/', PracticeValidationView.as_view(), name='practice-validate'),
    
    # 2025-12-18: Student dashboard endpoint
    path('dashboard/', StudentDashboardView.as_view(), name='student-dashboard'),

    # 2026-02-14: Daily activity endpoint for streak tracking
    path('daily-activity/', DailyActivityView.as_view(), name='daily-activity'),
]
