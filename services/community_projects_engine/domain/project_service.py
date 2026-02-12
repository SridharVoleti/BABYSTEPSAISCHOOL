# 2025-10-22: Service for managing community projects
# Authors: Cascade

class ProjectService:
    """
    # 2025-10-22: A service to manage community projects.
    # This uses an in-memory list as a placeholder for a database.
    """
    def __init__(self):
        self._projects = []
        self._next_id = 1

    def create_project(self, project_data):
        """
        # 2025-10-22: Creates a new project.
        """
        project_data['id'] = f"proj_{self._next_id}"
        self._projects.append(project_data)
        self._next_id += 1
        return project_data

    def get_all_projects(self):
        """
        # 2025-10-22: Retrieves all projects.
        """
        return self._projects
