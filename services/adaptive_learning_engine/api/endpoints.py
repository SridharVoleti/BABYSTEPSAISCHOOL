# 2025-10-22: API endpoints for the Adaptive Learning Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Adaptive Learning Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.adaptive_engine import AdaptiveEngine

# 2025-10-22: Create a Blueprint for the API. Blueprints help organize a group of related views.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the AdaptiveEngine as a singleton.
# This ensures that the engine and its models are loaded only once.
adaptive_engine = AdaptiveEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint to confirm the service is running.
    """
    # 2025-10-22: Return a success response
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/analyze', methods=['POST'])
def analyze_submission():
    """
    # 2025-10-22: Endpoint to analyze a student's submission.
    # It receives submission data and returns adaptive feedback.
    """
    # 2025-10-22: Get data from the request
    submission_data = request.get_json()
    if not submission_data:
        return jsonify({"error": "Invalid submission data"}), 400

    # 2025-10-22: Use the adaptive engine to get feedback
    try:
        feedback = adaptive_engine.get_adaptive_feedback(submission_data)
        return jsonify(feedback), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application
        return jsonify({"error": f"An error occurred during analysis: {str(e)}"}), 500
