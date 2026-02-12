# 2025-10-22: Service for analyzing peer reflections
# Authors: Cascade

from transformers import pipeline

class ReflectionAnalyzer:
    """
    # 2025-10-22: A service to analyze peer reflections for sentiment and constructiveness.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the sentiment analysis pipeline.
        # This uses a small, efficient model suitable for this task.
        """
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )

    def analyze(self, reflection_text):
        """
        # 2025-10-22: Analyzes a reflection for sentiment and constructiveness.
        """
        # 2025-10-22: Analyze sentiment.
        sentiment_result = self.sentiment_analyzer(reflection_text)[0]
        sentiment = sentiment_result['label']
        sentiment_score = sentiment_result['score']

        # 2025-10-22: Analyze constructiveness (rule-based placeholder).
        # A more advanced model could be trained for this.
        constructiveness_score = 0.5 # Base score
        if '?' in reflection_text:
            constructiveness_score += 0.2 # Asking questions is constructive
        if ' you could ' in reflection_text.lower() or ' maybe ' in reflection_text.lower():
            constructiveness_score += 0.2 # Suggestive language

        return {
            "sentiment": sentiment,
            "sentiment_score": sentiment_score,
            "constructiveness_score": min(1.0, constructiveness_score) # Cap at 1.0
        }
