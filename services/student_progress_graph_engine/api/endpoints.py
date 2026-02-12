# 2025-10-22: API endpoints for the Student Progress Graph Engine
# Authors: Cascade

# 2025-10-22: API endpoints for the Student Progress Graph Engine
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.progress_graph_engine import ProgressGraphEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the ProgressGraphEngine as a singleton.
progress_graph_engine = ProgressGraphEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/generate_graph', methods=['POST'])
def generate_graph():
    """
    # 2025-10-22: Endpoint to generate a progress graph from student data.
    """
    student_data = request.get_json()
    if not student_data or not isinstance(student_data, list):
        return jsonify({"error": "A JSON list of student activities is required"}), 400

    try:
        # 2025-10-22: Use the engine to generate the graph data.
        graph_data = progress_graph_engine.generate_graph(student_data)
        return jsonify({"message": "Graph data generated", "graph_data": graph_data}), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during graph generation: {str(e)}"}), 500
