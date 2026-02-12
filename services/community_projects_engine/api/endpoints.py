# 2025-10-22: API endpoints for the Community Projects Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Community Projects Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.projects_engine import ProjectsEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the ProjectsEngine as a singleton.
projects_engine = ProjectsEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/projects', methods=['GET', 'POST'])
def manage_projects():
    """
    # 2025-10-22: Endpoint to manage community projects.
    """
    if request.method == 'POST':
        project_data = request.get_json()
        if not project_data or 'name' not in project_data:
            return jsonify({"error": "'name' is a required field for a new project"}), 400
        
        new_project = projects_engine.create_project(project_data)
        return jsonify({"message": "Project created successfully", "project": new_project}), 201
    else:
        all_projects = projects_engine.get_all_projects()
        return jsonify(all_projects), 200

@api_blueprint.route('/leaderboard', methods=['POST'])
def get_leaderboard():
    """
    # 2025-10-22: Endpoint to get the project contribution leaderboard.
    """
    contribution_data = request.get_json()
    if not contribution_data:
        return jsonify({"error": "Contribution data is required"}), 400
        
    leaderboard = projects_engine.get_leaderboard(contribution_data)
    return jsonify(leaderboard), 200
