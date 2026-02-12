# 2025-10-22: API endpoints for the Assessment Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Assessment Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.assessment_engine import AssessmentEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the AssessmentEngine as a singleton.
assessment_engine = AssessmentEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/assess', methods=['POST'])
def assess_submission():
    """
    # 2025-10-22: Endpoint to assess a student's submission.
    """
    data = request.get_json()
    student_answer = data.get('student_answer')
    correct_answer = data.get('correct_answer')

    if not all([student_answer, correct_answer]):
        return jsonify({"error": "'student_answer' and 'correct_answer' are required"}), 400

    try:
        # 2025-10-22: Use the assessment engine to grade the response.
        assessment = assessment_engine.assess(student_answer, correct_answer)
        return jsonify(assessment), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during assessment: {str(e)}"}), 500
