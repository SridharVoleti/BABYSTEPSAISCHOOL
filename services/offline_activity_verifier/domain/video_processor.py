# 2025-10-22: Service for processing and analyzing video files
# Authors: Cascade

import cv2
import mediapipe as mp
import tempfile
import os

class VideoProcessor:
    """
    # 2025-10-22: A service to analyze video frames for face and hand presence.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize Mediapipe solutions for face and hand detection.
        """
        self.mp_face_detection = mp.solutions.face_detection
        self.mp_hands = mp.solutions.hands

    def analyze_video(self, video_file_path):
        """
        # 2025-10-22: Processes a video file to detect face and hand presence.
        # This is a simplified version and processes only a subset of frames for efficiency.
        """
        cap = cv2.VideoCapture(video_file_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_with_face = 0
        frames_with_hands = 0
        processed_frames = 0

        with self.mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection,
             self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5) as hands:
            
            # 2025-10-22: Analyze every Nth frame to speed up processing.
            frame_interval = max(1, total_frames // 20) # Analyze ~20 frames

            for i in range(0, total_frames, frame_interval):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                success, image = cap.read()
                if not success:
                    continue
                
                processed_frames += 1
                # 2025-10-22: Convert the BGR image to RGB.
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # 2025-10-22: Process the image for face detection.
                face_results = face_detection.process(image_rgb)
                if face_results.detections:
                    frames_with_face += 1

                # 2025-10-22: Process the image for hand detection.
                hand_results = hands.process(image_rgb)
                if hand_results.multi_hand_landmarks:
                    frames_with_hands += 1

        cap.release()

        # 2025-10-22: Calculate percentages.
        face_presence_percent = (frames_with_face / processed_frames) * 100 if processed_frames > 0 else 0
        hand_presence_percent = (frames_with_hands / processed_frames) * 100 if processed_frames > 0 else 0

        return {
            "face_presence_percentage": face_presence_percent,
            "hand_presence_percentage": hand_presence_percent,
            "total_frames_processed": processed_frames
        }
