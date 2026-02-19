"""
2026-02-19: Parent Dashboard serializers.

Purpose:
    Validate incoming data for parental controls updates.
"""

from rest_framework import serializers  # 2026-02-19: DRF serializers


class ParentalControlsUpdateSerializer(serializers.Serializer):
    """
    2026-02-19: Validate parental controls update payload.

    All fields are optional (partial update semantics).
    """

    daily_time_limit_minutes = serializers.IntegerField(  # 2026-02-19: 15–480 min
        min_value=15, max_value=480, required=False
    )
    schedule_enabled = serializers.BooleanField(  # 2026-02-19: Toggle schedule
        required=False
    )
    schedule_start_time = serializers.TimeField(  # 2026-02-19: HH:MM
        required=False, allow_null=True
    )
    schedule_end_time = serializers.TimeField(  # 2026-02-19: HH:MM
        required=False, allow_null=True
    )
    ai_log_enabled = serializers.BooleanField(  # 2026-02-19: Toggle AI log
        required=False
    )
