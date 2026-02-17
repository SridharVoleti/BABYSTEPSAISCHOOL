"""
2026-02-17: AI Teaching Engine serializers.

Purpose:
    DRF serializers for teaching engine API request validation.
"""

from rest_framework import serializers  # 2026-02-17: DRF serializers


class StartDaySerializer(serializers.Serializer):
    """2026-02-17: Serializer for starting a day's micro-lesson."""

    day_number = serializers.IntegerField(  # 2026-02-17: Optional day override
        min_value=1, max_value=4,
        required=False,
        help_text='Day number (1-4). Defaults to current day.',
    )


class CompleteDaySerializer(serializers.Serializer):
    """2026-02-17: Serializer for completing a day's micro-lesson."""

    day_number = serializers.IntegerField(  # 2026-02-17: Day being completed
        min_value=1, max_value=4,
        help_text='Day number (1-4) being completed.',
    )
    practice_answers = serializers.DictField(  # 2026-02-17: Answers map
        child=serializers.IntegerField(min_value=0),
        help_text='Map of question_id -> selected option index.',
    )
    time_spent = serializers.IntegerField(  # 2026-02-17: Time in seconds
        min_value=0,
        help_text='Time spent in seconds.',
    )


class SubmitAssessmentSerializer(serializers.Serializer):
    """2026-02-17: Serializer for submitting a weekly assessment."""

    answers = serializers.DictField(  # 2026-02-17: Answers map
        child=serializers.IntegerField(min_value=0),
        help_text='Map of question_id -> selected option index.',
    )
    time_spent = serializers.IntegerField(  # 2026-02-17: Time in seconds
        min_value=0,
        help_text='Time spent in seconds.',
    )


class TutoringChatSerializer(serializers.Serializer):
    """2026-02-17: Serializer for tutoring chat messages."""

    message = serializers.CharField(  # 2026-02-17: Student message
        max_length=1000,
        help_text='Student message text.',
    )
    lesson_id = serializers.CharField(  # 2026-02-17: Optional lesson context
        max_length=100, required=False,
        help_text='Lesson ID for context.',
    )
    day_number = serializers.IntegerField(  # 2026-02-17: Optional day context
        min_value=1, max_value=4, required=False,
        help_text='Day number for context.',
    )
