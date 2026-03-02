"""
2026-02-20: Streak freeze service for Gamification Engine (BS-GAM).

Handles awarding freeze tokens at streak milestones and applying them
to protect a missed day. Idempotent: uses FreezeLedger to deduplicate.
"""

from datetime import date  # 2026-02-20: Today's date for applied reason

from rest_framework.exceptions import ValidationError  # 2026-02-20: Error type

from .models import FreezeLedger, StudentGameProfile  # 2026-02-20: Models

# 2026-02-20: (streak_threshold, freezes_awarded, reason_key)
FREEZE_MILESTONES = [
    (7, 1, 'streak_7'),
    (14, 1, 'streak_14'),
    (30, 2, 'streak_30'),
]

MAX_FREEZES = 5  # 2026-02-20: Maximum freezes a student can hold


def _get_streak(student):
    """
    2026-02-20: Retrieve current streak days for a student.

    Uses StudentLearningProfile.current_streak_days via the user relation.
    Returns 0 if profile does not exist (new student).

    Args:
        student: Student model instance.

    Returns:
        int: Current streak days (0 if unavailable).
    """
    try:
        return student.user.learning_profile.current_streak_days  # 2026-02-20: Cross-app access
    except AttributeError:
        return 0  # 2026-02-20: Fallback for students without learning profile


def check_and_award_freezes(student):
    """
    2026-02-20: Award streak freeze tokens at milestone thresholds.

    Checks each FREEZE_MILESTONE in order. Skips milestones already awarded
    (idempotency via FreezeLedger). Caps at MAX_FREEZES.

    Args:
        student: Student model instance.

    Returns:
        int: Number of new freeze tokens awarded this call.
    """
    streak = _get_streak(student)  # 2026-02-20: Current streak
    profile, _ = StudentGameProfile.objects.get_or_create(
        student=student  # 2026-02-20: Auto-create profile if needed
    )
    total_awarded = 0  # 2026-02-20: Track new freezes this call

    for threshold, count, reason in FREEZE_MILESTONES:
        if streak < threshold:  # 2026-02-20: Not yet at this milestone
            continue
        already_awarded = FreezeLedger.objects.filter(  # 2026-02-20: Idempotency check
            student=student,
            event_type='earned',
            reason=reason,
        ).exists()
        if already_awarded:
            continue  # 2026-02-20: Skip duplicate award
        # 2026-02-20: Award freeze tokens
        new_total = min(MAX_FREEZES, profile.freezes_available + count)
        actually_added = new_total - profile.freezes_available
        profile.freezes_available = new_total
        FreezeLedger.objects.create(  # 2026-02-20: Audit record
            student=student,
            event_type='earned',
            reason=reason,
        )
        total_awarded += actually_added

    if total_awarded > 0:
        profile.save()  # 2026-02-20: Persist updated freeze count

    return total_awarded  # 2026-02-20: Number of new freezes this call


def apply_freeze(student):
    """
    2026-02-20: Use one freeze token to protect a missed streak day.

    Decrements freezes_available by 1 and logs an 'applied' FreezeLedger row.

    Args:
        student: Student model instance.

    Returns:
        dict: {'freezes_remaining': N}

    Raises:
        ValidationError: If no freeze tokens available.
    """
    profile, _ = StudentGameProfile.objects.get_or_create(
        student=student  # 2026-02-20: Auto-create profile if needed
    )
    if profile.freezes_available <= 0:  # 2026-02-20: No freezes to use
        raise ValidationError('No freeze tokens available.')
    profile.freezes_available -= 1  # 2026-02-20: Consume one freeze
    profile.save()
    FreezeLedger.objects.create(  # 2026-02-20: Audit the application
        student=student,
        event_type='applied',
        reason=f'applied_{date.today().isoformat()}',
    )
    return {'freezes_remaining': profile.freezes_available}  # 2026-02-20: Return new count
