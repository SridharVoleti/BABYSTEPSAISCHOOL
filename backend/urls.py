# 2025-10-31: URL configuration for BabySteps Digital School backend
# Author: BabySteps Development Team
# Last Modified: 2025-10-31

"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.contrib import admin  # 2025-10-31: Import admin
from django.urls import path, include  # 2025-10-31: Import path and include
from django.http import JsonResponse  # 2025-10-31: Import JsonResponse

# 2025-10-31: Root API endpoint
def api_root(request):
    """2025-10-31: Root API endpoint with available endpoints"""
    return JsonResponse({
        'message': 'BabySteps Digital School API',
        'version': '1.0.0',
        'endpoints': {
            'admin': '/admin/',
            'curriculum': '/api/curriculum/',
            'curriculum_list': '/api/curriculum/list/',
            'lesson_example': '/api/curriculum/class/1/subject/EVS/month/1/week/1/day/1/',
        }
    })

# 2025-10-31: URL patterns
urlpatterns = [
    # Django admin interface
    # Provides web-based database management
    # Access at: http://localhost:8000/admin/
    path('admin/', admin.site.urls),

    # API root endpoint
    # Returns available API endpoints
    # Access at: http://localhost:8000/api/
    path('api/', api_root, name='api-root'),

    # Curriculum loader service endpoints
    # Includes all curriculum-related APIs
    # Mounted at: http://localhost:8000/api/curriculum/
    path('api/curriculum/', include('services.curriculum_loader_service.urls')),

    # Mentor chat service endpoints
    # Includes AI mentor chat APIs
    # Mounted at: http://localhost:8000/api/mentor/
    path('api/mentor/', include('services.mentor_chat_service.urls')),

    # Analytics service endpoints
    # Includes student activity and progress tracking APIs
    # Mounted at: http://localhost:8000/api/analytics/
    path('api/analytics/', include('services.analytics_service.urls')),
    
    # Student registration endpoints
    # 2025-12-13: Includes registration submission and admin approval APIs
    # Mounted at: http://localhost:8000/api/
    path('api/', include('student_registration.urls')),
    
    # Learning engine endpoints
    # 2025-12-18: Micro-lesson learning system with adaptive difficulty
    # Mounted at: http://localhost:8000/api/learning/
    path('api/learning/', include('services.learning_engine.urls')),

    # 2026-02-12: Authentication service endpoints (BS-AUT module)
    # Mounted at: http://localhost:8000/api/v1/auth/
    path('api/v1/auth/', include('services.auth_service.urls')),

    # 2026-02-12: Diagnostic assessment service endpoints (BS-DIA module)
    # Mounted at: http://localhost:8000/api/v1/diagnostic/
    path('api/v1/diagnostic/', include('services.diagnostic_service.urls')),

    # 2026-02-17: AI Teaching Engine endpoints (BS-AIE module)
    # Mounted at: http://localhost:8000/api/v1/teaching/
    path('api/v1/teaching/', include('services.teaching_engine.urls')),
]
