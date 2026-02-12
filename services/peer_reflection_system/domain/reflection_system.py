# 2025-10-22: Core Peer Reflection System
# Authors: Cascade

from .reflection_analyzer import ReflectionAnalyzer

class ReflectionSystem:
    """
    # 2025-10-22: Orchestrates the peer reflection analysis process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the reflection analyzer.
        """
        self.analyzer = ReflectionAnalyzer()

    def analyze_reflection(self, reflection_text):
        """
        # 2025-10-22: Analyzes a peer reflection.
        """
        return self.analyzer.analyze(reflection_text)
