"""2026-03-04: Communication Service serializers."""

from rest_framework import serializers

from .models import Announcement, Message, MessageThread, TermReport, WeeklyProgressReport


class MessageSerializer(serializers.ModelSerializer):
    """2026-03-04: Single message in a thread."""

    class Meta:
        model = Message
        fields = ['id', 'sender_type', 'body', 'is_read', 'created_at']
        read_only_fields = fields


class MessageThreadSerializer(serializers.ModelSerializer):
    """2026-03-04: Thread summary."""

    student_name = serializers.CharField(source='student.full_name', read_only=True)
    parent_name = serializers.CharField(source='parent.full_name', read_only=True)
    monitor_name = serializers.CharField(source='monitor.get_full_name', read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ['id', 'student_id', 'student_name', 'parent_name', 'monitor_name',
                  'subject', 'is_closed', 'unread_count', 'created_at', 'updated_at']
        read_only_fields = fields

    def get_unread_count(self, obj):
        """2026-03-04: Unread messages in thread."""
        return obj.messages.filter(is_read=False).count()


class StartThreadSerializer(serializers.Serializer):
    """2026-03-04: Request to start or open a thread."""

    student_id = serializers.UUIDField()
    monitor_id = serializers.IntegerField()   # 2026-03-04: Django User PK
    subject = serializers.CharField(max_length=200, required=False, default='')


class SendMessageSerializer(serializers.Serializer):
    """2026-03-04: Request to send a message."""

    thread_id = serializers.UUIDField()
    body = serializers.CharField(min_length=1)


class AnnouncementSerializer(serializers.ModelSerializer):
    """2026-03-04: Announcement response."""

    author = serializers.CharField(source='created_by.get_full_name', read_only=True, default='')

    class Meta:
        model = Announcement
        fields = ['id', 'title', 'body', 'audience', 'grades', 'priority',
                  'author', 'is_active', 'publish_at', 'expires_at', 'created_at']
        read_only_fields = fields


class CreateAnnouncementSerializer(serializers.Serializer):
    """2026-03-04: Request to create an announcement."""

    title = serializers.CharField(max_length=200)
    body = serializers.CharField()
    audience = serializers.ChoiceField(choices=['all', 'grade', 'parents'], default='all')
    grades = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    priority = serializers.ChoiceField(choices=['low', 'normal', 'high'], default='normal')


class WeeklyReportSerializer(serializers.ModelSerializer):
    """2026-03-04: Weekly progress report response."""

    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = WeeklyProgressReport
        fields = [
            'id', 'student_id', 'student_name', 'week_start', 'week_end',
            'summary_text', 'highlights', 'areas_of_improvement',
            'attendance_days', 'lessons_completed', 'avg_star_rating',
            'generated_at',
        ]
        read_only_fields = fields


class GenerateWeeklyReportSerializer(serializers.Serializer):
    """2026-03-04: Request to generate a weekly report."""

    student_id = serializers.UUIDField()
    week_start = serializers.DateField()  # 2026-03-04: Monday of the week
    attendance_days = serializers.IntegerField(min_value=0, max_value=7, required=False, default=0)
    lessons_completed = serializers.IntegerField(min_value=0, required=False, default=0)
    avg_star_rating = serializers.FloatField(required=False, allow_null=True, default=None)


class TermReportSerializer(serializers.ModelSerializer):
    """2026-03-04: Term report summary."""

    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = TermReport
        fields = ['id', 'student_id', 'student_name', 'academic_year', 'term',
                  'report_data', 'generated_at']
        read_only_fields = fields


class GenerateTermReportSerializer(serializers.Serializer):
    """2026-03-04: Request to generate a term report."""

    student_id = serializers.UUIDField()
    academic_year = serializers.CharField(max_length=9)  # 2026-03-04: e.g. '2025-2026'
    term = serializers.ChoiceField(choices=['T1', 'T2', 'T3'])
