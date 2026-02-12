"""
Adaptive Difficulty Adjustment Algorithm

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Algorithms for real-time difficulty adjustment based on student performance.
    Implements Zone of Proximal Development (ZPD) and Flow State optimization.

Algorithm:
    1. Analyze recent performance snapshots
    2. Calculate current ability level
    3. Determine optimal challenge zone (ZPD)
    4. Adjust difficulty to maintain flow state
    5. Prevent extreme swings with gradual adjustment

Design Pattern:
    - Strategy Pattern: Different adjustment strategies
    - Observer Pattern: Responds to performance changes
    - Template Method: Base algorithm with customization points
"""

# Django imports
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User
from django.utils import timezone

# Python standard library
from decimal import Decimal
from datetime import timedelta
from typing import Optional

# Local imports
from .models import (
    DifficultyProfile,
    PerformanceSnapshot,
    ContentDifficulty,
    StudentMastery,
    Skill,
)


def calculate_optimal_difficulty(student: User, skill: Skill) -> float:
    """
    Calculate optimal difficulty level for student on given skill.
    
    Purpose:
        Determine difficulty that promotes learning in Zone of Proximal Development.
        Aims for 70-80% success rate (flow state).
    
    Args:
        student: User object
        skill: Skill object
    
    Returns:
        float: Optimal difficulty level (0-100)
    
    Algorithm:
        1. Get current mastery level
        2. Get recent performance data
        3. Calculate ability level
        4. Apply ZPD offset (slightly above ability)
        5. Return bounded difficulty
    """
    # Get or create difficulty profile
    profile, created = DifficultyProfile.objects.get_or_create(
        student=student,
        skill=skill,
        defaults={'current_difficulty': Decimal('50.0')}
    )
    
    # Get mastery data
    try:
        mastery = StudentMastery.objects.get(student=student, skill=skill)
        current_ability = (mastery.mastery_level / 5.0) * 100  # Convert 0-5 to 0-100
    except StudentMastery.DoesNotExist:
        current_ability = 30.0  # Conservative starting point
    
    # Get recent performance
    recent_snapshots = PerformanceSnapshot.objects.filter(
        student=student,
        skill=skill,
        recorded_at__gte=timezone.now() - timedelta(days=7)
    ).order_by('-recorded_at')[:10]
    
    if recent_snapshots.exists():
        # Calculate average recent success rate
        total_attempts = sum(s.attempts for s in recent_snapshots)
        total_successes = sum(s.successes for s in recent_snapshots)
        
        if total_attempts > 0:
            recent_success_rate = (total_successes / total_attempts) * 100
            
            # Adjust based on performance
            if recent_success_rate > 85:
                # Too easy - increase difficulty
                optimal = current_ability + 15
            elif recent_success_rate < 60:
                # Too hard - decrease difficulty
                optimal = current_ability - 10
            else:
                # In flow state - maintain with slight challenge
                optimal = current_ability + 5
        else:
            optimal = current_ability + 5
    else:
        # No recent data - use ability level + ZPD offset
        optimal = current_ability + 10
    
    # Bound to valid range
    return max(20.0, min(90.0, optimal))


def adjust_difficulty_realtime(
    student: User,
    skill: Skill,
    recent_window_hours: int = 24
) -> float:
    """
    Adjust difficulty in real-time based on very recent performance.
    
    Purpose:
        Provide immediate difficulty adjustment during active learning.
        Responds quickly to student struggles or rapid improvement.
    
    Args:
        student: User object
        skill: Skill object
        recent_window_hours: How recent to consider (default 24 hours)
    
    Returns:
        float: Adjusted difficulty level
    """
    # Get current profile
    profile, created = DifficultyProfile.objects.get_or_create(
        student=student,
        skill=skill
    )
    
    current_difficulty = float(profile.current_difficulty)
    
    # Get very recent performance
    cutoff = timezone.now() - timedelta(hours=recent_window_hours)
    recent_snapshots = PerformanceSnapshot.objects.filter(
        student=student,
        skill=skill,
        recorded_at__gte=cutoff
    ).order_by('-recorded_at')
    
    if not recent_snapshots.exists():
        # No recent data - use optimal calculation
        return calculate_optimal_difficulty(student, skill)
    
    # Calculate recent success rate
    total_attempts = sum(s.attempts for s in recent_snapshots)
    total_successes = sum(s.successes for s in recent_snapshots)
    
    if total_attempts == 0:
        return current_difficulty
    
    success_rate = (total_successes / total_attempts) * 100
    
    # Suggest adjustment
    suggested = profile.suggest_next_difficulty(success_rate)
    
    # Prevent extreme swings - limit change to 15 points
    max_change = 15.0
    if abs(suggested - current_difficulty) > max_change:
        if suggested > current_difficulty:
            adjusted = current_difficulty + max_change
        else:
            adjusted = current_difficulty - max_change
    else:
        adjusted = suggested
    
    # Apply and save
    profile.apply_adjustment(adjusted)
    
    return adjusted


