"""
2026-02-27: URL routing for Spaced Repetition Service (BS-SPC).

All endpoints mounted under /api/v1/spaced-repetition/.
"""
from django.urls import path  # 2026-02-27: URL pattern helper

from .views import PacingView, ReviewQueueView, ReviewCompleteView  # 2026-02-27: Views

app_name = 'spaced_repetition_service'

urlpatterns = [
    # 2026-02-27: GET /api/v1/spaced-repetition/pacing/
    path('pacing/', PacingView.as_view(), name='pacing'),

    # 2026-02-27: GET /api/v1/spaced-repetition/reviews/today/
    path('reviews/today/', ReviewQueueView.as_view(), name='review-queue'),

    # 2026-02-27: POST /api/v1/spaced-repetition/reviews/complete/
    path('reviews/complete/', ReviewCompleteView.as_view(), name='review-complete'),
]
