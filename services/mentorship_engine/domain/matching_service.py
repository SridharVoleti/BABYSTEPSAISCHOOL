# 2025-10-22: Service for matching mentors and mentees
# Authors: Cascade

from sentence_transformers import SentenceTransformer, util

class MatchingService:
    """
    # 2025-10-22: A service to match mentors and mentees based on semantic similarity of their profiles.
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        """
        # 2025-10-22: Initialize the sentence-transformer model.
        """
        self.model = SentenceTransformer(model_name)

    def find_best_match(self, mentee_profile, mentor_profiles):
        """
        # 2025-10-22: Finds the best mentor for a mentee.
        # 'profiles' are dictionaries that should contain a text field with interests/needs.
        """
        if not mentor_profiles:
            return None

        # 2025-10-22: Generate embeddings for the mentee and all potential mentors.
        mentee_embedding = self.model.encode(mentee_profile['text'], convert_to_tensor=True)
        mentor_embeddings = self.model.encode([p['text'] for p in mentor_profiles], convert_to_tensor=True)

        # 2025-10-22: Compute cosine similarity.
        cosine_scores = util.cos_sim(mentee_embedding, mentor_embeddings)

        # 2025-10-22: Find the mentor with the highest similarity score.
        best_match_index = cosine_scores.argmax()
        best_mentor = mentor_profiles[best_match_index]

        return best_mentor
