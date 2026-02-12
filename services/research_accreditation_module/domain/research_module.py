# 2025-10-22: Core Research & Accreditation Module
# Authors: Cascade

from .reporting_service import ReportingService

class ResearchModule:
    """
    # 2025-10-22: Orchestrates the generation of research and accreditation reports.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the reporting service.
        """
        self.reporting_service = ReportingService()

    def generate_report(self, school_data, benchmark_data):
        """
        # 2025-10-22: Generates a comparative report.
        """
        return self.reporting_service.generate_comparative_report(school_data, benchmark_data)
