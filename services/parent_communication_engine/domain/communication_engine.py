# 2025-10-22: Core Parent Communication Engine
# Authors: Cascade

from .report_service import ReportService

class CommunicationEngine:
    """
    # 2025-10-22: Orchestrates the parent communication services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the report service.
        """
        self.report_service = ReportService()

    def generate_report(self, student_data):
        """
        # 2025-10-22: Generates a weekly report for a parent.
        """
        return self.report_service.generate_weekly_report(student_data)
