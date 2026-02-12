# 2025-10-22: API endpoints for the AI Training & Feedback Loop
# Authors: Cascade

# 2025-10-22: API endpoints for the AI Training & Feedback Loop
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.training_loop_engine import TrainingLoopEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the TrainingLoopEngine as a singleton.
training_loop_engine = TrainingLoopEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/start_training_round', methods=['POST'])
def start_training_round():
    """
    # 2025-10-22: Endpoint to start a new round of federated learning.
    """
    data = request.get_json()
    model_name = data.get('model_name')
    data_config = data.get('data_config')

    if not all([model_name, data_config]):
        return jsonify({"error": "'model_name' and 'data_config' are required"}), 400

    try:
        # 2025-10-22: Use the engine to start the training round.
        result = training_loop_engine.start_training_round(model_name, data_config)
        return jsonify(result), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred while starting the training round: {str(e)}"}), 500
