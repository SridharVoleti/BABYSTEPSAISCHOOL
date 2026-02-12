# 2025-10-22: API endpoints for the Team Collaboration Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Team Collaboration Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.collaboration_engine import CollaborationEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the CollaborationEngine as a singleton.
collaboration_engine = CollaborationEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/assign_roles', methods=['POST'])
def assign_roles():
    """
    # 2025-10-22: Endpoint to assign roles to team members for a project.
    """
    data = request.get_json()
    team_members = data.get('team_members')
    available_roles = data.get('available_roles') # Optional

    if not team_members:
        return jsonify({"error": "'team_members' list is required"}), 400

    try:
        assignments = collaboration_engine.assign_roles(team_members, available_roles)
        return jsonify({"message": "Roles assigned successfully", "assignments": assignments}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred during role assignment: {str(e)}"}), 500


@api_blueprint.route('/track_collaboration', methods=['POST'])
def track_collaboration():
    """
    # 2025-10-22: Endpoint to track group participation.
    """
    collaboration_data = request.get_json()
    if not collaboration_data:
        return jsonify({"error": "Collaboration data is required"}), 400
        
    try:
        participation_metrics = collaboration_engine.track_collaboration(collaboration_data)
        return jsonify({"message": "Collaboration tracked", "participation_metrics": participation_metrics}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred during tracking: {str(e)}"}), 500
