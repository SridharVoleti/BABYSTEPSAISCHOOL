# 2025-10-22: API endpoints for the Olympiad Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Olympiad Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.olympiad_engine import OlympiadEngine
import json

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the OlympiadEngine as a singleton.
olympiad_engine = OlympiadEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/generate_challenge', methods=['POST'])
def generate_challenge():
    """
    # 2025-10-22: Endpoint to generate an Olympiad challenge.
    """
    data = request.get_json()
    topic = data.get('topic')
    difficulty = data.get('difficulty', 'medium')

    if not topic:
        return jsonify({"error": "'topic' is a required field"}), 400

    try:
        # 2025-10-22: Generate the challenge content.
        challenge_json_str = olympiad_engine.generate_challenge(topic, difficulty)
        # 2025-10-22: The LLM should return a JSON string, so we parse it.
        challenge_json = json.loads(challenge_json_str)
        return jsonify(challenge_json), 200
    except ValueError as ve:
        # 2025-10-22: Handle cases where the API key is missing.
        return jsonify({"error": str(ve)}), 503 # Service Unavailable
    except Exception as e:
        # 2025-10-22: Handle other potential errors during generation.
        return jsonify({"error": f"An error occurred during challenge generation: {str(e)}"}), 500
