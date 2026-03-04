"""
2026-03-02: Math Service DRF serializers (BS-MTH module).

Purpose:
    Validate request payloads for math session start, answer submission,
    and hint requests. All fields are documented with help_text.
"""

from rest_framework import serializers  # 2026-03-02: DRF serializers


class StartSessionSerializer(serializers.Serializer):
    """
    2026-03-02: Validates the POST /sessions/ request body.

    Fields:
        lesson_id: MathLesson lesson_id string.
        day_number: Day within the lesson (1-4).
    """

    lesson_id = serializers.CharField(  # 2026-03-02: Lesson identifier
        max_length=50,
        help_text='MathLesson lesson_id, e.g. MATH1_W01',
    )
    day_number = serializers.IntegerField(  # 2026-03-02: Day 1-4
        min_value=1,
        max_value=4,
        help_text='Day number within the lesson (1-4)',
    )


class SubmitAnswerSerializer(serializers.Serializer):
    """
    2026-03-02: Validates the POST /sessions/{id}/answer/ request body.

    Fields:
        problem_id: Problem ID from JSON problem bank.
        answer: Student's answer (string for all types).
        time_taken: Optional seconds taken to answer.
    """

    problem_id = serializers.CharField(  # 2026-03-02: Problem identifier
        max_length=100,
        help_text='Problem ID from the JSON problem bank',
    )
    answer = serializers.CharField(  # 2026-03-02: Student answer
        allow_blank=True,
        help_text='Student answer as a string (index for MCQ, value for numeric)',
    )
    time_taken = serializers.IntegerField(  # 2026-03-02: Optional time
        required=False,
        allow_null=True,
        min_value=0,
        help_text='Seconds taken to answer (optional)',
    )


class RequestHintSerializer(serializers.Serializer):
    """
    2026-03-02: Validates the POST /sessions/{id}/hint/ request body.

    Fields:
        problem_id: Problem ID from JSON problem bank.
    """

    problem_id = serializers.CharField(  # 2026-03-02: Problem identifier
        max_length=100,
        help_text='Problem ID from the JSON problem bank',
    )


class StartDrillSerializer(serializers.Serializer):
    """
    2026-03-03: Validates the POST /drills/ request body (AMT-APE-005).

    Fields:
        drill_type: Type of drill — 'tables', 'squares', or 'cubes'.
        number_range_min: Lower bound for number range (1-20).
        number_range_max: Upper bound for number range (1-20).
        time_limit_seconds: Session duration (30, 60, or 120 seconds).
        total_questions: Number of questions (5-20, default 10).
    """

    DRILL_TYPE_CHOICES = ['tables', 'squares', 'cubes']  # 2026-03-03: Valid types
    TIME_LIMIT_CHOICES = [30, 60, 120]  # 2026-03-03: Valid time limits

    drill_type = serializers.ChoiceField(  # 2026-03-03: Drill type
        choices=DRILL_TYPE_CHOICES,
        help_text="Drill type: 'tables', 'squares', or 'cubes'",
    )
    number_range_min = serializers.IntegerField(  # 2026-03-03: Range lower bound
        min_value=1,
        max_value=20,
        default=1,
        help_text='Lower bound for number range (1-20)',
    )
    number_range_max = serializers.IntegerField(  # 2026-03-03: Range upper bound
        min_value=1,
        max_value=20,
        default=12,
        help_text='Upper bound for number range (1-20)',
    )
    time_limit_seconds = serializers.ChoiceField(  # 2026-03-03: Time limit
        choices=TIME_LIMIT_CHOICES,
        default=60,
        help_text='Session duration in seconds: 30, 60, or 120',
    )
    total_questions = serializers.IntegerField(  # 2026-03-03: Question count
        min_value=5,
        max_value=20,
        default=10,
        help_text='Number of questions in the drill (5-20)',
    )

    def validate(self, data):
        """2026-03-03: Cross-field validation: min must not exceed max."""
        if data['number_range_min'] > data['number_range_max']:
            raise serializers.ValidationError(
                'number_range_min must not be greater than number_range_max.'
            )
        return data


class SubmitDrillAnswerSerializer(serializers.Serializer):
    """
    2026-03-03: Validates the POST /drills/{id}/answer/ request body (AMT-APE-005).

    Fields:
        question_index: 0-based index of the question being answered.
        answer: Student's answer string (numeric value as text).
        response_time_ms: Optional time taken to answer in milliseconds.
    """

    question_index = serializers.IntegerField(  # 2026-03-03: Question index
        min_value=0,
        help_text='0-based index of the question being answered',
    )
    answer = serializers.CharField(  # 2026-03-03: Student answer
        max_length=20,
        help_text='Student answer as a string (numeric value)',
    )
    response_time_ms = serializers.IntegerField(  # 2026-03-03: Optional timing
        required=False,
        allow_null=True,
        min_value=0,
        help_text='Time taken to answer in milliseconds (optional)',
    )


class TeachingChatSerializer(serializers.Serializer):
    """
    2026-03-02: Validates POST /sessions/{id}/teach/chat/ request body (BS-AMT-001).

    Fields:
        message: Student's question or response text during teaching phase.
    """

    message = serializers.CharField(  # 2026-03-02: Student message
        max_length=500,
        help_text='Student message text (question or response) during teaching phase',
    )
