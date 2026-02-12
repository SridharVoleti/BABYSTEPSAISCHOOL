# 2025-10-22: Core Adaptive Learning Engine
# Authors: Cascade

from .emotion_detection import EmotionDetector
from .understanding_analysis import UnderstandingAnalyzer

class AdaptiveEngine:
    """
    # 2025-10-22: Orchestrates the analysis of student submissions to generate adaptive feedback.
    # This class follows the Facade design pattern to simplify the interface to the underlying services.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying analysis services.
        """
        self.emotion_detector = EmotionDetector()
        self.understanding_analyzer = UnderstandingAnalyzer()

    def get_adaptive_feedback(self, submission_data):
        """
        # 2025-10-22: Processes submission data and returns adaptive feedback.
        """
        text_response = submission_data.get('text_response')
        audio_response = submission_data.get('audio_response')
        expected_keywords = submission_data.get('expected_keywords', [])

        understanding_analysis = None
        if text_response:
            understanding_analysis = self.understanding_analyzer.analyze_text(text_response, expected_keywords)

        emotion_analysis = None
        if audio_response:
            emotion_analysis = self.emotion_detector.detect_emotion(audio_response)

        # 2025-10-22: Combine analyses to generate final feedback (placeholder logic)
        feedback = "Great effort!"
        if understanding_analysis and understanding_analysis['keyword_score'] < 0.5:
            feedback = "Good start, but let's review the key concepts."

        return {
            "feedback": feedback,
            "understanding_analysis": understanding_analysis,
            "emotion_analysis": emotion_analysis
        }
