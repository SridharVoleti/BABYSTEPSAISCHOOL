# 2025-10-22: Core Authenticity & Integrity Monitor Engine
# Authors: Cascade

from .plagiarism_detector import PlagiarismDetector

class IntegrityMonitor:
    """
    # 2025-10-22: Orchestrates the authenticity and integrity monitoring process.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the plagiarism detector.
        """
        self.plagiarism_detector = PlagiarismDetector()

    def monitor(self, submission_data):
        """
        # 2025-10-22: Monitors a submission for authenticity and integrity.
        """
        new_submission_text = submission_data.get('text')
        # 2025-10-22: In a real app, this would be fetched from a database.
        past_submissions = submission_data.get('past_submissions', [])

        # 2025-10-22: Check for plagiarism.
        plagiarism_result = self.plagiarism_detector.check_for_plagiarism(
            new_submission_text, 
            [s.get('text') for s in past_submissions]
        )

        # 2025-10-22: Calculate an integrity score.
        integrity_score = 1.0 - plagiarism_result.get("max_similarity", 0)
        is_authentic = integrity_score > 0.8 # Set a threshold

        # 2025-10-22: Generate flags if plagiarism is suspected.
        flags = []
        if not is_authentic:
            flags.append(f"High similarity ({plagiarism_result['max_similarity']:.2f}) found with a past submission.")

        return {
            "is_authentic": is_authentic,
            "integrity_score": integrity_score,
            "flags": flags,
            "plagiarism_details": plagiarism_result
        }
