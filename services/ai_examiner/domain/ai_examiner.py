# 2025-10-22: Core AI Examiner Engine
# Authors: Cascade

from .report_generator import ReportGenerator

class AiExaminer:
    """
    # 2025-10-22: Orchestrates the report generation process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the report generator.
        """
        self.report_generator = ReportGenerator()

    def examine(self, performance_data):
        """
        # 2025-10-22: Generates a complete examiner report.
        """
        return self.report_generator.generate_report(performance_data)
