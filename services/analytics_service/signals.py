"""
Analytics Service Signal Handlers

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Django signal handlers for analytics service.
    Automatically update related data when activities or progress change.

Signals:
    - Update progress when activity is completed
    - Recalculate metrics when data changes
    - Maintain data consistency
    - Trigger notifications

Design Pattern:
    - Observer pattern: React to model changes
    - Decoupled: Signals keep logic separate from models
    - Automatic: No manual intervention needed
"""

# Django imports
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

# Import models
from .models import StudentActivity, StudentProgress


@receiver(post_save, sender=StudentActivity)
def update_progress_on_activity(sender, instance, created, **kwargs):
    """
    Update student progress when activity is completed.
    
    Purpose:
        Automatically sync progress metrics when students complete activities.
        Maintains consistency between activity tracking and progress records.
    
    Trigger:
        Fires after StudentActivity is saved
    
    Logic:
        - If activity is completed (is_completed=True)
        - Find corresponding progress record
        - Update lessons_completed or skills_mastered
        - Update time_spent_minutes
        - Update last_activity_date
        - Update streak
    
    Args:
        sender: StudentActivity model class
        instance: The saved activity instance
        created: Boolean, True if new record
        **kwargs: Additional signal arguments
    """
    # Only process completed activities
    if not instance.is_completed:
        return
    
    # Only process if activity has ended (has duration)
    if not instance.duration_seconds:
        return
    
    # Map activity types to what they affect
    # lesson_complete affects lessons_completed
    # Other types might affect different metrics
    if instance.activity_type not in ['lesson_complete', 'quiz_complete']:
        return
    
    # Get or create progress record for this student
    # We need to know the subject and grade level
    # For now, we'll update the most recent progress for any subject
    # In production, activity should include subject reference
    
    progress_records = StudentProgress.objects.filter(
        student=instance.student
    )
    
    # Update all progress records for this student
    # (In reality, we'd filter by subject)
    for progress in progress_records:
        # Increment lessons completed
        if instance.activity_type == 'lesson_complete':
            progress.lessons_completed += 1
        
        # Add time spent (convert seconds to minutes)
        time_minutes = instance.duration_seconds // 60
        progress.time_spent_minutes += time_minutes
        
        # Update last activity date
        activity_date = instance.started_at.date()
        if progress.last_activity_date is None or activity_date > progress.last_activity_date:
            progress.last_activity_date = activity_date
            # Update streak
            progress.update_streak()
        
        # Save progress
        progress.save()


@receiver(pre_save, sender=StudentProgress)
def calculate_average_score(sender, instance, **kwargs):
    """
    Calculate weighted average score before saving progress.
    
    Purpose:
        Ensure average_score is always up-to-date with latest data.
    
    Trigger:
        Fires before StudentProgress is saved
    
    Logic:
        - Query all activities for this student in this subject
        - Calculate weighted average of scores
        - Update average_score field
    
    Note:
        This is a placeholder. In production, we'd need a more sophisticated
        scoring system that tracks assessment results.
    """
    # Skip if this is a new record (no activities yet)
    if instance.pk is None:
        return
    
    # Calculate average engagement from recent activities
    # This is a proxy for academic score
    # In production, we'd use actual assessment scores
    
    recent_activities = StudentActivity.objects.filter(
        student=instance.student,
        is_completed=True,
        engagement_score__isnull=False
    ).order_by('-started_at')[:20]  # Last 20 activities
    
    if recent_activities.exists():
        from django.db.models import Avg
        avg_engagement = recent_activities.aggregate(
            avg=Avg('engagement_score')
        )['avg']
        
        if avg_engagement is not None:
            # Use engagement as proxy for score
            # In production, replace with actual assessment scores
            instance.average_score = avg_engagement


@receiver(post_save, sender=StudentProgress)
def notify_on_milestone(sender, instance, created, **kwargs):
    """
    Send notification when student reaches milestone.
    
    Purpose:
        Celebrate student achievements to encourage continued learning.
    
    Trigger:
        Fires after StudentProgress is saved
    
    Logic:
        - Check if milestone reached (e.g., 100% completion)
        - Check if streak milestone reached (e.g., 30 days)
        - Send notification to student
        - Update badges/achievements
    
    Milestones:
        - Lesson completion: 25%, 50%, 75%, 100%
        - Skill mastery: 50%, 100%
        - Streak: 7, 14, 30, 100 days
    
    Note:
        Notification system to be implemented in separate service
    """
    # Check completion milestones
    completion = instance.completion_percentage()
    
    milestone_percentages = [25, 50, 75, 100]
    for milestone in milestone_percentages:
        if completion >= milestone and completion < milestone + 5:
            # Close to milestone, could trigger notification
            # Notification implementation will go here
            pass
    
    # Check streak milestones
    streak_milestones = [7, 14, 30, 60, 100]
    if instance.streak_days in streak_milestones:
        # Streak milestone reached
        # Notification implementation will go here
        pass


# Signal connection is automatic due to @receiver decorator
# No need to manually connect signals in apps.py

# Additional signals to implement:
# - Send weekly progress report
# - Alert teacher when student struggles
# - Congratulate on first perfect score
# - Remind student if inactive for 3 days
# - Update leaderboard on score change
