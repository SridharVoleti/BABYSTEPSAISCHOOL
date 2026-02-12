# 2025-10-22: Service for generating Olympiad challenges
# Authors: Cascade

from openai import OpenAI
from core.config import settings

class ChallengeGenerator:
    """
    # 2025-10-22: A service to generate reasoning-based challenges using an LLM.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the OpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_challenge(self, topic, difficulty):
        """
        # 2025-10-22: Generates a reasoning-based challenge.
        """
        # 2025-10-22: Construct a prompt for the LLM.
        prompt = f"""
        Create a single, reasoning-based Olympiad-style challenge for a student.
        The topic is '{topic}'.
        The difficulty should be '{difficulty}'.
        The output must be a JSON object with two keys: 'question' and 'solution'.
        The question should be a word problem that requires logical deduction.
        """

        # 2025-10-22: Call the OpenAI API.
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in creating educational reasoning problems."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 2025-10-22: Return the generated JSON content.
        return response.choices[0].message.content
