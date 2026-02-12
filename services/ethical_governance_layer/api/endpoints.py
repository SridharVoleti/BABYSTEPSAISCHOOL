# 2025-10-22: API endpoints for the Ethical Governance Layer
# Authors: Cascade

# 2025-10-22: API endpoints for the Ethical Governance Layer
# Authors: Cascade

from flask import Blueprint, jsonify, request
from domain.governance_engine import GovernanceEngine

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

@api_blueprint.route('/log_event', methods=['POST'])
def log_event():
    """
    # 2025-10-22: Endpoint to log an audit event.
    """
    data = request.get_json()
    event_name = data.get('event_name')
    user_id = data.get('user_id')
    details = data.get('details', {})
    if not all([event_name, user_id]):
        return jsonify({"error": "'event_name' and 'user_id' are required"}), 400
    
    log = governance_engine.log_event(event_name, user_id, details)
    return jsonify({"message": "Event logged successfully", "log": log}), 200

@api_blueprint.route('/anonymize', methods=['POST'])
def anonymize_data():
    """
    # 2025-10-22: Endpoint to anonymize a block of data.
    """
    data = request.get_json()
    fields = data.get('fields_to_anonymize') # Optional
    anonymized_data = governance_engine.anonymize_data(data, fields)
    return jsonify({"message": "Data anonymized", "anonymized_data": anonymized_data}), 200

@api_blueprint.route('/check_consent', methods=['POST'])
def check_consent():
    """
    # 2025-10-22: Endpoint to check user consent for a specific action.
    """
    data = request.get_json()
    user_id = data.get('user_id')
    consent_type = data.get('consent_type')
    if not all([user_id, consent_type]):
        return jsonify({"error": "'user_id' and 'consent_type' are required"}), 400

    has_consent = governance_engine.check_consent(user_id, consent_type)
    return jsonify({"user_id": user_id, "consent_type": consent_type, "has_consent": has_consent}), 200
