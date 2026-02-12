# 2025-10-22: API endpoints for the Offline Activity Verifier
# Authors: Cascade

# 2025-10-22: API endpoints for the Offline Activity Verifier
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.verification_engine import VerificationEngine
import tempfile
import os

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the VerificationEngine as a singleton.
verification_engine = VerificationEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/verify', methods=['POST'])
def verify_activity():
    """
    # 2025-10-22: Endpoint to verify an offline activity from a video.
    """
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files['video']

    # 2025-10-22: Save the video to a temporary file for processing.
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_video:
        video_file.save(temp_video.name)
        temp_video_path = temp_video.name

    try:
        # 2025-10-22: Use the verification engine to analyze the video.
        verification_result = verification_engine.verify(temp_video_path)
        return jsonify(verification_result), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during verification: {str(e)}"}), 500
    finally:
        # 2025-10-22: Clean up the temporary file.
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
