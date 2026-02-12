# 2025-10-22: Core Olympiad Engine
# Authors: Cascade

from .challenge_generator import ChallengeGenerator

class OlympiadEngine:
    """
    # 2025-10-22: Orchestrates the challenge generation process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the challenge generator.
        """
        self.challenge_generator = ChallengeGenerator()

    def generate_challenge(self, topic, difficulty):
        """
        # 2025-10-22: Generates a complete Olympiad challenge.
        """
        return self.challenge_generator.generate_challenge(topic, difficulty)
