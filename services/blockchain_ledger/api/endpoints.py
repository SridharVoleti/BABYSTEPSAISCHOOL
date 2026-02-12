# 2025-10-22: API endpoints for the Blockchain Academic Ledger
# Authors: Cascade

# 2025-10-22: API endpoints for the Blockchain Academic Ledger
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.ledger_engine import LedgerEngine

# 2025-10-22: Create a Blueprint for the API.
api_blueprint = Blueprint('api', __name__)

# 2025-10-22: Instantiate the LedgerEngine as a singleton.
ledger_engine = LedgerEngine()

@api_blueprint.route('/health', methods=['GET'])
def health_check():
    """
    # 2025-10-22: Health check endpoint.
    """
    return jsonify({"status": "healthy"}), 200

@api_blueprint.route('/add_achievement', methods=['POST'])
def add_achievement():
    """
    # 2025-10-22: Endpoint to add a verified achievement to the ledger.
    """
    achievement_data = request.get_json()
    if not achievement_data:
        return jsonify({"error": "Achievement data is required"}), 400

    try:
        result = ledger_engine.add_achievement(achievement_data)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@api_blueprint.route('/chain', methods=['GET'])
def get_chain():
    """
    # 2025-10-22: Endpoint to view the full blockchain.
    """
    response = {
        'chain': ledger_engine.get_full_chain(),
        'length': len(ledger_engine.get_full_chain()),
    }
    return jsonify(response), 200
