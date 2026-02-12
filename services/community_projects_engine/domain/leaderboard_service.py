# 2025-10-22: Service for generating project leaderboards
# Authors: Cascade

class LeaderboardService:
    """
    # 2025-10-22: A service to calculate and rank user contributions.
    """
    def generate_leaderboard(self, project_contributions):
        """
        # 2025-10-22: Generates a leaderboard from contribution data.
        # 'project_contributions' is a dict like {'user_id': contribution_score}.
        """
        if not project_contributions:
            return []

        # 2025-10-22: Sort users by their contribution score in descending order.
        sorted_leaderboard = sorted(
            project_contributions.items(), 
            key=lambda item: item[1], 
            reverse=True
        )

        # 2025-10-22: Format for the API response.
        return [{"user_id": user, "score": score} for user, score in sorted_leaderboard]
