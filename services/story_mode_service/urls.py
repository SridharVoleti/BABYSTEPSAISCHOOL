"""
2026-02-27: URL routing for Story Mode Service (BS-GAM-003).

All endpoints mounted under /api/v1/story/.
"""
from django.urls import path  # 2026-02-27: URL path registration

from .views import StoryProgressView, StorySceneView  # 2026-02-27: View classes

app_name = 'story_mode_service'  # 2026-02-27: Namespace for URL reversals

urlpatterns = [
    # 2026-02-27: GET /api/v1/story/progress/
    path('progress/', StoryProgressView.as_view(), name='progress'),

    # 2026-02-27: GET /api/v1/story/scene/<scene_id>/
    path('scene/<str:scene_id>/', StorySceneView.as_view(), name='scene-detail'),
]
