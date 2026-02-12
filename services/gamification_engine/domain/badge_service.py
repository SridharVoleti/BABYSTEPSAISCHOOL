# 2025-10-22: Service for managing and awarding badges
# Authors: Cascade

class BadgeService:
    """
    # 2025-10-22: A service to define and award badges based on user activity.
    """
    def __init__(self):
        """
        # 2025-10-22: Define the badge criteria. In a real system, this would come from a database.
        """
        self.badge_definitions = {
            "First Steps": {"event_type": "activity_completed", "condition": lambda data: data.get('total_completed', 0) == 1},
            "Math Whiz": {"event_type": "activity_completed", "condition": lambda data: data.get('subject') == 'Math' and data.get('score', 0) > 0.9},
            "Perfect Score": {"event_type": "activity_completed", "condition": lambda data: data.get('score', 0) == 1.0}
        }

    def check_for_new_badges(self, event_type, event_data, user_badges):
        """
        # 2025-10-22: Checks if a user has earned any new badges based on an event.
        """
        newly_earned = []
        for badge_name, criteria in self.badge_definitions.items():
            if criteria['event_type'] == event_type and badge_name not in user_badges:
                if criteria['condition'](event_data):
                    newly_earned.append(badge_name)
        return newly_earned
