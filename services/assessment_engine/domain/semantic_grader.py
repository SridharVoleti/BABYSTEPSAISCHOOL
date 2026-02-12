# 2025-10-22: Semantic Grading Service
# Authors: Cascade

from sentence_transformers import SentenceTransformer, util

class SemanticGrader:
    """
    # 2025-10-22: A service to grade student responses based on semantic similarity.
    # This uses a pre-trained sentence-transformer model.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        # 2025-10-22: Initialize the sentence-transformer model.
        # The model is loaded once and reused, which is efficient.
        """
        self.model = SentenceTransformer(model_name)

    def grade_response(self, student_answer, correct_answer):
        """
        # 2025-10-22: Calculates the semantic similarity between two texts.
        """
        # 2025-10-22: Generate embeddings for both texts.
        embedding1 = self.model.encode(student_answer, convert_to_tensor=True)
        embedding2 = self.model.encode(correct_answer, convert_to_tensor=True)

        # 2025-10-22: Compute cosine similarity.
        cosine_scores = util.cos_sim(embedding1, embedding2)
        score = cosine_scores.item()

        # 2025-10-22: Generate simple feedback based on the score.
        if score > 0.8:
            feedback = "Excellent understanding!"
        elif score > 0.6:
            feedback = "Good job, you've grasped the main idea."
        else:
            feedback = "You're on the right track, but let's review the key points."

        return {
            "score": score,
            "feedback": feedback
        }
