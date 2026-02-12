# 2025-10-22: API endpoints for the Lesson JSON Generator
# Authors: Cascade

# 2025-10-22: API endpoints for the Lesson JSON Generator
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.lesson_generator import LessonGenerator
import json

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the LessonGenerator as a singleton.
lesson_generator = LessonGenerator()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/generate', methods=['POST'])
def generate_lesson():
    """
    # 2025-10-22: Endpoint to generate a lesson JSON.
    """
    data = request.get_json()
    topic = data.get('topic')
    grade_level = data.get('grade_level')

    if not all([topic, grade_level]):
        return jsonify({"error": "'topic' and 'grade_level' are required"}), 400

    try:
        # 2025-10-22: Generate the lesson content.
        lesson_json_str = lesson_generator.generate_lesson(topic, grade_level)
        # 2025-10-22: The LLM should return a JSON string, so we parse it.
        lesson_json = json.loads(lesson_json_str)
        return jsonify(lesson_json), 200
    except ValueError as ve:
        # 2025-10-22: Handle cases where the API key is missing.
        return jsonify({"error": str(ve)}), 503 # Service Unavailable
    except Exception as e:
        # 2025-10-22: Handle other potential errors during generation.
        return jsonify({"error": f"An error occurred during lesson generation: {str(e)}"}), 500
