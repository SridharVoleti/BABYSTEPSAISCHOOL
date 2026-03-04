"""
2026-03-04: Attendance Service serializers.

Purpose:
    DRF serializers for request validation and response formatting.
"""

from datetime import date  # 2026-03-04: Date field

from rest_framework import serializers  # 2026-03-04: DRF serializers

from .models import AttendanceRecord  # 2026-03-04: Model


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """2026-03-04: Full serializer for AttendanceRecord response."""

    student_name = serializers.CharField(  # 2026-03-04: Denorm for convenience
        source='student.full_name', read_only=True
    )

    class Meta:
        """2026-03-04: Meta options."""

        model = AttendanceRecord
        fields = [
            'id', 'student_id', 'student_name', 'date', 'status',
            'check_in_time', 'check_out_time', 'session_duration_minutes',
            'recorded_by', 'notes', 'created_at',
        ]
        read_only_fields = fields  # 2026-03-04: All read-only (writes via service)


class MarkAttendanceSerializer(serializers.Serializer):
    """2026-03-04: Serializer for manual attendance marking by monitor."""

    student_id = serializers.UUIDField()  # 2026-03-04: Target student UUID
    date = serializers.DateField()  # 2026-03-04: Target date
    status = serializers.ChoiceField(  # 2026-03-04: Attendance status
        choices=[c[0] for c in AttendanceRecord.STATUS_CHOICES]
    )
    notes = serializers.CharField(  # 2026-03-04: Optional notes
        required=False, default='', allow_blank=True
    )


class BulkMarkAttendanceSerializer(serializers.Serializer):
    """2026-03-04: Serializer for bulk marking an entire class."""

    grade = serializers.IntegerField(min_value=1, max_value=12)  # 2026-03-04: Class
    date = serializers.DateField()  # 2026-03-04: Target date
    records = serializers.ListField(  # 2026-03-04: Per-student overrides
        child=serializers.DictField(),
        required=False,
        default=list,
    )


class AttendanceSummaryQuerySerializer(serializers.Serializer):
    """2026-03-04: Query params for monthly summary."""

    year = serializers.IntegerField(  # 2026-03-04: Calendar year
        min_value=2024, max_value=2050, required=False
    )
    month = serializers.IntegerField(  # 2026-03-04: Month (1-12)
        min_value=1, max_value=12, required=False
    )


class ClassAttendanceQuerySerializer(serializers.Serializer):
    """2026-03-04: Query params for daily class roster."""

    grade = serializers.IntegerField(min_value=1, max_value=12)  # 2026-03-04: Class
    date = serializers.DateField(required=False)  # 2026-03-04: Default today
