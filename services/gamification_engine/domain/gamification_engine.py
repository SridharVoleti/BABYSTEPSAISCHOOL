# 2025-10-22: Core Gamification Engine
# Authors: Cascade

from .badge_service import BadgeService
from .streak_service import StreakService

class GamificationEngine:
    """
    # 2025-10-22: Orchestrates the gamification services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying services.
        """
        self.badge_service = BadgeService()
        self.streak_service = StreakService()

    def process_event(self, event_data):
        """
        # 2025-10-22: Processes a student event and returns any rewards.
        """
        user_id = event_data.get('user_id')
        event_type = event_data.get('event_type')
        user_current_badges = event_data.get('user_badges', [])

        rewards = []

        # 2025-10-22: Check for new badges.
        new_badges = self.badge_service.check_for_new_badges(event_type, event_data, user_current_badges)
        for badge in new_badges:
            rewards.append({"type": "badge", "name": badge})

        # 2025-10-22: Update streak and award points if it's a new day.
        current_streak = self.streak_service.update_streak(user_id)
        if current_streak > 1:
            rewards.append({"type": "streak_bonus", "days": current_streak, "points": current_streak * 5})

        # 2025-10-22: Award base points for the event.
        rewards.append({"type": "points", "amount": 10})

        return rewards
