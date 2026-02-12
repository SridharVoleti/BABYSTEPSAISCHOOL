# 2025-10-22: API endpoints for the AI Examiner
# Authors: Cascade

# 2025-10-22: API endpoints for the AI Examiner
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.ai_examiner import AiExaminer
import json

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the AiExaminer as a singleton.
ai_examiner = AiExaminer()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/examine', methods=['POST'])
def examine_performance():
    """
    # 2025-10-22: Endpoint to generate an AI examiner report.
    """
    performance_data = request.get_json()
    if not performance_data:
        return jsonify({"error": "Performance data is required"}), 400

    try:
        # 2025-10-22: Generate the examiner report.
        report_json_str = ai_examiner.examine(performance_data)
        # 2025-10-22: The LLM should return a JSON string, so we parse it.
        report_json = json.loads(report_json_str)
        return jsonify(report_json), 200
    except ValueError as ve:
        # 2025-10-22: Handle cases where the API key is missing.
        return jsonify({"error": str(ve)}), 503 # Service Unavailable
    except Exception as e:
        # 2025-10-22: Handle other potential errors during report generation.
        return jsonify({"error": f"An error occurred during examination: {str(e)}"}), 500
