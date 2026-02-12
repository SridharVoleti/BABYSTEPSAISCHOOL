# 2025-10-22: Service for generating AI examiner reports
# Authors: Cascade

from openai import OpenAI
from core.config import settings
import json

class ReportGenerator:
    """
    # 2025-10-22: A service to generate examiner-style reports from student data.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the OpenAI client.
        """
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables.")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def generate_report(self, student_performance_data):
        """
        # 2025-10-22: Generates a comprehensive report using an LLM.
        """
        # 2025-10-22: Convert the performance data to a string for the prompt.
        performance_summary = json.dumps(student_performance_data, indent=2)

        # 2025-10-22: Construct a detailed prompt for the LLM.
        prompt = f"""
        Act as an expert AI examiner. You are reviewing a student's performance data.
        The data is as follows:
        {performance_summary}

        Generate a comprehensive report in JSON format. The report must include:
        1. A 'summary' of the student's overall performance.
        2. A list of 'strengths'.
        3. A list of 'areas_for_improvement' with actionable suggestions.
        The tone should be encouraging but professional. The output must be a single, valid JSON object.
        """

        # 2025-10-22: Call the OpenAI API.
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI school examiner providing student feedback."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # 2025-10-22: Return the generated JSON content.
        return response.choices[0].message.content
