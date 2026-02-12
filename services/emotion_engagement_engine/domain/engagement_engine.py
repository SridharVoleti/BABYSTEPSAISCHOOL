# 2025-10-22: Core Emotion–Engagement Engine
# Authors: Cascade

from .facial_emotion_service import FacialEmotionService
from .vocal_emotion_service import VocalEmotionService

class EngagementEngine:
    """
    # 2025-10-22: Orchestrates the emotion and engagement analysis.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying analysis services.
        """
        self.facial_service = FacialEmotionService()
        self.vocal_service = VocalEmotionService()

    def analyze_engagement(self, image_data=None, audio_data=None):
        """
        # 2025-10-22: Analyzes facial and vocal data to determine engagement.
        """
        facial_emotion = None
        if image_data:
            facial_emotion = self.facial_service.analyze_face(image_data)

        vocal_emotion = None
        if audio_data:
            vocal_emotion = self.vocal_service.analyze_audio(audio_data)

        # 2025-10-22: Combine results to determine an overall engagement score.
        # This is a simple placeholder logic.
        engagement_score = 0.5 # Base score
        if facial_emotion and facial_emotion['emotion'] in ['happy', 'surprised']:
            engagement_score += 0.3
        if vocal_emotion and vocal_emotion['emotion'] == 'calm':
            engagement_score += 0.1

        return {
            "facial_emotion": facial_emotion,
            "vocal_emotion": vocal_emotion,
            "engagement_score": min(1.0, engagement_score)
        }
