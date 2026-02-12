# 2025-10-22: Core Lesson Generator Engine
# Authors: Cascade

from .generation_service import GenerationService

class LessonGenerator:
    """
    # 2025-10-22: Orchestrates the lesson generation process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the generation service.
        """
        self.generation_service = GenerationService()

    def generate_lesson(self, topic, grade_level):
        """
        # 2025-10-22: Generates a complete lesson plan in JSON format.
        """
        return self.generation_service.generate_lesson_content(topic, grade_level)
