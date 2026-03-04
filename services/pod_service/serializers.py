"""
2026-03-04: Pod Service serializers for input validation.

Purpose:
    Validate incoming data for heartbeat, attention events,
    help requests, enrollment actions, and alert resolution.
"""

from rest_framework import serializers  # 2026-03-04: DRF serializers

from .models import ATTENTION_EVENT_TYPES  # 2026-03-04: Choices


class HeartbeatSerializer(serializers.Serializer):
    """2026-03-04: Validates heartbeat POST (no required fields — student from JWT)."""

    pass  # 2026-03-04: No body needed; student is derived from JWT


class AttentionEventSerializer(serializers.Serializer):
    """2026-03-04: Validates an attention event report from the client."""

    VALID_TYPES = [t[0] for t in ATTENTION_EVENT_TYPES]  # 2026-03-04: Allowed types

    event_type = serializers.ChoiceField(  # 2026-03-04: Must be a valid type
        choices=VALID_TYPES,
    )
    ai_response = serializers.CharField(  # 2026-03-04: What TTS said
        max_length=500,
        required=False,
        allow_blank=True,
        default='',
    )
    escalated = serializers.BooleanField(  # 2026-03-04: Parent notified?
        required=False,
        default=False,
    )


class HelpRequestSerializer(serializers.Serializer):
    """2026-03-04: Validates a student help request."""

    message = serializers.CharField(  # 2026-03-04: Optional custom message
        max_length=500,
        required=False,
        allow_blank=True,
        default='',
    )


class EnrollStudentSerializer(serializers.Serializer):
    """2026-03-04: Validates enroll/unenroll POST body."""

    student_id = serializers.UUIDField()  # 2026-03-04: Student UUID


class ResolveAlertSerializer(serializers.Serializer):
    """2026-03-04: Validates alert resolution request."""

    alert_id = serializers.IntegerField(min_value=1)  # 2026-03-04: Alert integer PK
