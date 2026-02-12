# 2025-10-22: API endpoints for the Parent Communication Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Parent Communication Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.communication_engine import CommunicationEngine
import json

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the CommunicationEngine as a singleton.
communication_engine = CommunicationEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/generate_report', methods=['POST'])
def generate_report():
    """
    # 2025-10-22: Endpoint to generate a weekly progress report for a parent.
    """
    student_data = request.get_json()
    if not student_data:
        return jsonify({"error": "Student data is required"}), 400

    try:
        # 2025-10-22: Generate the report.
        report_json_str = communication_engine.generate_report(student_data)
        # 2025-10-22: The LLM should return a JSON string, so we parse it.
        report_json = json.loads(report_json_str)
        return jsonify(report_json), 200
    except ValueError as ve:
        # 2025-10-22: Handle cases where the API key is missing.
        return jsonify({"error": str(ve)}), 503 # Service Unavailable
    except Exception as e:
        # 2025-10-22: Handle other potential errors during report generation.
        return jsonify({"error": f"An error occurred during report generation: {str(e)}"}), 500
