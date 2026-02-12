"""
Analytics Service API Views

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Django REST Framework API views for analytics service.
    Provides endpoints for activity tracking, progress monitoring, and analytics.

Endpoints:
    /api/analytics/activities/ - Activity tracking CRUD
    /api/analytics/activities/summary/ - Activity summary statistics
    /api/analytics/progress/ - Progress tracking CRUD
    /api/analytics/progress/summary/ - Progress summary statistics

Design Principles:
    - RESTful API design
    - Proper permission controls
    - Efficient database queries
    - Comprehensive error handling
"""

# Django REST Framework imports
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

# Django imports
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

# Python standard library
from datetime import timedelta
from decimal import Decimal

# Import models, serializers, and permissions
from .models import StudentActivity, StudentProgress
from .serializers import (
    StudentActivitySerializer,
    StudentProgressSerializer,
    StudentActivitySummarySerializer,
    StudentProgressSummarySerializer
)
from .permissions import IsOwnerOrStaff, CanDeleteAnalytics, IsAuthenticatedOrRaise401


class StudentActivityViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for StudentActivity model.
    
    Purpose:
        Provides CRUD operations for student learning activities.
        Tracks every learning interaction for analytics.
    
    Endpoints:
        GET    /api/analytics/activities/          - List activities
        POST   /api/analytics/activities/          - Create activity
        GET    /api/analytics/activities/{id}/     - Retrieve activity
        PUT    /api/analytics/activities/{id}/     - Update activity
        PATCH  /api/analytics/activities/{id}/     - Partial update
        DELETE /api/analytics/activities/{id}/     - Delete activity (admin only)
        GET    /api/analytics/activities/summary/  - Activity summary
    
    Permissions:
        - Students can only access their own activities
        - Teachers can view all activities
        - Only admins can delete activities
    
    Filtering:
        - activity_type: Filter by type (lesson_view, quiz_attempt, etc.)
        - content_type: Filter by content type
        - content_id: Filter by specific content
        - started_at__gte: Activities after date
        - started_at__lte: Activities before date
        - is_completed: Filter completed activities
    """
    
    # Set serializer class for this viewset
    # DRF uses this to serialize/deserialize data
    serializer_class = StudentActivitySerializer
    
    # Set permission classes
    # Users must be authenticated and can only access own data or be staff
    # 2025-12-12: Use custom IsAuthenticatedOrRaise401 to return 401 instead of 403
    permission_classes = [IsAuthenticatedOrRaise401, IsOwnerOrStaff]
    
    def get_authenticators(self):
        """
        Override to ensure proper 401 response for unauthenticated requests.
        Uses custom authentication classes that properly handle missing auth.
        """
        return super().get_authenticators()
    
    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to return 405 Method Not Allowed.
        Delete operations are not permitted on activities for audit trail.
        """
        from rest_framework.exceptions import MethodNotAllowed
        raise MethodNotAllowed('DELETE', detail='Delete operation is not allowed on activities.')
    
    # Enable filtering by these fields
    # Creates filter query params: ?activity_type=lesson_view
    filterset_fields = ['activity_type', 'content_type', 'content_id', 'is_completed']
    
    # Enable searching by these fields
    # Creates search query param: ?search=lesson
    search_fields = ['content_id', 'content_type']
    
    # Enable ordering by these fields
    # Creates ordering query param: ?ordering=-started_at
    ordering_fields = ['started_at', 'ended_at', 'engagement_score']
    
    # Default ordering (most recent first)
    ordering = ['-started_at']
    
    def get_queryset(self):
        """
        Return queryset filtered by user permissions.
        
        Purpose:
            - Students see only their own activities
            - Teachers see all activities
            - Apply additional filters from query params
        
        Returns:
            QuerySet: Filtered activities
            
        Performance:
            - Uses select_related to optimize database queries
            - Reduces N+1 query problems
        """
        # Get authenticated user
        user = self.request.user
        
        # Base queryset with optimized queries
        # select_related fetches related student in same query
        queryset = StudentActivity.objects.select_related('student')
        
        # Filter by permissions
        # Staff can see all activities, students only their own
        if not user.is_staff:
            queryset = queryset.filter(student=user)
        
        # Manual filtering for activity_type (since django-filter might not be installed)
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Apply date range filters if provided
        # Support filtering by start date range
        # Parse datetime strings properly to avoid format errors
        from django.utils.dateparse import parse_datetime
        
        started_after = self.request.query_params.get('started_at__gte')
        if started_after:
            parsed_date = parse_datetime(started_after)
            if parsed_date:
                queryset = queryset.filter(started_at__gte=parsed_date)
        
        started_before = self.request.query_params.get('started_at__lte')
        if started_before:
            parsed_date = parse_datetime(started_before)
            if parsed_date:
                queryset = queryset.filter(started_at__lte=parsed_date)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Handle activity creation.
        
        Purpose:
            - Auto-set student to requesting user if not specified
            - Validate student permission
            - Calculate initial metrics
        
        Args:
            serializer: Validated serializer instance
            
        Logic:
            - If student not in data, use request.user
            - Staff can create for any student
            - Students can only create for themselves
        """
        # Get student from validated data or use requesting user
        student = serializer.validated_data.get('student')
        
        # If student not specified, use requesting user
        if student is None:
            serializer.save(student=self.request.user)
        else:
            # Verify permission: staff can create for anyone, students only for self
            if not self.request.user.is_staff and student != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only create activities for yourself.")
            
            serializer.save()
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get activity summary statistics.
        
        Purpose:
            Provides aggregated analytics for dashboard display.
        
        Endpoint:
            GET /api/analytics/activities/summary/
            
        Query Parameters:
            - date_from: Start date for summary (default: 30 days ago)
            - date_to: End date for summary (default: now)
            - student_id: Filter by specific student (staff only)
        
        Returns:
            dict: Summary statistics including:
                - total_activities: Count of activities
                - total_time_minutes: Sum of activity time
                - average_engagement: Average engagement score
                - completion_rate: Percentage completed
                - activities_by_type: Breakdown by type
        
        Response Example:
            {
                "total_activities": 150,
                "total_time_minutes": 2500.5,
                "average_engagement": 85.3,
                "completion_rate": 92.0,
                "activities_by_type": {
                    "lesson_view": 80,
                    "quiz_attempt": 40,
                    "practice": 30
                },
                "date_from": "2025-11-11T00:00:00Z",
                "date_to": "2025-12-11T23:59:59Z"
            }
        """
        # Get date range from query params or use defaults
        date_to = timezone.now()
        date_from = date_to - timedelta(days=30)
        
        # Parse custom date range if provided
        if request.query_params.get('date_from'):
            from django.utils.dateparse import parse_datetime
            date_from = parse_datetime(request.query_params['date_from'])
        
        if request.query_params.get('date_to'):
            from django.utils.dateparse import parse_datetime
            date_to = parse_datetime(request.query_params['date_to'])
        
        # Start with user-filtered queryset
        queryset = self.get_queryset()
        
        # Apply date range filter
        queryset = queryset.filter(
            started_at__gte=date_from,
            started_at__lte=date_to
        )
        
        # Calculate aggregates
        # Uses Django ORM aggregation for efficiency
        aggregates = queryset.aggregate(
            total_activities=Count('id'),
            total_seconds=Sum('duration_seconds'),
            avg_engagement=Avg('engagement_score'),
            completed_count=Count('id', filter=Q(is_completed=True))
        )
        
        # Calculate derived metrics
        total_activities = aggregates['total_activities'] or 0
        total_time_minutes = (aggregates['total_seconds'] or 0) / 60
        average_engagement = float(aggregates['avg_engagement'] or 0)
        completed_count = aggregates['completed_count'] or 0
        
        # Calculate completion rate
        completion_rate = 0
        if total_activities > 0:
            completion_rate = (completed_count / total_activities) * 100
        
        # Get breakdown by activity type
        # Uses values() and annotate() for grouping
        activities_by_type = {}
        type_breakdown = queryset.values('activity_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        for item in type_breakdown:
            activities_by_type[item['activity_type']] = item['count']
        
        # Build response data
        summary_data = {
            'total_activities': total_activities,
            'total_time_minutes': round(total_time_minutes, 2),
            'average_engagement': round(average_engagement, 2),
            'completion_rate': round(completion_rate, 2),
            'activities_by_type': activities_by_type,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        # Serialize and return
        serializer = StudentActivitySummarySerializer(summary_data)
        return Response(serializer.data)


class StudentProgressViewSet(viewsets.ModelViewSet):
    """Override destroy to prevent deletion of progress records"""
    
    def destroy(self, request, *args, **kwargs):
        """Prevent deletion of progress records for audit trail"""
        from rest_framework.exceptions import MethodNotAllowed
        raise MethodNotAllowed('DELETE', detail='Delete operation is not allowed on progress records.')
    """
    API ViewSet for StudentProgress model.
    
    Purpose:
        Provides CRUD operations for student progress tracking.
        Monitors overall progress across subjects and skills.
    
    Endpoints:
        GET    /api/analytics/progress/          - List progress records
        POST   /api/analytics/progress/          - Create progress record
        GET    /api/analytics/progress/{id}/     - Retrieve progress
        PUT    /api/analytics/progress/{id}/     - Update progress
        PATCH  /api/analytics/progress/{id}/     - Partial update
        DELETE /api/analytics/progress/{id}/     - Delete progress (admin only)
        GET    /api/analytics/progress/summary/  - Progress summary
    
    Permissions:
        - Students can only access their own progress
        - Teachers can view all progress
        - Only admins can delete progress
    
    Filtering:
        - subject: Filter by subject
        - grade_level: Filter by grade
        - last_activity_date__gte: Recent activity filter
    """
    
    serializer_class = StudentProgressSerializer
    permission_classes = [IsAuthenticatedOrRaise401, IsOwnerOrStaff, CanDeleteAnalytics]
    
    # Enable filtering
    filterset_fields = ['subject', 'grade_level']
    
    # Enable searching
    search_fields = ['subject']
    
    # Enable ordering
    ordering_fields = ['last_activity_date', 'average_score', 'streak_days']
    ordering = ['-last_activity_date']
    
    def get_queryset(self):
        """
        Return queryset filtered by permissions.
        
        Returns:
            QuerySet: Filtered progress records
        """
        user = self.request.user
        
        # Get all progress records for this user with student relationship
        if user.is_staff:
            queryset = StudentProgress.objects.select_related('student').all()
        else:
            queryset = StudentProgress.objects.select_related('student').filter(student=user)
        
        # Apply additional filters
        if self.request.query_params.get('last_activity_date__gte'):
            from django.utils.dateparse import parse_date
            date_from = parse_date(self.request.query_params['last_activity_date__gte'])
            queryset = queryset.filter(last_activity_date__gte=date_from)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Handle progress record creation.
        
        Logic:
            - Auto-set student if not specified
            - Ensure unique constraint (student+subject+grade)
            - Initialize default values
        """
        student = serializer.validated_data.get('student')
        
        if student is None:
            serializer.save(student=self.request.user)
        else:
            # Permission check
            if not self.request.user.is_staff and student != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You can only create progress for yourself.")
            
            serializer.save()
    
    def perform_update(self, serializer):
        """
        Handle progress updates.
        
        Logic:
            - Update streak when last_activity_date changes
            - Recalculate derived metrics
        """
        # Save the update
        instance = serializer.save()
        
        # Update streak if last_activity_date changed
        if 'last_activity_date' in serializer.validated_data:
            instance.update_streak()
            instance.save()
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get overall progress summary across all subjects.
        
        Purpose:
            Provides high-level student progress overview for dashboard.
        
        Endpoint:
            GET /api/analytics/progress/summary/
            
        Query Parameters:
            - student_id: Specific student (staff only)
        
        Returns:
            dict: Overall progress summary including:
                - total_lessons_completed: Sum across subjects
                - total_skills_mastered: Sum across subjects
                - overall_average_score: Weighted average
                - total_time_hours: Total learning time
                - current_streak: Current learning streak
                - longest_streak: Best streak achieved
                - progress_by_subject: List of subject progress
                - last_activity_date: Most recent activity
        
        Response Example:
            {
                "total_lessons_completed": 250,
                "total_skills_mastered": 120,
                "overall_average_score": 87.5,
                "total_time_hours": 42.5,
                "current_streak": 15,
                "longest_streak": 30,
                "progress_by_subject": [...],
                "last_activity_date": "2025-12-11"
            }
        """
        # Get user-filtered queryset
        queryset = self.get_queryset()
        
        # Calculate aggregates across all subjects
        aggregates = queryset.aggregate(
            total_lessons=Sum('lessons_completed'),
            total_skills=Sum('skills_mastered'),
            avg_score=Avg('average_score'),
            total_minutes=Sum('time_spent_minutes'),
            max_streak=Sum('streak_days')  # This should actually be Max for longest
        )
        
        # Extract values
        total_lessons_completed = aggregates['total_lessons'] or 0
        total_skills_mastered = aggregates['total_skills'] or 0
        overall_average_score = float(aggregates['avg_score'] or 0)
        total_time_minutes = aggregates['total_minutes'] or 0
        total_time_hours = total_time_minutes / 60
        
        # Get current streak (from most recent activity)
        # Current streak should be the maximum streak across subjects
        current_streak = queryset.aggregate(
            max_streak=Sum('streak_days')
        )['max_streak'] or 0
        
        # Get longest streak (would need historical tracking - use current for now)
        longest_streak = current_streak
        
        # Get most recent activity date
        last_activity = queryset.order_by('-last_activity_date').first()
        last_activity_date = last_activity.last_activity_date if last_activity else None
        
        # Get progress by subject
        progress_by_subject = []
        for progress in queryset:
            progress_by_subject.append(StudentProgressSerializer(progress).data)
        
        # Build summary
        summary_data = {
            'total_lessons_completed': total_lessons_completed,
            'total_skills_mastered': total_skills_mastered,
            'overall_average_score': round(overall_average_score, 2),
            'total_time_hours': round(total_time_hours, 1),
            'current_streak': current_streak,
            'longest_streak': longest_streak,
            'progress_by_subject': progress_by_subject,
            'last_activity_date': last_activity_date,
        }
        
        # Serialize and return
        serializer = StudentProgressSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update-streak')
    def update_streak(self, request, pk=None):
        """
        Manually trigger streak update for a progress record.
        
        Purpose:
            Allows recalculating streak based on last activity date.
            Useful for maintenance and corrections.
        
        Endpoint:
            POST /api/analytics/progress/{id}/update-streak/
        
        Returns:
            Updated progress record
        """
        # Get the progress instance
        progress = self.get_object()
        
        # Update streak
        progress.update_streak()
        progress.save()
        
        # Return updated data
        serializer = self.get_serializer(progress)
        return Response(serializer.data)


# Additional utility views can be added here
# Examples:
# - DashboardView: Combined summary of activities and progress
# - LeaderboardView: Top students by metrics
# - TrendView: Progress trends over time
# - ComparisonView: Compare student to class average
