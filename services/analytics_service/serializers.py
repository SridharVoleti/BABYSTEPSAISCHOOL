"""
Analytics Service API Serializers

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Django REST Framework serializers for analytics models.
    Handles serialization/deserialization of analytics data for API endpoints.

Serialization Features:
    - Convert models to JSON and vice versa
    - Field validation
    - Nested serialization for related objects
    - Read-only computed fields
    - Custom field representations
"""

# Django REST Framework imports
from rest_framework import serializers

# Django imports
from django.contrib.auth import get_user_model

# Import models
from .models import StudentActivity, StudentProgress

# Get User model
User = get_user_model()


class StudentActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for StudentActivity model.
    
    Purpose:
        - Convert StudentActivity instances to JSON
        - Validate incoming activity data
        - Include computed fields in API responses
    
    Fields:
        - All model fields
        - student_username (read-only computed)
        - duration_minutes (read-only computed)
        - engagement_percentage (read-only computed)
    """
    
    # Read-only computed fields
    # These are included in responses but not required in requests
    student_username = serializers.CharField(
        source='student.username',
        read_only=True,
        help_text="Username of the student"
    )
    
    # Duration in minutes for easier consumption
    duration_minutes = serializers.SerializerMethodField(
        read_only=True,
        help_text="Activity duration in minutes"
    )
    
    # Engagement as percentage for display
    engagement_percentage = serializers.SerializerMethodField(
        read_only=True,
        help_text="Engagement score as percentage"
    )
    
    class Meta:
        """
        Serializer metadata configuration.
        
        Attributes:
            model: The model class to serialize
            fields: List of fields to include in serialization
            read_only_fields: Fields that cannot be modified via API
            extra_kwargs: Additional field configurations
        """
        model = StudentActivity
        
        # Include all fields in serialization
        # '__all__' includes every model field
        fields = '__all__'
        
        # Add computed fields
        # These are appended to model fields
        extra_fields = [
            'student_username',
            'duration_minutes',
            'engagement_percentage',
        ]
        
        # Fields that should not be writable via API
        # System-managed fields
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
            'duration_seconds',  # Auto-calculated
            'engagement_score',  # Auto-calculated
        ]
        
        # Additional field configurations
        extra_kwargs = {
            'metadata': {
                'required': False,
                'help_text': 'Additional activity metadata as JSON'
            },
            'ended_at': {
                'required': False,
                'help_text': 'When activity ended (null if ongoing)'
            },
            'is_completed': {
                'default': False,
                'help_text': 'Whether activity was completed'
            },
        }
    
    def get_duration_minutes(self, obj):
        """
        Calculate duration in minutes.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            float: Duration in minutes, or None if not ended
            
        Purpose:
            - Provide duration in more readable unit
            - Frontend can display "5.5 minutes" instead of "330 seconds"
        """
        if obj.duration_seconds is None:
            return None
        
        # Convert seconds to minutes with 2 decimal places
        return round(obj.duration_seconds / 60, 2)
    
    def get_engagement_percentage(self, obj):
        """
        Get engagement score as percentage.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            float: Engagement percentage, or None if not calculated
        """
        if obj.engagement_score is None:
            return None
        
        # Return as float for JSON serialization
        return float(obj.engagement_score)
    
    def validate_started_at(self, value):
        """
        Validate that started_at is not in the future.
        
        Args:
            value: DateTime value to validate
            
        Returns:
            DateTime: Validated value
            
        Raises:
            ValidationError: If date is in future
            
        Purpose:
            - Prevent data entry errors
            - Ensure data integrity
        """
        from django.utils import timezone
        
        # Check if date is in future
        if value > timezone.now():
            raise serializers.ValidationError(
                "Activity start time cannot be in the future."
            )
        
        return value
    
    def validate(self, data):
        """
        Object-level validation.
        
        Args:
            data: Dictionary of all field values
            
        Returns:
            dict: Validated data
            
        Raises:
            ValidationError: If validation fails
            
        Purpose:
            - Validate relationships between fields
            - Check business logic constraints
        """
        # If ended_at is provided, validate it's after started_at
        if 'ended_at' in data and data['ended_at'] is not None:
            started_at = data.get('started_at')
            if started_at and data['ended_at'] < started_at:
                raise serializers.ValidationError(
                    "Activity end time must be after start time."
                )
        
        return data


class StudentProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for StudentProgress model.
    
    Purpose:
        - Convert StudentProgress instances to JSON
        - Validate progress data
        - Include computed metrics
    
    Features:
        - Computed completion and mastery percentages
        - Subject display name
        - Time spent in hours
        - Streak information
    """
    
    # Read-only computed fields
    student_username = serializers.CharField(
        source='student.username',
        read_only=True,
        help_text="Username of the student"
    )
    
    # Display name for subject
    subject_display = serializers.CharField(
        source='get_subject_display',
        read_only=True,
        help_text="Human-readable subject name"
    )
    
    # Computed percentages
    completion_percentage = serializers.SerializerMethodField(
        read_only=True,
        help_text="Percentage of lessons completed"
    )
    
    mastery_percentage = serializers.SerializerMethodField(
        read_only=True,
        help_text="Percentage of skills mastered"
    )
    
    # Time in hours for better readability
    time_spent_hours = serializers.SerializerMethodField(
        read_only=True,
        help_text="Total time spent in hours"
    )
    
    class Meta:
        """Serializer metadata."""
        model = StudentProgress
        fields = '__all__'
        
        # Read-only system fields
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]
        
        # Field configurations
        extra_kwargs = {
            'lessons_completed': {
                'min_value': 0,
                'help_text': 'Number of completed lessons'
            },
            'lessons_total': {
                'min_value': 0,
                'help_text': 'Total lessons in curriculum'
            },
            'skills_mastered': {
                'min_value': 0,
                'help_text': 'Number of mastered skills'
            },
            'skills_total': {
                'min_value': 0,
                'help_text': 'Total skills in curriculum'
            },
            'average_score': {
                'min_value': 0,
                'max_value': 100,
                'help_text': 'Average score (0-100)'
            },
            'time_spent_minutes': {
                'min_value': 0,
                'help_text': 'Total time in minutes'
            },
            'streak_days': {
                'min_value': 0,
                'help_text': 'Current learning streak in days'
            },
        }
    
    def get_completion_percentage(self, obj):
        """Get completion percentage."""
        if hasattr(obj, 'completion_percentage'):
            return float(obj.completion_percentage())
        if isinstance(obj, dict) and 'completion_percentage' in obj:
            return obj['completion_percentage']
        return 0.0
    
    def get_mastery_percentage(self, obj):
        """Get mastery percentage."""
        if hasattr(obj, 'mastery_percentage'):
            return float(obj.mastery_percentage())
        if isinstance(obj, dict) and 'mastery_percentage' in obj:
            return obj['mastery_percentage']
        return 0.0
    
    def get_time_spent_hours(self, obj):
        """Get time spent in hours."""
        if hasattr(obj, 'time_spent_minutes'):
            return round(obj.time_spent_minutes / 60, 1)
        if isinstance(obj, dict) and 'time_spent_minutes' in obj:
            return round(obj['time_spent_minutes'] / 60, 1)
        return 0.0
    
    def validate(self, data):
        """Object-level validation for PATCH/PUT requests."""
        # For PATCH requests, get existing values from instance if available
        if self.instance:
            lessons_completed = data.get('lessons_completed', self.instance.lessons_completed)
            lessons_total = data.get('lessons_total', self.instance.lessons_total)
            skills_mastered = data.get('skills_mastered', self.instance.skills_mastered)
            skills_total = data.get('skills_total', self.instance.skills_total)
        else:
            lessons_completed = data.get('lessons_completed', 0)
            lessons_total = data.get('lessons_total', 0)
            skills_mastered = data.get('skills_mastered', 0)
            skills_total = data.get('skills_total', 0)
        
        if lessons_completed > lessons_total:
            raise serializers.ValidationError(
                "Completed lessons cannot exceed total lessons."
            )
        
        if skills_mastered > skills_total:
            raise serializers.ValidationError(
                "Mastered skills cannot exceed total skills."
            )
        
        return data


