"""
2026-03-06: Serializers for Mentor Dashboard Service (BS-MNT).

Purpose:
    Input validation for mentor review submission and parent message drafting.
"""

from rest_framework import serializers  # 2026-03-06: DRF serializers


class ReviewSubmitSerializer(serializers.Serializer):
    """
    2026-03-06: Validates mentor score submission for a comprehension response.

    Fields:
        mentor_score: int 0-5 (0=fail, 1-5=quality level)
        mentor_notes: optional text notes from the mentor
    """

    mentor_score = serializers.IntegerField(  # 2026-03-06: Quality score
        min_value=0,
        max_value=5,
        help_text='0=fail, 1-5=quality rating',
    )
    mentor_notes = serializers.CharField(  # 2026-03-06: Optional notes
        allow_blank=True,
        required=False,
        default='',
        max_length=2000,
    )


class DraftMessageSerializer(serializers.Serializer):
    """
    2026-03-06: Validates context_hint for AI parent message drafting.

    Fields:
        context_hint: optional free-text hint for the LLM (max 200 chars)
    """

    context_hint = serializers.CharField(  # 2026-03-06: Optional focus hint
        allow_blank=True,
        required=False,
        default='',
        max_length=200,
    )
