# 2025-10-22: API endpoints for the Data Ethics & Governance Service
# Authors: Cascade

# 2025-10-22: API endpoints for the Data Ethics & Governance Service
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.governance_engine import GovernanceEngine
import numpy as np

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the GovernanceEngine as a singleton.
governance_engine = GovernanceEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/explain', methods=['POST'])
def explain_decision():
    """
    # 2025-10-22: Endpoint to generate an explanation for an AI decision.
    """
    data = request.get_json()
    instance_features = data.get('features')

    if not instance_features or not isinstance(instance_features, list):
        return jsonify({"error": "A 'features' list is required"}), 400

    try:
        # 2025-10-22: Convert features to a numpy array for the model.
        features_np = np.array(instance_features)
        
        # 2025-10-22: Use the engine to generate the explanation.
        explanation = governance_engine.explain_decision(features_np)
        return jsonify({"message": "Explanation generated", "explanation": explanation}), 200
    except Exception as e:
        # 2025-10-22: Log the exception in a real application.
        return jsonify({"error": f"An error occurred during explanation generation: {str(e)}"}), 500
