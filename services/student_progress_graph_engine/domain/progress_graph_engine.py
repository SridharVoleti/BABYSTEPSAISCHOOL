# 2025-10-22: Core Student Progress Graph Engine
# Authors: Cascade

from .graph_builder import GraphBuilder

class ProgressGraphEngine:
    """
    # 2025-10-22: Orchestrates the creation of student progress graphs.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the graph builder.
        """
        self.graph_builder = GraphBuilder()

    def generate_graph(self, student_data):
        """
        # 2025-10-22: Generates a progress graph from student data.
        """
        return self.graph_builder.build_graph(student_data)