class StudentActivitySummarySerializer(serializers.Serializer):
    """
    Serializer for activity summary statistics.
    
    Purpose:
        - Provide aggregated activity metrics
        - Used for dashboard and analytics endpoints
        - Read-only serializer (no model backing)
    
    Fields:
        - total_activities: Count of activities
        - total_time_minutes: Sum of activity time
        - average_engagement: Average engagement score
        - completion_rate: Percentage of completed activities
        - activities_by_type: Breakdown by activity type
    """
    
    # Total activity count
    total_activities = serializers.IntegerField(
        read_only=True,
        help_text="Total number of activities"
    )
    
    # Total time spent
    total_time_minutes = serializers.FloatField(
        read_only=True,
        help_text="Total time spent in minutes"
    )
    
    # Average engagement score
    average_engagement = serializers.FloatField(
        read_only=True,
        help_text="Average engagement score"
    )
    
    # Completion rate
    completion_rate = serializers.FloatField(
        read_only=True,
        help_text="Percentage of completed activities"
    )
    
    # Activities by type
    activities_by_type = serializers.DictField(
        read_only=True,
        help_text="Count of activities by type"
    )
    
    # Date range
    date_from = serializers.DateTimeField(
        read_only=True,
        help_text="Start date of summary period"
    )
    
    date_to = serializers.DateTimeField(
        read_only=True,
        help_text="End date of summary period"
    )


class StudentProgressSummarySerializer(serializers.Serializer):
    """
    Serializer for overall student progress summary.
    
    Purpose:
        - Provide high-level progress overview
        - Used for dashboard homepage
        - Aggregates data across all subjects
    
    Fields:
        - total_lessons_completed: Sum across all subjects
        - total_skills_mastered: Sum across all skills
        - overall_average_score: Weighted average
        - total_time_hours: Total learning time
        - current_streak: Current learning streak
        - progress_by_subject: Breakdown by subject
    """
    
    # Aggregated totals
    total_lessons_completed = serializers.IntegerField(
        read_only=True,
        help_text="Total lessons completed across all subjects"
    )
    
    total_skills_mastered = serializers.IntegerField(
        read_only=True,
        help_text="Total skills mastered across all subjects"
    )
    
    # Overall average
    overall_average_score = serializers.FloatField(
        read_only=True,
        help_text="Weighted average score across subjects"
    )
    
    # Time tracking
    total_time_hours = serializers.FloatField(
        read_only=True,
        help_text="Total learning time in hours"
    )
    
    # Gamification metrics
    current_streak = serializers.IntegerField(
        read_only=True,
        help_text="Current learning streak in days"
    )
    
    longest_streak = serializers.IntegerField(
        read_only=True,
        help_text="Longest learning streak achieved"
    )
    
    # Subject breakdown
    progress_by_subject = serializers.ListField(
        child=StudentProgressSerializer(),
        read_only=True,
        help_text="Progress details for each subject"
    )
    
    # Last activity
    last_activity_date = serializers.DateField(
        read_only=True,
        allow_null=True,
        help_text="Date of last learning activity"
    )
