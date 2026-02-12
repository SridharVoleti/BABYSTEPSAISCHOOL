# 2025-10-22: Core AI Training & Feedback Loop Engine
# Authors: Cascade

from .federated_learning_service import FederatedLearningService

class TrainingLoopEngine:
    """
    # 2025-10-22: Orchestrates the AI training and feedback loop.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the federated learning service.
        """
        self.fl_service = FederatedLearningService()

    def start_training_round(self, model_name, data_config):
        """
        # 2025-10-22: Starts a new round of federated learning.
        """
        return self.fl_service.start_training_round(model_name, data_config)
