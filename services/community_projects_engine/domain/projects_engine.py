# 2025-10-22: Core Community Projects Engine
# Authors: Cascade

from .project_service import ProjectService
from .leaderboard_service import LeaderboardService

class ProjectsEngine:
    """
    # 2025-10-22: Orchestrates the community projects services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying services.
        """
        self.project_service = ProjectService()
        self.leaderboard_service = LeaderboardService()

    def create_project(self, project_data):
        return self.project_service.create_project(project_data)

    def get_all_projects(self):
        return self.project_service.get_all_projects()

    def get_leaderboard(self, project_contributions):
        return self.leaderboard_service.generate_leaderboard(project_contributions)
