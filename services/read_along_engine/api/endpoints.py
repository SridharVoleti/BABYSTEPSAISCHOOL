# 2025-10-22: API endpoints for the Read-Along & Mimic Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Read-Along & Mimic Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.mimic_engine import MimicEngine

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

@api_blueprint.route('/align_and_compare', methods=['POST'])
def align_and_compare():
    """
    # 2025-10-22: Endpoint to analyze a student's mimicry.
    """
    # 2025-10-22: In a real implementation, this would handle file uploads.
    # For now, we'll work with mock data from the request body.
    data = request.get_json()
    original_text = data.get('original_text')
    original_audio = data.get('original_audio') # This would be audio data
    student_audio = data.get('student_audio') # This would be audio data

    if not all([original_text, original_audio, student_audio]):
        return jsonify({"error": "Missing required data"}), 400

    try:
        analysis = mimic_engine.analyze_mimicry(original_text, original_audio, student_audio)
        return jsonify(analysis), 200
    except Exception as e:
        return jsonify({"error": f"An error occurred during analysis: {str(e)}"}), 500
