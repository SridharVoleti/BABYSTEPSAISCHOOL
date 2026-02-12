# 2025-10-22: Core Mentorship Engine
# Authors: Cascade

from .matching_service import MatchingService
from .tracking_service import TrackingService

class MentorshipEngine:
    """
    # 2025-10-22: Orchestrates the mentorship matching and tracking services.
    # This class follows the Facade design pattern.
    """
    def __init__(self):
        """
        # 2025-10-22: Initialize the underlying services.
        """
        self.matching_service = MatchingService()
        self.tracking_service = TrackingService()

    def match_mentor(self, mentee_profile, mentor_profiles):
        return self.matching_service.find_best_match(mentee_profile, mentor_profiles)

    def track_interaction(self, mentor_id, mentee_id, interaction_log):
        return self.tracking_service.track_interaction(mentor_id, mentee_id, interaction_log)
