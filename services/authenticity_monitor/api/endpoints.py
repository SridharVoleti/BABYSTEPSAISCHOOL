# 2025-10-22: API endpoints for the Authenticity & Integrity Monitor
# Authors: Cascade

# 2025-10-22: API endpoints for the Authenticity & Integrity Monitor
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.integrity_monitor import IntegrityMonitor

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the IntegrityMonitor as a singleton.
integrity_monitor = IntegrityMonitor()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/monitor', methods=['POST'])
def monitor_submission():
    """
    # 2025-10-22: Endpoint to monitor a submission for authenticity.
    """
    submission_data = request.get_json()
    if not submission_data or 'text' not in submission_data:
        return jsonify({"error": "Submission data with 'text' field is required"}), 400

    try:
        # 2025-10-22: Use the integrity monitor to analyze the submission.
        monitoring_result = integrity_monitor.monitor(submission_data)
        return jsonify(monitoring_result), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during monitoring: {str(e)}"}), 500
