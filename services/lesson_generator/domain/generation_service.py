# 2025-10-22: Service for interacting with the OpenAI API
# Authors: Cascade

from openai import OpenAI
from core.config import settings

class GenerationService:
    """
    # 2025-10-22: A service to handle the generation of content using an LLM.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the OpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_lesson_content(self, topic, grade_level):
        """
        # 2025-10-22: Generates lesson content in JSON format.
        """
        # 2025-10-22: Construct a detailed prompt for the LLM.
        prompt = f"""
        Generate a structured lesson in JSON format for a {grade_level} student on the topic of '{topic}'.
        The JSON should follow the 'Rulebook 2.1' format and include adaptive and Olympiad elements.
        The output must be a single, valid JSON object.
        """

        # 2025-10-22: Call the OpenAI API.
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in creating educational content."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 2025-10-22: Return the generated JSON content.
        return response.choices[0].message.content
