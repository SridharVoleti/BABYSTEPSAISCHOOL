"""
2026-02-20: Coin economy service for Gamification Engine (BS-GAM).

Provides thread-safe earn/spend operations using select_for_update.
All balance changes go through CoinLedger (append-only audit trail).
"""

from django.db import transaction  # 2026-02-20: Atomic blocks
from rest_framework.exceptions import ValidationError  # 2026-02-20: Error type

from .models import CoinLedger, StudentGameProfile  # 2026-02-20: Models


def earn_coins(student, amount, event_type, description, reference_id=None):
    """
    2026-02-20: Add coins to a student's balance.

    Creates a CoinLedger row and increments StudentGameProfile.coin_balance
    inside a single atomic transaction with select_for_update to prevent races.

    Args:
        student: Student model instance.
        amount: Positive integer number of coins to earn.
        event_type: CoinLedger.EVENT_TYPE_CHOICES string.
        description: Human-readable note (max 200 chars).
        reference_id: Optional UUID of the triggering object.

    Returns:
        int: New coin balance after earning.
    """
    with transaction.atomic():  # 2026-02-20: Atomic block for consistency
        profile, _ = StudentGameProfile.objects.select_for_update().get_or_create(
            student=student  # 2026-02-20: Auto-create profile on first activity
        )
        CoinLedger.objects.create(  # 2026-02-20: Append ledger row
            student=student,
            amount=amount,
            event_type=event_type,
            description=description,
            reference_id=reference_id,
        )
        profile.coin_balance += amount  # 2026-02-20: Update cached balance
        profile.save()
        return profile.coin_balance  # 2026-02-20: Return new balance


def spend_coins(student, amount, event_type, description, reference_id=None):
    """
    2026-02-20: Deduct coins from a student's balance.

    Raises ValidationError if the student has insufficient coins.
    Creates a CoinLedger row with negative amount.

    Args:
        student: Student model instance.
        amount: Positive integer number of coins to spend.
        event_type: CoinLedger.EVENT_TYPE_CHOICES string.
        description: Human-readable note (max 200 chars).
        reference_id: Optional UUID of the triggering object.

    Returns:
        int: New coin balance after spending.

    Raises:
        ValidationError: If coin_balance < amount.
    """
    with transaction.atomic():  # 2026-02-20: Atomic block for consistency
        profile, _ = StudentGameProfile.objects.select_for_update().get_or_create(
            student=student  # 2026-02-20: Auto-create profile on first activity
        )
        if profile.coin_balance < amount:  # 2026-02-20: Insufficient funds check
            raise ValidationError('Insufficient coins')
        CoinLedger.objects.create(  # 2026-02-20: Append negative ledger row
            student=student,
            amount=-amount,
            event_type=event_type,
            description=description,
            reference_id=reference_id,
        )
        profile.coin_balance -= amount  # 2026-02-20: Deduct from cached balance
        profile.save()
        return profile.coin_balance  # 2026-02-20: Return new balance
