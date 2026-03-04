"""2026-03-04: Monitor Tools Service serializers."""

from rest_framework import serializers  # 2026-03-04: DRF

from .models import GradeBookEntry, HomeworkAssignment, HomeworkSubmission, TimetableSlot


# ============================================================
# Grade Book
# ============================================================

class GradeBookEntrySerializer(serializers.ModelSerializer):
    """2026-03-04: Response serializer for GradeBookEntry."""

    student_name = serializers.CharField(source='student.full_name', read_only=True)
    percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = GradeBookEntry
        fields = [
            'id', 'student_id', 'student_name', 'subject', 'term',
            'assessment_type', 'title', 'score', 'max_score',
            'percentage', 'letter_grade', 'remarks', 'date_recorded', 'created_at',
        ]
        read_only_fields = fields


class AddGradeSerializer(serializers.Serializer):
    """2026-03-04: Request serializer for adding a grade."""

    student_id = serializers.UUIDField()
    subject = serializers.CharField(max_length=50)
    term = serializers.ChoiceField(choices=['T1', 'T2', 'T3'])
    assessment_type = serializers.ChoiceField(choices=['formative', 'summative', 'project'])
    title = serializers.CharField(max_length=100)
    score = serializers.FloatField(min_value=0)
    max_score = serializers.FloatField(min_value=1, default=100.0)
    remarks = serializers.CharField(required=False, default='', allow_blank=True)
    date_recorded = serializers.DateField(required=False)


class GradesQuerySerializer(serializers.Serializer):
    """2026-03-04: Query params for fetching grades."""

    subject = serializers.CharField(required=False)
    term = serializers.ChoiceField(choices=['T1', 'T2', 'T3'], required=False)


# ============================================================
# Homework
# ============================================================

class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    """2026-03-04: Response serializer for HomeworkAssignment."""

    class Meta:
        model = HomeworkAssignment
        fields = ['id', 'grade', 'subject', 'title', 'description', 'due_date', 'is_active', 'created_at']
        read_only_fields = fields


class CreateHomeworkSerializer(serializers.Serializer):
    """2026-03-04: Request serializer for creating homework."""

    grade = serializers.IntegerField(min_value=1, max_value=12)
    subject = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    due_date = serializers.DateField()


class HomeworkSubmissionSerializer(serializers.ModelSerializer):
    """2026-03-04: Response serializer for HomeworkSubmission."""

    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = HomeworkSubmission
        fields = ['id', 'homework_id', 'student_id', 'student_name', 'status', 'note', 'submitted_at']
        read_only_fields = fields


class MarkHomeworkDoneSerializer(serializers.Serializer):
    """2026-03-04: Request to mark homework done."""

    homework_id = serializers.UUIDField()
    note = serializers.CharField(required=False, default='', allow_blank=True)


# ============================================================
# Timetable
# ============================================================

class TimetableSlotSerializer(serializers.ModelSerializer):
    """2026-03-04: Response serializer for TimetableSlot."""

    day_name = serializers.SerializerMethodField()

    class Meta:
        model = TimetableSlot
        fields = [
            'id', 'grade', 'day_of_week', 'day_name', 'start_time',
            'end_time', 'subject', 'teacher_name', 'room', 'is_active',
        ]
        read_only_fields = fields

    def get_day_name(self, obj):
        """2026-03-04: Convert day number to name."""
        return dict(TimetableSlot.DAY_CHOICES).get(obj.day_of_week, '')


class CreateTimetableSlotSerializer(serializers.Serializer):
    """2026-03-04: Request to add a timetable slot."""

    grade = serializers.IntegerField(min_value=1, max_value=12)
    day_of_week = serializers.IntegerField(min_value=1, max_value=6)
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    subject = serializers.CharField(max_length=50)
    teacher_name = serializers.CharField(required=False, default='', allow_blank=True)
    room = serializers.CharField(required=False, default='', allow_blank=True)


class UpdateTimetableSlotSerializer(serializers.Serializer):
    """2026-03-04: Request to update a timetable slot."""

    subject = serializers.CharField(max_length=50, required=False)
    teacher_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    room = serializers.CharField(max_length=50, required=False, allow_blank=True)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)
