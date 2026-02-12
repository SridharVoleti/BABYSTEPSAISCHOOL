# 2025-10-22: Service for managing user streaks
# Authors: Cascade

import datetime

class StreakService:
    """
    # 2025-10-22: A service to manage user activity streaks.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize an in-memory store for streaks. A real system would use a database.
        """
        self._streak_store = {}

    def update_streak(self, user_id):
        """
        # 2025-10-22: Updates a user's activity streak.
        """
        today = datetime.date.today()
        user_streak = self._streak_store.get(user_id, {"current_streak": 0, "last_activity_date": None})

        if user_streak['last_activity_date'] == today:
            # 2025-10-22: Already active today, no change.
            return user_streak['current_streak']
        
        if user_streak['last_activity_date'] == today - datetime.timedelta(days=1):
            # 2025-10-22: Consecutive day, increment streak.
            user_streak['current_streak'] += 1
        else:
            # 2025-10-22: Not a consecutive day, reset streak to 1.
            user_streak['current_streak'] = 1

        user_streak['last_activity_date'] = today
        self._streak_store[user_id] = user_streak
        return user_streak['current_streak']
