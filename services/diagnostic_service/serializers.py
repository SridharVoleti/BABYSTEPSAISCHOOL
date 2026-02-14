"""
2026-02-12: Diagnostic assessment service serializers.

Purpose:
    DRF serializers for diagnostic API request/response validation.
"""

from rest_framework import serializers  # 2026-02-12: DRF serializers


class DiagnosticRespondSerializer(serializers.Serializer):
    """2026-02-12: Serializer for submitting a diagnostic response."""

    item_id = serializers.CharField(  # 2026-02-12: Question bank item ID
        max_length=50,
        help_text='The ID of the item being answered.',
    )
    selected_option = serializers.IntegerField(  # 2026-02-13: Option index or numeric answer
        min_value=0,
        help_text='Index of selected option (MCQ: 0-3, T/F: 0-1) or numeric answer value.',
    )
    response_time_ms = serializers.IntegerField(  # 2026-02-12: Time to respond
        min_value=0,
        required=False,
        default=0,
        help_text='Time to respond in milliseconds.',
    )
