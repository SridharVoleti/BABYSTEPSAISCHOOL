# 2025-10-22: API endpoints for the Research & Accreditation Module
# Authors: Cascade

# 2025-10-22: API endpoints for the Research & Accreditation Module
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.research_module import ResearchModule

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the ResearchModule as a singleton.
research_module = ResearchModule()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/generate_report', methods=['POST'])
def generate_report():
    """
    # 2025-10-22: Endpoint to generate a research or accreditation report.
    """
    data = request.get_json()
    school_data = data.get('school_data')
    benchmark_data = data.get('benchmark_data')

    if not all([school_data, benchmark_data]):
        return jsonify({"error": "'school_data' and 'benchmark_data' are required"}), 400

    try:
        # 2025-10-22: Use the research module to generate the report.
        report = research_module.generate_report(school_data, benchmark_data)
        return jsonify(report), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during report generation: {str(e)}"}), 500
