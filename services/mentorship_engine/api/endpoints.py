# 2025-10-22: API endpoints for the Mentorship Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Mentorship Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.mentorship_engine import MentorshipEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the MentorshipEngine as a singleton.
mentorship_engine = MentorshipEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/match', methods=['POST'])
def match_mentor():
    """
    # 2025-10-22: Endpoint to match a mentee with a suitable mentor.
    """
    data = request.get_json()
    mentee_profile = data.get('mentee_profile')
    mentor_profiles = data.get('mentor_profiles')

    if not all([mentee_profile, mentor_profiles]):
        return jsonify({"error": "'mentee_profile' and 'mentor_profiles' are required"}), 400

    try:
        best_match = mentorship_engine.match_mentor(mentee_profile, mentor_profiles)
        if not best_match:
            return jsonify({"message": "No suitable mentor found"}), 404
        return jsonify({"message": "Match found", "best_match": best_match}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred during matching: {str(e)}"}), 500

@api_blueprint.route('/track', methods=['POST'])
def track_growth():
    """
    # 2025-10-22: Endpoint to track mentorship progress and empathy growth.
    """
    data = request.get_json()
    mentor_id = data.get('mentor_id')
    mentee_id = data.get('mentee_id')
    interaction_log = data.get('interaction_log')

    if not all([mentor_id, mentee_id, interaction_log]):
        return jsonify({"error": "'mentor_id', 'mentee_id', and 'interaction_log' are required"}), 400

    try:
        log = mentorship_engine.track_interaction(mentor_id, mentee_id, interaction_log)
        return jsonify({"message": "Progress tracked", "log": log}), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred during tracking: {str(e)}"}), 500
