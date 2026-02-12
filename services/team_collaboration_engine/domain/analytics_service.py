# 2025-10-22: Service for analyzing team collaboration data
# Authors: Cascade

class AnalyticsService:
    """
    # 2025-10-22: A service to analyze collaboration metrics.
    """
    def analyze_participation(self, collaboration_data):
        """
        # 2025-10-22: Calculates participation scores based on activity data.
        # 'collaboration_data' should be a dict like {'user_id': {'commits': 5, 'messages': 20}}
        """
        total_activity = 0
        user_scores = {}

        # 2025-10-22: Calculate total activity to normalize scores.
        for user, data in collaboration_data.items():
            # 2025-10-22: Simple weighted score.
            score = data.get('commits', 0) * 2 + data.get('messages', 0) * 0.5
            user_scores[user] = score
            total_activity += score

        # 2025-10-22: Normalize the scores to get a participation percentage.
        participation_metrics = {}
        if total_activity > 0:
            for user, score in user_scores.items():
                participation_metrics[user] = score / total_activity
        
        return participation_metrics
