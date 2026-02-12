# 2025-10-22: Service for detecting plagiarism
# Authors: Cascade

from sentence_transformers import SentenceTransformer, util

class PlagiarismDetector:
    """
    # 2025-10-22: A service to detect plagiarism by comparing semantic similarity.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        # 2025-10-22: Initialize the sentence-transformer model.
        """
        self.model = SentenceTransformer(model_name)

    def check_for_plagiarism(self, new_submission_text, past_submissions):
        """
        # 2025-10-22: Compares a new submission against a list of past ones.
        """
        if not past_submissions:
            return {"max_similarity": 0, "most_similar_submission_id": None}

        # 2025-10-22: Generate embeddings for the new submission and all past ones.
        new_embedding = self.model.encode(new_submission_text, convert_to_tensor=True)
        past_embeddings = self.model.encode(past_submissions, convert_to_tensor=True)

        # 2025-10-22: Compute cosine similarity between the new submission and all past ones.
        cosine_scores = util.cos_sim(new_embedding, past_embeddings)

        # 2025-10-22: Find the highest similarity score.
        max_score = max(cosine_scores[0])

        return {
            "max_similarity": max_score.item(),
            # In a real app, you'd return the ID of the most similar submission.
            "most_similar_submission_id": None 
        }
