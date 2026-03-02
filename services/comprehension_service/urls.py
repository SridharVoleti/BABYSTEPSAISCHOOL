"""
2026-02-19: URL patterns for the Comprehension Capture Engine (BS-CMP).

Endpoints (holistic evaluation — BS-CMP v1):
    POST  /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/explain/
    GET   /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/best/

Endpoints (marks-based articulation — BS-CMP v2):
    GET   /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/questions/
    POST  /api/v1/comprehension/lessons/<lesson_id>/day/<day_number>/questions/<question_id>/answer/
"""

from django.urls import path  # 2026-02-19: URL helper

from .views import (  # 2026-02-19: Views
    SubmitExplanationView,
    BestEvaluationView,
    DayQuestionsView,  # 2026-02-21: BS-CMP marks-based
    SubmitQuestionAnswerView,  # 2026-02-21: BS-CMP marks-based
)

urlpatterns = [  # 2026-02-19: Comprehension engine URL patterns
    # 2026-02-19: Holistic evaluation endpoints (v1)
    path(
        'lessons/<uuid:lesson_id>/day/<int:day_number>/explain/',
        SubmitExplanationView.as_view(),
        name='comprehension-submit',
    ),  # 2026-02-19: Submit holistic explanation
    path(
        'lessons/<uuid:lesson_id>/day/<int:day_number>/best/',
        BestEvaluationView.as_view(),
        name='comprehension-best',
    ),  # 2026-02-19: Get best holistic evaluation

    # 2026-02-21: Marks-based articulation endpoints (v2)
    path(
        'lessons/<uuid:lesson_id>/day/<int:day_number>/questions/',
        DayQuestionsView.as_view(),
        name='comprehension-day-questions',
    ),  # 2026-02-21: List questions for a day
    path(
        'lessons/<uuid:lesson_id>/day/<int:day_number>/questions/<str:question_id>/answer/',
        SubmitQuestionAnswerView.as_view(),
        name='comprehension-submit-answer',
    ),  # 2026-02-21: Submit answer to a specific question
]
