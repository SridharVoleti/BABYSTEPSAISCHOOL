# 2025-10-22: Core Offline Activity Verification Engine
# Authors: Cascade

from .video_processor import VideoProcessor

class VerificationEngine:
    """
    # 2025-10-22: Orchestrates the verification process for offline activities.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the video processor.
        """
        self.video_processor = VideoProcessor()

    def verify(self, video_file_path):
        """
        # 2025-10-22: Verifies an offline activity video.
        """
        analysis_results = self.video_processor.analyze_video(video_file_path)

        # 2025-10-22: Apply a simple rule-based logic for verification.
        face_presence = analysis_results.get("face_presence_percentage", 0)
        hand_presence = analysis_results.get("hand_presence_percentage", 0)

        # 2025-10-22: Calculate an authenticity score.
        # Score is higher if both face and hands are present.
        authenticity_score = (face_presence * 0.7) + (hand_presence * 0.3)
        authenticity_score /= 100 # Normalize to 0-1 range

        # 2025-10-22: Determine if the submission is verified.
        is_verified = authenticity_score > 0.7 and face_presence > 50

        # 2025-10-22: Generate flags if something is suspicious.
        flags = []
        if face_presence < 50:
            flags.append("Student's face was not visible for a significant portion of the video.")
        if hand_presence < 20:
            flags.append("Student's hands were not actively engaged for a significant portion of the video.")

        return {
            "is_verified": is_verified,
            "authenticity_score": authenticity_score,
            "flags": flags,
            "analysis_details": analysis_results
        }
