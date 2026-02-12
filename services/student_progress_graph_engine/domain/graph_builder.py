# 2025-10-22: Service for building a student progress graph
# Authors: Cascade

class GraphBuilder:
    """
    # 2025-10-22: A service to convert student performance data into a graph structure.
    """
    def build_graph(self, student_data):
        """
        # 2025-10-22: Builds a graph from a list of student activities.
        # 'student_data' should be a list of dicts, e.g., [{'topic': 'Math', 'score': 0.8}, ...]
        """
        nodes = []
        edges = []
        node_map = {}
        node_id_counter = 1

        # 2025-10-22: Create nodes for each unique topic.
        for activity in student_data:
            topic = activity.get('topic')
            if topic and topic not in node_map:
                node_map[topic] = node_id_counter
                nodes.append({"id": node_id_counter, "label": topic, "score": activity.get('score')})
                node_id_counter += 1

        # 2025-10-22: Create edges based on the sequence of activities.
        # This is a simple sequential model of progress.
        for i in range(len(student_data) - 1):
            topic1 = student_data[i].get('topic')
            topic2 = student_data[i+1].get('topic')
            if topic1 and topic2 and topic1 != topic2:
                edges.append({
                    "from": node_map[topic1],
                    "to": node_map[topic2],
                    "label": f"progressed from {topic1} to {topic2}"
                })

        return {"nodes": nodes, "edges": edges}
