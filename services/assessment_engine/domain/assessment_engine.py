# 2025-10-22: Core Assessment Engine
# Authors: Cascade

from .semantic_grader import SemanticGrader

class AssessmentEngine:
    """
    # 2025-10-22: Orchestrates the assessment process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the semantic grader.
        """
        self.semantic_grader = SemanticGrader()

    def assess(self, student_answer, correct_answer):
        """
        # 2025-10-22: Assesses a student's answer against a correct answer.
        """
        return self.semantic_grader.grade_response(student_answer, correct_answer)
