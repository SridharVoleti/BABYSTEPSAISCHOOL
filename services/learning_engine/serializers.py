# 2025-12-18: Learning Engine Serializers
# Author: BabySteps Development Team
# Purpose: DRF serializers for learning engine API
# Last Modified: 2025-12-18

"""
Learning Engine Serializers

Provides serializers for:
- MicroLesson: Full lesson content delivery
- MicroLessonProgress: Student progress tracking
- PracticeAttempt: Practice question submission and validation
- StudentLearningProfile: Student profile and stats
- DifficultyCalibration: Adaptive difficulty settings
"""

# 2025-12-18: Import DRF serializers
from rest_framework import serializers

# 2025-12-18: Import models
from .models import (
    StudentLearningProfile,
    MicroLesson,
    MicroLessonProgress,
    PracticeAttempt,
    DifficultyCalibration,
)


class StudentLearningProfileSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Serializer for StudentLearningProfile.
    Includes computed fields for dashboard display.
    """
    
    # 2025-12-18: Include username from related user
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = StudentLearningProfile
        fields = [
            'id',
            'username',
            'learning_speed',
            'preferred_explanation_mode',
            'error_patterns',
            'weak_concepts',
            'strong_concepts',
            'total_mastery_points',
            'current_streak_days',
            'longest_streak_days',
            'last_activity_date',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'total_mastery_points',
            'current_streak_days',
            'longest_streak_days',
            'last_activity_date',
            'created_at',
            'updated_at',
        ]


class MicroLessonListSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Lightweight serializer for lesson listing.
    Excludes heavy content fields for performance.
    """
    
    # 2025-12-18: Include validation status
    is_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = MicroLesson
        fields = [
            'id',
            'lesson_id',
            'title',
            'learning_objective',
            'subject',
            'class_number',
            'chapter_id',
            'chapter_name',
            'sequence_in_chapter',
            'duration_minutes',
            'qa_status',
            'is_published',
            'is_valid',
            'language',
            'version',
        ]
    
    def get_is_valid(self, obj):
        """2025-12-18: Check if lesson structure is valid."""
        is_valid, _ = obj.validate_structure()
        return is_valid


class MicroLessonDetailSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Full serializer for lesson detail view.
    Includes all content for lesson delivery.
    """
    
    # 2025-12-18: Include validation details
    validation_status = serializers.SerializerMethodField()
    
    # 2025-12-18: Include student's progress if authenticated
    student_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = MicroLesson
        fields = [
            'id',
            'lesson_id',
            'title',
            'learning_objective',
            'subject',
            'class_number',
            'chapter_id',
            'chapter_name',
            'sequence_in_chapter',
            'duration_minutes',
            'worked_examples',
            'practice_questions',
            'practice_themes',
            'visual_assets',
            'teacher_narration',
            'textbook_reading',
            'misconceptions',
            'prerequisites',
            'qa_status',
            'is_published',
            'language',
            'localization_variants',
            'version',
            'validation_status',
            'student_progress',
        ]
    
    def get_validation_status(self, obj):
        """2025-12-18: Get validation status with errors if any."""
        is_valid, errors = obj.validate_structure()
        return {
            'is_valid': is_valid,
            'errors': errors
        }
    
    def get_student_progress(self, obj):
        """2025-12-18: Get current user's progress on this lesson."""
        request = self.context.get('request')
        # 2025-12-18: Check if request exists and user is authenticated
        if request and hasattr(request, 'user') and request.user and request.user.is_authenticated:
            progress = MicroLessonProgress.objects.filter(
                student=request.user,
                micro_lesson=obj
            ).order_by('-attempt_number').first()
            if progress:
                return MicroLessonProgressSerializer(progress).data
        return None


class MicroLessonProgressSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Serializer for MicroLessonProgress.
    Tracks student's journey through a lesson.
    """
    
    # 2025-12-18: Include lesson info
    lesson_id = serializers.CharField(source='micro_lesson.lesson_id', read_only=True)
    lesson_title = serializers.CharField(source='micro_lesson.title', read_only=True)
    
    # 2025-12-18: Include accuracy percentage
    accuracy_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = MicroLessonProgress
        fields = [
            'id',
            'lesson_id',
            'lesson_title',
            'status',
            'current_step',
            'questions_attempted',
            'questions_correct',
            'accuracy_percentage',
            'mastery_score',
            'time_spent_seconds',
            'attempt_number',
            'difficulty_level',
            'hints_used',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'lesson_id',
            'lesson_title',
            'mastery_score',
            'created_at',
            'updated_at',
        ]
    
    def get_accuracy_percentage(self, obj):
        """2025-12-18: Calculate accuracy as percentage."""
        if obj.questions_attempted == 0:
            return 0
        return round((obj.questions_correct / obj.questions_attempted) * 100, 1)


class PracticeAttemptSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Serializer for PracticeAttempt.
    Records individual question attempts.
    """
    
    class Meta:
        model = PracticeAttempt
        fields = [
            'id',
            'lesson_progress',
            'question_index',
            'question_content',
            'student_answer',
            'correct_answer',
            'is_correct',
            'partial_credit',
            'time_taken_seconds',
            'hints_used',
            'retry_count',
            'feedback_shown',
            'misconception_detected',
            'attempted_at',
        ]
        read_only_fields = [
            'id',
            'is_correct',
            'partial_credit',
            'feedback_shown',
            'misconception_detected',
            'attempted_at',
        ]


