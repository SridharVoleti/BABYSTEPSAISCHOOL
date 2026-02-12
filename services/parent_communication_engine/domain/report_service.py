# 2025-10-22: Service for generating parent-facing reports
# Authors: Cascade

from openai import OpenAI
from core.config import settings
import json

class ReportService:
    """
    # 2025-10-22: A service to generate personalized reports for parents.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the OpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_weekly_report(self, student_data):
        """
        # 2025-10-22: Generates a weekly summary report using an LLM.
        """
        # 2025-10-22: Convert the student data to a string for the prompt.
        data_summary = json.dumps(student_data, indent=2)

        # 2025-10-22: Construct a detailed prompt for the LLM.
        prompt = f"""
        Act as a friendly and encouraging teacher. You are writing a weekly progress report for a student's parent.
        The student's data for the week is as follows:
        {data_summary}

        Generate a brief, personalized report in JSON format. The report must include:
        1. A 'summary' of the student's week, written in a warm and positive tone.
        2. A list of 'highlights' (key achievements).
        3. A list of 'suggestions' for activities to do at home.
        The output must be a single, valid JSON object.
        """

        # 2025-10-22: Call the OpenAI API.
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful teacher communicating with a parent."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 2025-10-22: Return the generated JSON content.
        return response.choices[0].message.content
