"""
2026-02-19: Django admin configuration for Comprehension Capture Engine (BS-CMP).

Purpose:
    Register ComprehensionEvaluation with the Django admin site, providing
    list display, filtering, search, and readonly computed fields.
"""

from django.contrib import admin  # 2026-02-19: Django admin

from .models import ComprehensionEvaluation, ComprehensionQuestionResponse  # 2026-02-19: Models


@admin.register(ComprehensionEvaluation)
class ComprehensionEvaluationAdmin(admin.ModelAdmin):
    """
    2026-02-19: Admin view for ComprehensionEvaluation records.

    Displays key fields for quick review and supports filtering by
    parroting status, LLM error flag, and star rating.
    """

    list_display = [  # 2026-02-19: Table columns
        'student',
        'lesson',
        'day_number',
        'attempt_number',
        'is_parroting',
        'comprehension_score',
        'weighted_star_rating',
        'llm_error',
        'created_at',
    ]

    list_filter = [  # 2026-02-19: Filter panel
        'is_parroting',
        'llm_error',
        'weighted_star_rating',
        'day_number',
    ]

    search_fields = [  # 2026-02-19: Search bar
        'student__full_name',
        'lesson__lesson_id',
        'lesson__title',
        'student_text',
    ]

    readonly_fields = [  # 2026-02-19: Computed / auto fields
        'id',
        'comprehension_score',
        'weighted_score',
        'weighted_star_rating',
        'attempt_number',
        'created_at',
    ]

    fieldsets = [  # 2026-02-19: Organised field groups
        ('Context', {
            'fields': ['id', 'student', 'lesson', 'day_number', 'attempt_number', 'created_at'],
        }),
        ('Student Explanation', {
            'fields': ['student_text', 'is_parroting'],
        }),
        ('LLM Scores', {
            'fields': [
                'score_understanding', 'score_accuracy', 'score_own_words',
                'score_depth', 'score_clarity', 'comprehension_score',
                'llm_feedback', 'llm_error',
            ],
        }),
        ('Weighted Formula', {
            'fields': [
                'practice_stars', 'application_score', 'retention_score',
                'weighted_score', 'weighted_star_rating',
            ],
        }),
    ]

    ordering = ['-created_at']  # 2026-02-19: Newest first


@admin.register(ComprehensionQuestionResponse)
class ComprehensionQuestionResponseAdmin(admin.ModelAdmin):
    """
    2026-02-21: Admin view for ComprehensionQuestionResponse records (BS-CMP v2).

    Allows administrators to review per-question articulation attempts,
    filter by LLM error status, and search by student or question ID.
    """

    list_display = [  # 2026-02-21: Table columns
        'student',
        'lesson',
        'day_number',
        'question_id',
        'marks_awarded',
        'marks_available',
        'input_method',
        'attempt_number',
        'llm_error',
        'created_at',
    ]

    list_filter = [  # 2026-02-21: Filter panel
        'llm_error',
        'input_method',
        'day_number',
        'marks_available',
    ]

    search_fields = [  # 2026-02-21: Search bar
        'student__full_name',
        'lesson__lesson_id',
        'question_id',
        'student_text',
    ]

    readonly_fields = [  # 2026-02-21: Computed / auto fields
        'id',
        'marks_awarded',
        'key_points_covered',
        'attempt_number',
        'created_at',
    ]

    fieldsets = [  # 2026-02-21: Organised field groups
        ('Context', {
            'fields': [
                'id', 'student', 'lesson', 'day_number',
                'question_id', 'question_text', 'marks_available',
                'attempt_number', 'created_at',
            ],
        }),
        ('Student Answer', {
            'fields': ['student_text', 'input_method'],
        }),
        ('Evaluation', {
            'fields': [
                'key_points_covered', 'marks_awarded',
                'llm_feedback', 'llm_error',
            ],
        }),
    ]

    ordering = ['-created_at']  # 2026-02-21: Newest first
