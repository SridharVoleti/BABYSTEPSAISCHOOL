# 2025-10-22: API endpoints for the Peer Reflection System
# Authors: Cascade

# 2025-10-22: API endpoints for the Peer Reflection System
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.reflection_system import ReflectionSystem

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the ReflectionSystem as a singleton.
reflection_system = ReflectionSystem()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/analyze_reflection', methods=['POST'])
def analyze_reflection():
    """
    # 2025-10-22: Endpoint to analyze a peer reflection.
    """
    data = request.get_json()
    reflection_text = data.get('text')

    if not reflection_text:
        return jsonify({"error": "'text' field is required"}), 400

    try:
        # 2025-10-22: Use the reflection system to analyze the text.
        analysis = reflection_system.analyze_reflection(reflection_text)
        return jsonify(analysis), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during analysis: {str(e)}"}), 500
