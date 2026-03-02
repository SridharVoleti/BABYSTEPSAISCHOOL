"""
2026-02-20: Badge award service for Gamification Engine (BS-GAM).

check_and_award_badges(student) evaluates all 20 badge criteria against
live DB state and creates StudentBadge rows for newly earned badges.
"""

from django.utils import timezone  # 2026-02-20: Timezone-aware now()

from .badge_catalog import BADGE_CATALOG  # 2026-02-20: Badge definitions
from .coin_service import earn_coins  # 2026-02-20: Bonus coins for badges
from .models import Badge, StudentBadge, StudentGameProfile  # 2026-02-20: Models

BADGE_BONUS_COINS = 10  # 2026-02-20: Coins awarded per badge earned


def _get_streak(student):
    """
    2026-02-20: Retrieve current streak days for a student.

    Returns 0 if StudentLearningProfile does not exist.

    Args:
        student: Student model instance.

    Returns:
        int: Current streak days.
    """
    try:
        return student.user.learning_profile.current_streak_days  # 2026-02-20: Cross-app
    except AttributeError:
        return 0  # 2026-02-20: Fallback for new students


def _evaluate_criterion(student, badge_def, profile):
    """
    2026-02-20: Evaluate whether a single badge criterion is satisfied.

    Uses lazy imports to avoid circular dependencies from cross-service
    model references.

    Args:
        student: Student model instance.
        badge_def: Dict entry from BADGE_CATALOG.
        profile: StudentGameProfile instance.

    Returns:
        bool: True if criterion is met.
    """
    c_type = badge_def['criterion_type']
    c_value = badge_def['criterion_value']

    if c_type == 'streak':
        return _get_streak(student) >= c_value

    if c_type == 'total_stars':
        return profile.total_stars_earned >= c_value

    if c_type == 'day_progress_count':
        # 2026-02-20: Count all completed DayProgress rows for this student
        # DayProgress → lesson_progress (StudentLessonProgress) → student
        from services.teaching_engine.models import DayProgress  # 2026-02-20: Lazy import
        count = DayProgress.objects.filter(
            lesson_progress__student=student,
            status='completed',
        ).count()
        return count >= c_value

    if c_type == 'day_progress_today':
        # 2026-02-20: Count DayProgress rows completed today
        from services.teaching_engine.models import DayProgress  # 2026-02-20: Lazy import
        today = timezone.now().date()
        count = DayProgress.objects.filter(
            lesson_progress__student=student,
            status='completed',
            completed_at__date=today,
        ).count()
        return count >= c_value

    if c_type == 'practice_5star_count':
        # 2026-02-20: Count PracticeSession rows where star_rating == 5
        from services.teaching_engine.models import PracticeSession  # 2026-02-20: Lazy import
        count = PracticeSession.objects.filter(
            student=student,
            star_rating=5,
        ).count()
        return count >= c_value

    if c_type == 'practice_5star_last7':
        # 2026-02-20: Check 7 days all have at least one 5-star PracticeSession
        from services.teaching_engine.models import PracticeSession  # 2026-02-20: Lazy import
        from datetime import timedelta
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        # 2026-02-20: Distinct dates with a 5-star session in the last 7 days
        perfect_days = (
            PracticeSession.objects
            .filter(student=student, star_rating=5, created_at__gte=seven_days_ago)
            .dates('created_at', 'day')
            .count()
        )
        return perfect_days >= c_value

    if c_type == 'vocab_mastered':
        # 2026-02-20: Count StudentWordProgress rows with status='mastered'
        from services.vocabulary_service.models import StudentWordProgress  # 2026-02-20: Lazy import
        count = StudentWordProgress.objects.filter(
            student=student,
            status='mastered',
        ).count()
        return count >= c_value

    if c_type == 'vocab_languages':
        # 2026-02-20: Count distinct languages with ≥1 completed VocabularySession
        from services.vocabulary_service.models import VocabularySession  # 2026-02-20: Lazy import
        count = (
            VocabularySession.objects
            .filter(student=student, status='completed')
            .values('language')
            .distinct()
            .count()
        )
        return count >= c_value

    if c_type == 'read_along_count':
        # 2026-02-20: Count ReadAlongSession rows for this student
        from services.read_along_service.models import ReadAlongSession  # 2026-02-20: Lazy import
        count = ReadAlongSession.objects.filter(student=student).count()
        return count >= c_value

    return False  # 2026-02-20: Unknown criterion type — conservative fallback


def check_and_award_badges(student):
    """
    2026-02-20: Evaluate all badge criteria and award newly earned badges.

    For each badge in the catalog:
    1. Skip if StudentBadge(student, badge) already exists.
    2. Evaluate criterion via DB query.
    3. If met: create StudentBadge, increment profile total, award bonus coins.

    Args:
        student: Student model instance.

    Returns:
        list[dict]: Newly awarded badges (empty list if none).
    """
    profile, _ = StudentGameProfile.objects.get_or_create(
        student=student  # 2026-02-20: Auto-create profile if needed
    )

    # 2026-02-20: Build set of already-earned badge_ids for fast lookup
    already_earned_ids = set(
        StudentBadge.objects
        .filter(student=student)
        .values_list('badge__badge_id', flat=True)
    )

    newly_earned = []  # 2026-02-20: Collect new badges this call

    for badge_def in BADGE_CATALOG:
        badge_id = badge_def['badge_id']

        if badge_id in already_earned_ids:
            continue  # 2026-02-20: Already awarded — skip evaluation

        if not _evaluate_criterion(student, badge_def, profile):
            continue  # 2026-02-20: Criterion not yet met

        # 2026-02-20: Award the badge
        try:
            badge = Badge.objects.get(badge_id=badge_id)
        except Badge.DoesNotExist:
            continue  # 2026-02-20: Catalog row missing (migration not run)

        StudentBadge.objects.get_or_create(  # 2026-02-20: Race-safe creation
            student=student,
            badge=badge,
        )
        profile.total_badges_earned += 1  # 2026-02-20: Update cached count
        profile.save()

        # 2026-02-20: Bonus coin reward for earning a badge
        earn_coins(
            student=student,
            amount=BADGE_BONUS_COINS,
            event_type='badge_bonus',
            description=f'Badge earned: {badge.name}',
        )

        newly_earned.append({  # 2026-02-20: Return dict for API response
            'badge_id': badge.badge_id,
            'name': badge.name,
            'icon': badge.icon,
            'description': badge.description,
            'category': badge.category,
            'rarity': badge.rarity,
        })

    return newly_earned  # 2026-02-20: Empty list if nothing new