class PracticeSubmissionSerializer(serializers.Serializer):
    """
    2025-12-18: Serializer for submitting a practice answer.
    Used for real-time validation endpoint.
    """
    
    # 2025-12-18: Required fields
    lesson_progress_id = serializers.IntegerField(
        help_text="ID of the MicroLessonProgress record"
    )
    question_index = serializers.IntegerField(
        min_value=1,
        max_value=10,
        help_text="Question number (1-10)"
    )
    student_answer = serializers.CharField(
        help_text="Student's submitted answer"
    )
    time_taken_seconds = serializers.IntegerField(
        min_value=0,
        help_text="Time taken to answer in seconds"
    )
    
    # 2025-12-18: Optional fields
    hints_requested = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Number of hints used for this question"
    )
    retry_count = serializers.IntegerField(
        default=0,
        min_value=0,
        help_text="Number of retries for this question"
    )


class PracticeValidationResponseSerializer(serializers.Serializer):
    """
    2025-12-18: Serializer for practice validation response.
    Provides immediate feedback to student.
    """
    
    # 2025-12-18: Result fields
    is_correct = serializers.BooleanField()
    partial_credit = serializers.FloatField()
    
    # 2025-12-18: Feedback fields
    correct_answer = serializers.CharField()
    step_by_step_solution = serializers.ListField(
        child=serializers.CharField(),
        help_text="Step-by-step solution explanation"
    )
    common_misconception = serializers.CharField(
        allow_blank=True,
        help_text="Relevant misconception if answer was wrong"
    )
    
    # 2025-12-18: Encouragement
    feedback_message = serializers.CharField(
        help_text="Personalized feedback message"
    )
    
    # 2025-12-18: Progress update
    questions_remaining = serializers.IntegerField()
    current_accuracy = serializers.FloatField()
    
    # 2025-12-18: Adaptive hint (for weak students)
    adaptive_hint = serializers.CharField(
        allow_blank=True,
        help_text="Additional hint for struggling students"
    )


class DifficultyCalibrationSerializer(serializers.ModelSerializer):
    """
    2025-12-18: Serializer for DifficultyCalibration.
    Shows adaptive difficulty settings.
    """
    
    # 2025-12-18: Include username
    username = serializers.CharField(source='student.username', read_only=True)
    
    class Meta:
        model = DifficultyCalibration
        fields = [
            'id',
            'username',
            'subject',
            'current_difficulty',
            'rolling_accuracy',
            'avg_time_per_question',
            'avg_retries',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'username',
            'rolling_accuracy',
            'avg_time_per_question',
            'avg_retries',
            'created_at',
            'updated_at',
        ]


class StudentDashboardSerializer(serializers.Serializer):
    """
    2025-12-18: Serializer for student dashboard data.
    Aggregates progress, mastery, and streaks.
    """
    
    # 2025-12-18: Profile info
    profile = StudentLearningProfileSerializer()
    
    # 2025-12-18: Progress summary
    total_lessons_completed = serializers.IntegerField()
    total_lessons_in_progress = serializers.IntegerField()
    overall_mastery_average = serializers.FloatField()
    
    # 2025-12-18: Recent activity
    recent_lessons = MicroLessonProgressSerializer(many=True)
    
    # 2025-12-18: Skill heatmap data
    skill_heatmap = serializers.DictField(
        help_text="Mastery scores by chapter/topic"
    )
    
    # 2025-12-18: Recommendations
    recommended_lessons = MicroLessonListSerializer(many=True)
    revision_needed = MicroLessonListSerializer(many=True)


class LessonProgressUpdateSerializer(serializers.Serializer):
    """
    2025-12-18: Serializer for updating lesson progress.
    Used when student advances through lesson steps.
    """
    
    # 2025-12-18: Progress update fields
    current_step = serializers.ChoiceField(
        choices=[
            ('objective', 'Viewing Objective'),
            ('visual_intro', 'Visual Introduction'),
            ('worked_example_1', 'Worked Example 1'),
            ('worked_example_2', 'Worked Example 2'),
            ('practice', 'Practice Questions'),
            ('mastery_check', 'Mastery Checkpoint'),
            ('completed', 'Completed'),
        ],
        help_text="New step in lesson flow"
    )
    time_spent_seconds = serializers.IntegerField(
        min_value=0,
        help_text="Additional time spent"
    )
    
    # 2025-12-18: Optional status update
    status = serializers.ChoiceField(
        choices=[
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('mastered', 'Mastered'),
        ],
        required=False,
        help_text="New status if changed"
    )
