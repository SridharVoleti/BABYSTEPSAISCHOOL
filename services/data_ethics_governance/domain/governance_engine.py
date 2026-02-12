# 2025-10-22: Core Data Ethics & Governance Engine
# Authors: Cascade

from .xai_service import XaiService

class GovernanceEngine:
    """
    # 2025-10-22: Orchestrates the data ethics and governance services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the XAI service.
        """
        self.xai_service = XaiService()

    def explain_decision(self, instance_features):
        """
        # 2025-10-22: Generates an explanation for an AI decision.
        """
        return self.xai_service.explain_prediction(instance_features)
