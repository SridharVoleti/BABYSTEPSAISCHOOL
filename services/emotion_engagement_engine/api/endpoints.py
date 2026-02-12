# 2025-10-22: API endpoints for the Emotion–Engagement Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Emotion–Engagement Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.engagement_engine import EngagementEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the EngagementEngine as a singleton.
engagement_engine = EngagementEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/analyze_engagement', methods=['POST'])
def analyze_engagement():
    """
    # 2025-10-22: Endpoint to analyze emotion and engagement.
    # This endpoint expects 'image' and/or 'audio' file uploads.
    """
    image_file = request.files.get('image')
    audio_file = request.files.get('audio')

    if not image_file and not audio_file:
        return jsonify({"error": "An 'image' or 'audio' file is required"}), 400

    image_data = image_file.read() if image_file else None
    audio_data = audio_file.read() if audio_file else None

    try:
        # 2025-10-22: Use the engagement engine to analyze the data.
        analysis = engagement_engine.analyze_engagement(image_data, audio_data)
        return jsonify(analysis), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during analysis: {str(e)}"}), 500
