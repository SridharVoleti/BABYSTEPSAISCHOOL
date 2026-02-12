# 2025-10-22: Service for generating corrective feedback
# Authors: Cascade

from openai import OpenAI
from core.config import settings

class FeedbackService:
    """
    # 2025-10-22: A service to generate corrective feedback for mimicry attempts.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the OpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_feedback(self, original_text, user_attempt):
        """
        # 2025-10-22: Generates corrective feedback using an LLM.
        """
        # 2025-10-22: A simple diff for demonstration.
        # A real implementation would use a more robust diff algorithm or ASR output.
        is_correct = original_text.lower() == user_attempt.lower()
        if is_correct:
            return {"is_correct": True, "feedback": "Perfect!"}

        # 2025-10-22: Construct a prompt for the LLM to generate feedback.
        prompt = f"""
        A student was asked to say: '{original_text}'
        They said: '{user_attempt}'
        
        Generate a short, encouraging, and corrective feedback message for the student.
        Explain the error simply. For example: 'You said [incorrect word], but the word was [correct word]. Try again!'
        """

        # 2025-10-22: Call the OpenAI API.
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo", # Using a faster model for this task
            messages=[
                {"role": "system", "content": "You are a patient and encouraging speech coach."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )

        feedback_text = response.choices[0].message.content
        return {"is_correct": False, "feedback": feedback_text}
