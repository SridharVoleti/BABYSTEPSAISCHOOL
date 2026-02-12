"""
Analytics Service Admin Configuration

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Configure Django admin interface for analytics models.
    Provides powerful admin views for monitoring and managing student analytics data.

Admin Features:
    - List views with filtering and searching
    - Readonly fields for calculated values
    - Custom actions for bulk operations
    - Date hierarchy for time-based navigation
    - Inline displays for related data
"""

# Django admin imports
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone

# Import models
from .models import StudentActivity, StudentProgress


@admin.register(StudentActivity)
class StudentActivityAdmin(admin.ModelAdmin):
    """
    Admin interface for StudentActivity model.
    
    Features:
        - Search by student, content ID, activity type
        - Filter by activity type, completion status, date
        - Display key metrics in list view
        - Readonly calculated fields
        - Date hierarchy for navigation
    """
    
    # List view configuration
    # Shows key fields in the admin list page
    list_display = [
        'id',
        'student_link',
        'activity_type',
        'content_display',
        'started_at',
        'duration_display',
        'engagement_display',
        'is_completed',
    ]
    
    # Enable filtering by these fields
    # Creates filter sidebar in admin
    list_filter = [
        'activity_type',
        'is_completed',
        'started_at',
        'content_type',
    ]
    
    # Enable search by these fields
    # Creates search box at top of list
    search_fields = [
        'student__username',
        'student__email',
        'content_id',
    ]
    
    # Date hierarchy for easy navigation by date
    # Creates drill-down navigation by year/month/day
    date_hierarchy = 'started_at'
    
    # Default ordering in admin (most recent first)
    ordering = ['-started_at']
    
    # Read-only fields that should not be edited manually
    # These are auto-calculated
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'duration_seconds',
        'engagement_score',
    ]
    
    # Fieldsets organize the edit form
    # Groups related fields together
    fieldsets = (
        ('Student Information', {
            'fields': ('student',)
        }),
        ('Activity Details', {
            'fields': (
                'activity_type',
                'content_id',
                'content_type',
                'is_completed',
            )
        }),
        ('Timing', {
            'fields': (
                'started_at',
                'ended_at',
                'duration_seconds',
            )
        }),
        ('Metrics', {
            'fields': (
                'engagement_score',
                'metadata',
            )
        }),
        ('System Fields', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),  # Initially collapsed
        }),
    )
    
    # Number of items per page
    list_per_page = 50
    
    # Show count of total items
    show_full_result_count = True
    
    def student_link(self, obj):
        """
        Display student as clickable link.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            str: HTML link to student's change page
            
        Purpose:
            - Quick navigation to student details
            - Better admin UX
        """
        from django.urls import reverse
        from django.utils.html import format_html
        
        # Create URL to student's admin change page
        url = reverse('admin:auth_user_change', args=[obj.student.id])
        
        # Return formatted HTML link
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    
    # Set column header for admin list
    student_link.short_description = 'Student'
    
    def content_display(self, obj):
        """
        Display content ID with type badge.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            str: Formatted content display with colored badge
        """
        # Color code by content type
        colors = {
            'lesson': 'blue',
            'quiz': 'green',
            'video': 'purple',
            'game': 'orange',
        }
        color = colors.get(obj.content_type, 'gray')
        
        # Return formatted HTML with badge
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px;">{}</span> {}',
            color,
            obj.content_type.upper(),
            obj.content_id[:30]  # Truncate long IDs
        )
    
    content_display.short_description = 'Content'
    
    def duration_display(self, obj):
        """
        Display duration in human-readable format.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            str: Formatted duration (e.g., "5m 30s")
        """
        if not obj.duration_seconds:
            return '-'
        
        # Convert seconds to minutes and seconds
        minutes = obj.duration_seconds // 60
        seconds = obj.duration_seconds % 60
        
        # Format based on duration
        if minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    duration_display.short_description = 'Duration'
    
    def engagement_display(self, obj):
        """
        Display engagement score with color coding.
        
        Args:
            obj: StudentActivity instance
            
        Returns:
            str: Colored engagement score
        """
        if not obj.engagement_score:
            return '-'
        
        # Color code based on score
        score = float(obj.engagement_score)
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        # Return colored score
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color,
            score
        )
    
    engagement_display.short_description = 'Engagement'
    
    def get_queryset(self, request):
        """
        Optimize queryset to reduce database queries.
        
        Args:
            request: HttpRequest object
            
        Returns:
            QuerySet: Optimized queryset with select_related
            
        Purpose:
            - Reduce N+1 query problems
            - Improve admin page load time
        """
        # Get base queryset
        queryset = super().get_queryset(request)
        
        # Use select_related to fetch related student in single query
        queryset = queryset.select_related('student')
        
        return queryset


