"""
Learning Style Detection Algorithm

Date: 2025-12-11
Author: BabySteps Development Team

Purpose:
    Algorithms to detect student learning styles from behavioral data.
    Uses VARK model (Visual, Auditory, Reading/Writing, Kinesthetic).

Algorithm:
    1. Collect content interaction preferences
    2. Analyze engagement patterns by content type
    3. Calculate style scores using weighted average
    4. Update student learning style profile

Design Pattern:
    - Strategy Pattern: Different detection strategies can be plugged in
    - Observer Pattern: Updates profile when new data arrives
"""

# Django imports
from django.db.models import Avg, Count, Q
from django.contrib.auth.models import User

# Python standard library
from decimal import Decimal
from typing import Optional

# Local imports
from .models import (
    LearningStyleProfile,
    StylePreference,
    ContentInteractionPattern,
    LearningSession,
)


def detect_learning_style(
    student: User,
    min_observations: int = 5,
    update_existing: bool = True
) -> Optional[LearningStyleProfile]:
    """
    Detect student's learning style from behavioral data.
    
    Purpose:
        Analyze student's content interaction history to determine
        learning style preferences using the VARK model.
    
    Args:
        student: User object for the student
        min_observations: Minimum observations needed for detection
        update_existing: Whether to update existing profile or create new
    
    Returns:
        LearningStyleProfile: Updated or new profile, or None if insufficient data
    
    Algorithm:
        1. Gather all style preference observations
        2. Calculate weighted scores for each content type
        3. Map content types to VARK categories
        4. Calculate final VARK scores
        5. Update or create profile
    
    Example:
        profile = detect_learning_style(student)
        if profile:
            print(f"Dominant style: {profile.get_dominant_style()}")
    """
    # Get all preference observations for student
    preferences = StylePreference.objects.filter(student=student)
    
    # Check if we have enough data
    if preferences.count() < min_observations:
        # Not enough data - return existing profile or None
        if update_existing:
            try:
                return LearningStyleProfile.objects.get(student=student)
            except LearningStyleProfile.DoesNotExist:
                return None
        return None
    
    # Calculate scores by content type
    content_scores = _calculate_content_type_scores(preferences)
    
    # Map content types to VARK categories
    vark_scores = _map_to_vark_model(content_scores)
    
    # Get or create profile
    if update_existing:
        profile, created = LearningStyleProfile.objects.get_or_create(
            student=student,
            defaults={
                'visual_score': Decimal('50.0'),
                'auditory_score': Decimal('50.0'),
                'kinesthetic_score': Decimal('50.0'),
                'reading_writing_score': Decimal('50.0'),
            }
        )
    else:
        profile = LearningStyleProfile(student=student)
    
    # Update scores
    profile.visual_score = Decimal(str(vark_scores['visual']))
    profile.auditory_score = Decimal(str(vark_scores['auditory']))
    profile.kinesthetic_score = Decimal(str(vark_scores['kinesthetic']))
    profile.reading_writing_score = Decimal(str(vark_scores['reading_writing']))
    profile.sample_size = preferences.count()
    
    # Save profile
    profile.save()
    
    return profile


def _calculate_content_type_scores(preferences):
    """
    Calculate weighted preference scores for each content type.
    
    Purpose:
        Aggregate all observations per content type into a single score.
        Uses weighted average based on time spent and recency.
    
    Args:
        preferences: QuerySet of StylePreference objects
    
    Returns:
        dict: Content type -> weighted score mapping
    """
    # Group by content type
    from django.db.models import Avg
    
    scores = {}
    
    for content_type in ['video', 'audio', 'text', 'image', 'interactive', 'quiz', 'game']:
        # Filter preferences for this content type
        type_prefs = preferences.filter(content_type=content_type)
        
        if type_prefs.exists():
            # Calculate weighted average
            total_weight = 0
            weighted_sum = 0
            
            for pref in type_prefs:
                # Weight based on time spent (more time = more weight)
                weight = pref.get_time_weight()
                
                # Preference score combines engagement and completion
                pref_score = pref.calculate_preference_score()
                
                weighted_sum += pref_score * weight
                total_weight += weight
            
            # Calculate weighted average
            if total_weight > 0:
                scores[content_type] = weighted_sum / total_weight
            else:
                scores[content_type] = 0
        else:
            scores[content_type] = 0
    
    return scores


def _map_to_vark_model(content_scores):
    """
    Map content type scores to VARK learning style categories.
    
    Purpose:
        Convert specific content type preferences to generalized
        learning style categories (Visual, Auditory, Reading/Writing, Kinesthetic).
    
    Args:
        content_scores: dict of content_type -> score
    
    Returns:
        dict: VARK category -> score mapping
    
    Mapping:
        Visual: video, image
        Auditory: audio
        Reading/Writing: text, quiz
        Kinesthetic: interactive, game
    """
    # Map content types to VARK categories
    vark = {
        'visual': 0,
        'auditory': 0,
        'reading_writing': 0,
        'kinesthetic': 0
    }
    
    # Visual: video, image
    visual_types = ['video', 'image']
    visual_scores = [content_scores.get(ct, 0) for ct in visual_types if content_scores.get(ct, 0) > 0]
    if visual_scores:
        # Use max instead of average to better capture strong preferences
        vark['visual'] = max(visual_scores)
    
    # Auditory: audio
    vark['auditory'] = content_scores.get('audio', 0)
    
    # Reading/Writing: text, quiz
    rw_types = ['text', 'quiz']
    rw_scores = [content_scores.get(ct, 0) for ct in rw_types if content_scores.get(ct, 0) > 0]
    if rw_scores:
        vark['reading_writing'] = max(rw_scores)
    
    # Kinesthetic: interactive, game
    kin_types = ['interactive', 'game']
    kin_scores = [content_scores.get(ct, 0) for ct in kin_types if content_scores.get(ct, 0) > 0]
    if kin_scores:
        vark['kinesthetic'] = max(kin_scores)
    
    # Normalize to 0-100 range if needed
    for key in vark:
        vark[key] = max(0, min(100, vark[key]))
    
    return vark


def update_style_from_session(session):
    """
    Update learning style based on a single session.
    
    Purpose:
        Incremental update when new session data is available.
        Avoids reprocessing all historical data.
    
    Args:
        session: LearningSession object
    
    Returns:
        LearningStyleProfile: Updated profile
    """
    # Get or create observations from session activities
    # This would be called from a signal when session completes
    
    # For now, trigger full redetection
    return detect_learning_style(session.student, update_existing=True)


def get_recommended_content_types(student: User, top_n: int = 3):
    """
    Get recommended content types for student based on learning style.
    
    Purpose:
        Suggest content formats that match student's learning preferences.
    
    Args:
        student: User object
        top_n: Number of top recommendations to return
    
    Returns:
        list: Recommended content types in order of preference
    
    Example:
        recommendations = get_recommended_content_types(student)
        # ['video', 'image', 'interactive']
    """
    try:
        profile = LearningStyleProfile.objects.get(student=student)
    except LearningStyleProfile.DoesNotExist:
        # No profile yet - detect first
        profile = detect_learning_style(student)
        if not profile:
            return ['text', 'video', 'quiz']  # Default recommendations
    
    # Get preferred formats from profile
    formats = profile.get_preferred_formats()
    
    # Return top N
    return formats[:top_n] if formats else ['text', 'video', 'quiz']
