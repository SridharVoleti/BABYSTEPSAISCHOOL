# 2025-10-22: Core Ethical Governance Engine
# Authors: Cascade

from .audit_service import AuditService
from .anonymization_service import AnonymizationService
from .consent_service import ConsentService

class GovernanceEngine:
    """
    # 2025-10-22: Orchestrates the ethical governance services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying services.
        """
        self.audit_service = AuditService()
        self.anonymization_service = AnonymizationService()
        self.consent_service = ConsentService()

    def log_event(self, event_name, user_id, details={}):
        return self.audit_service.log_event(event_name, user_id, details)

    def anonymize_data(self, data, fields_to_anonymize=None):
        return self.anonymization_service.anonymize(data, fields_to_anonymize)

    def check_consent(self, user_id, consent_type):
        return self.consent_service.check_consent(user_id, consent_type)