def get_content_for_difficulty(
    difficulty_level: float,
    content_type: str = None,
    tolerance: float = 10.0
) -> list:
    """
    Get content items matching target difficulty level.
    
    Purpose:
        Find appropriate content for student's current difficulty level.
        Enables adaptive content selection.
    
    Args:
        difficulty_level: Target difficulty (0-100)
        content_type: Filter by content type (optional)
        tolerance: Acceptable difficulty range (+/-)
    
    Returns:
        list: ContentDifficulty objects matching criteria
    """
    # Build query
    min_difficulty = max(0, difficulty_level - tolerance)
    max_difficulty = min(100, difficulty_level + tolerance)
    
    query = ContentDifficulty.objects.filter(
        base_difficulty__gte=Decimal(str(min_difficulty)),
        base_difficulty__lte=Decimal(str(max_difficulty))
    )
    
    if content_type:
        query = query.filter(content_type=content_type)
    
    return list(query.order_by('base_difficulty'))


def record_performance_snapshot(
    student: User,
    skill: Skill,
    difficulty_level: float,
    attempts: int,
    successes: int,
    avg_time_seconds: int
) -> PerformanceSnapshot:
    """
    Record a performance snapshot for future adjustment.
    
    Purpose:
        Capture performance data point for trend analysis.
        Used by adjustment algorithms.
    
    Args:
        student: User object
        skill: Skill object
        difficulty_level: Difficulty at time of performance
        attempts: Number of attempts
        successes: Number of successes
        avg_time_seconds: Average time per attempt
    
    Returns:
        PerformanceSnapshot: Created snapshot
    """
    snapshot = PerformanceSnapshot.objects.create(
        student=student,
        skill=skill,
        difficulty_level=Decimal(str(difficulty_level)),
        attempts=attempts,
        successes=successes,
        avg_time_seconds=avg_time_seconds
    )
    
    return snapshot


def analyze_performance_trend(
    student: User,
    skill: Skill,
    days: int = 7
) -> dict:
    """
    Analyze performance trend over time.
    
    Purpose:
        Identify if student is improving, declining, or plateauing.
        Informs difficulty adjustment strategy.
    
    Args:
        student: User object
        skill: Skill object
        days: Number of days to analyze
    
    Returns:
        dict: Trend analysis with direction and confidence
    """
    # Get snapshots
    cutoff = timezone.now() - timedelta(days=days)
    snapshots = PerformanceSnapshot.objects.filter(
        student=student,
        skill=skill,
        recorded_at__gte=cutoff
    ).order_by('recorded_at')
    
    if snapshots.count() < 3:
        return {
            'direction': 'unknown',
            'confidence': 0.0,
            'data_points': snapshots.count()
        }
    
    # Calculate success rates
    rates = [s.calculate_success_rate() for s in snapshots]
    
    # Simple linear regression
    n = len(rates)
    x = list(range(n))
    
    # Calculate slope
    x_mean = sum(x) / n
    y_mean = sum(rates) / n
    
    numerator = sum((x[i] - x_mean) * (rates[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    # Determine direction
    if slope > 2:
        direction = 'improving'
        confidence = min(100, abs(slope) * 10)
    elif slope < -2:
        direction = 'declining'
        confidence = min(100, abs(slope) * 10)
    else:
        direction = 'stable'
        confidence = 100 - abs(slope) * 10
    
    return {
        'direction': direction,
        'confidence': confidence,
        'slope': slope,
        'data_points': n,
        'avg_success_rate': y_mean
    }
