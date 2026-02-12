# 2025-10-22: Core Read-Along & Mimic Engine
# Authors: Cascade

from .alignment_service import AlignmentService
from .pronunciation_service import PronunciationService

class MimicEngine:
    """
    # 2025-10-22: Orchestrates the alignment and pronunciation analysis services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying services.
        """
        self.alignment_service = AlignmentService()
        self.pronunciation_service = PronunciationService()

    def analyze_mimicry(self, original_text, original_audio, student_audio):
        """
        # 2025-10-22: Provides a complete analysis of a student's mimicry.
        """
        # 2025-10-22: Generate timestamps for the original audio.
        timestamps = self.alignment_service.generate_timestamps(original_text, original_audio)

        # 2025-10-22: Score the student's pronunciation.
        pronunciation_score = self.pronunciation_service.score_pronunciation(original_text, student_audio)

        return {
            "timestamps": timestamps,
            "pronunciation_analysis": pronunciation_score
        }
