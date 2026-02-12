# 2025-10-22: API endpoints for the Gamification Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Gamification Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.gamification_engine import GamificationEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the GamificationEngine as a singleton.
gamification_engine = GamificationEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/process_event', methods=['POST'])
def process_event():
    """
    # 2025-10-22: Endpoint to process a student event and apply gamification rules.
    """
    event_data = request.get_json()
    if not event_data or 'event_type' not in event_data or 'user_id' not in event_data:
        return jsonify({"error": "Request must contain 'event_type' and 'user_id'"}), 400

    try:
        # 2025-10-22: Use the gamification engine to process the event.
        rewards = gamification_engine.process_event(event_data)
        return jsonify({"message": "Event processed", "rewards": rewards}), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred while processing the event: {str(e)}"}), 500