@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    """
    Admin interface for StudentProgress model.
    
    Features:
        - Search by student and subject
        - Filter by subject and grade level
        - Display progress percentages
        - Readonly calculated fields
        - Custom actions for bulk updates
    """
    
    # List view configuration
    list_display = [
        'id',
        'student_link',
        'subject_display',
        'grade_level',
        'completion_progress',
        'mastery_progress',
        'average_score_display',
        'streak_display',
        'last_activity_date',
    ]
    
    # Filtering options
    list_filter = [
        'subject',
        'grade_level',
        'last_activity_date',
    ]
    
    # Search functionality
    search_fields = [
        'student__username',
        'student__email',
    ]
    
    # Default ordering
    ordering = ['student', 'subject']
    
    # Readonly fields
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'completion_percentage',
        'mastery_percentage',
    ]
    
    # Fieldsets for edit form
    fieldsets = (
        ('Student Information', {
            'fields': ('student', 'subject', 'grade_level')
        }),
        ('Lesson Progress', {
            'fields': (
                'lessons_completed',
                'lessons_total',
                'completion_percentage',
            )
        }),
        ('Skill Mastery', {
            'fields': (
                'skills_mastered',
                'skills_total',
                'mastery_percentage',
            )
        }),
        ('Performance Metrics', {
            'fields': (
                'average_score',
                'time_spent_minutes',
            )
        }),
        ('Activity Tracking', {
            'fields': (
                'last_activity_date',
                'streak_days',
            )
        }),
        ('System Fields', {
            'fields': (
                'id',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Items per page
    list_per_page = 50
    
    def student_link(self, obj):
        """Display student as clickable link."""
        from django.urls import reverse
        url = reverse('admin:auth_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    
    student_link.short_description = 'Student'
    
    def subject_display(self, obj):
        """Display subject with icon."""
        # Subject icons
        icons = {
            'math': '🔢',
            'science': '🔬',
            'english': '📚',
            'social_studies': '🌍',
            'evs': '🌱',
            'hindi': '🇮🇳',
            'computer': '💻',
        }
        icon = icons.get(obj.subject, '📖')
        
        return f"{icon} {obj.get_subject_display()}"
    
    subject_display.short_description = 'Subject'
    
    def completion_progress(self, obj):
        """Display lesson completion as progress bar."""
        percentage = obj.completion_percentage()
        
        # Create progress bar HTML
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 4px;">'
            '<div style="width: {}%; background-color: #4CAF50; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%'
            '</div></div>',
            percentage,
            int(percentage)
        )
    
    completion_progress.short_description = 'Completion'
    
    def mastery_progress(self, obj):
        """Display skill mastery as progress bar."""
        percentage = obj.mastery_percentage()
        
        # Create progress bar HTML
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 4px;">'
            '<div style="width: {}%; background-color: #2196F3; height: 20px; border-radius: 4px; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%'
            '</div></div>',
            percentage,
            int(percentage)
        )
    
    mastery_progress.short_description = 'Mastery'
    
    def average_score_display(self, obj):
        """Display average score with color coding."""
        score = float(obj.average_score)
        
        # Color code
        if score >= 80:
            color = 'green'
        elif score >= 60:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}</span>',
            color,
            score
        )
    
    average_score_display.short_description = 'Avg Score'
    
    def streak_display(self, obj):
        """Display learning streak with flame icon."""
        if obj.streak_days == 0:
            return '-'
        
        # Add flame icons based on streak length
        if obj.streak_days >= 30:
            icon = '🔥🔥🔥'
        elif obj.streak_days >= 7:
            icon = '🔥🔥'
        else:
            icon = '🔥'
        
        return f"{icon} {obj.streak_days} days"
    
    streak_display.short_description = 'Streak'
    
    def get_queryset(self, request):
        """Optimize queryset."""
        queryset = super().get_queryset(request)
        queryset = queryset.select_related('student')
        return queryset
    
    # Custom admin actions
    actions = ['update_all_streaks']
    
    def update_all_streaks(self, request, queryset):
        """
        Custom admin action to update streaks for selected records.
        
        Args:
            request: HttpRequest object
            queryset: Selected StudentProgress records
            
        Purpose:
            - Bulk update streaks
            - Useful for maintenance
        """
        # Update each record
        updated_count = 0
        for progress in queryset:
            progress.update_streak()
            progress.save()
            updated_count += 1
        
        # Show success message
        self.message_user(
            request,
            f'Successfully updated {updated_count} streak record(s).'
        )
    
    update_all_streaks.short_description = 'Update learning streaks'


# Admin site customization
# Customize the admin site header and title
admin.site.site_header = 'BabySteps Digital School - Analytics Admin'
admin.site.site_title = 'Analytics Admin'
admin.site.index_title = 'Student Analytics Management'
