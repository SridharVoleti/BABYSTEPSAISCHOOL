# 2025-10-22: API endpoints for the Learn-by-Mimic Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Learn-by-Mimic Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.mimic_engine import MimicEngine
import uuid

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the MimicEngine as a singleton.
mimic_engine = MimicEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/start_cycle', methods=['POST'])
def start_cycle():
    """
    # 2025-10-22: Endpoint to start a mimicry cycle.
    """
    data = request.get_json()
    initial_challenge = data.get('challenge')
    if not initial_challenge:
        return jsonify({"error": "'challenge' text is required"}), 400

    # 2025-10-22: Generate a unique ID for the cycle.
    cycle_id = str(uuid.uuid4())
    
    try:
        result = mimic_engine.start_cycle(cycle_id, initial_challenge)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@api_blueprint.route('/submit_mimic', methods=['POST'])
def submit_mimic():
    """
    # 2025-10-22: Endpoint to submit a mimic attempt and get feedback.
    """
    data = request.get_json()
    cycle_id = data.get('cycle_id')
    user_attempt = data.get('attempt')

    if not all([cycle_id, user_attempt]):
        return jsonify({"error": "'cycle_id' and 'attempt' are required"}), 400

    try:
        feedback = mimic_engine.process_mimic(cycle_id, user_attempt)
        return jsonify(feedback), 200
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404 # Not Found for invalid cycle ID
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
