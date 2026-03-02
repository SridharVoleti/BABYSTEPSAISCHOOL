"""
2026-02-20: Gamification facade service (BS-GAM).

GamificationService.process_activity is the single entry point called by
the frontend after each learning activity. It earns coins, awards badges,
and checks for new freeze milestones in one call.
"""

from .badge_service import check_and_award_badges  # 2026-02-20: Badge checks
from .coin_service import earn_coins  # 2026-02-20: Coin earning
from .freeze_service import check_and_award_freezes  # 2026-02-20: Freeze checks
from .models import StudentGameProfile  # 2026-02-20: Profile model

# 2026-02-20: Coins earned per star rating (0-5 stars)
STAR_COIN_MAP = {
    0: 0,
    1: 5,
    2: 10,
    3: 15,
    4: 20,
    5: 30,
}


class GamificationService:
    """
    2026-02-20: Facade for all gamification operations.

    Frontend calls POST /api/v1/gamification/activity/ after each
    activity completion (practice, vocab session, read-along, etc.).
    """

    @staticmethod
    def process_activity(student, stars, activity_type, reference_id=None):
        """
        2026-02-20: Record a completed activity and trigger all gamification rewards.

        Steps:
        1. Get or create StudentGameProfile.
        2. Accumulate stars into total_stars_earned.
        3. Earn coins based on star rating.
        4. Check and award newly earned badges (each gives +10 bonus coins).
        5. Check and award streak freeze tokens.
        6. Return full reward summary.

        Args:
            student: Student model instance.
            stars: int 0-5 star rating for the activity.
            activity_type: str matching CoinLedger.EVENT_TYPE_CHOICES.
            reference_id: Optional UUID of source object (for ledger).

        Returns:
            dict: {
                'coins_earned': int,
                'new_coin_balance': int,
                'new_badges': list[dict],
                'freezes_awarded': int,
            }
        """
        # 2026-02-20: Normalise stars to valid range
        stars = max(0, min(5, int(stars)))

        # 2026-02-20: Step 1+2: Ensure profile and accumulate stars
        profile, _ = StudentGameProfile.objects.get_or_create(student=student)
        profile.total_stars_earned += stars
        profile.weekly_stars += stars  # 2026-02-27: Accumulate weekly star total for leaderboard
        profile.save()

        # 2026-02-27: Record leaderboard snapshot for this week
        try:
            from .leaderboard_service import LeaderboardService  # 2026-02-27: Lazy import
            LeaderboardService.record_week_snapshot(student, stars)
        except Exception as exc:  # 2026-02-27: Non-fatal — don't break activity recording
            import logging
            logging.getLogger(__name__).warning(
                f"Leaderboard snapshot failed for student {student.id}: {exc}"
            )

        # 2026-02-20: Step 3: Earn coins for star rating
        coins_this_activity = STAR_COIN_MAP.get(stars, 0)
        new_balance = earn_coins(
            student=student,
            amount=coins_this_activity,
            event_type=activity_type,
            description=f'{stars}★ {activity_type}',
            reference_id=reference_id,
        )

        # 2026-02-20: Step 4: Badge checks (each badge also earns bonus coins)
        new_badges = check_and_award_badges(student)

        # 2026-02-20: Step 5: Freeze milestone checks
        freezes_awarded = check_and_award_freezes(student)

        # 2026-02-20: Refresh balance after badge bonuses
        profile.refresh_from_db()

        return {  # 2026-02-20: Full reward summary for frontend
            'coins_earned': coins_this_activity,
            'new_coin_balance': profile.coin_balance,
            'new_badges': new_badges,
            'freezes_awarded': freezes_awarded,
        }
