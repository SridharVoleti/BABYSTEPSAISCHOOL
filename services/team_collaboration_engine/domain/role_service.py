# 2025-10-22: Service for assigning roles in a team project
# Authors: Cascade

import random

class RoleService:
    """
    # 2025-10-22: A service to assign roles to team members.
    """
    def assign_roles(self, team_members, available_roles=None):
        """
        # 2025-10-22: Assigns roles to team members. This is a simple random assignment.
        """
        if available_roles is None:
            available_roles = ['Leader', 'Researcher', 'Presenter', 'Scribe']
        
        assignments = {}
        shuffled_roles = random.sample(available_roles, len(available_roles))

        for i, member in enumerate(team_members):
            # 2025-10-22: Assign roles, cycling through the list if there are more members than roles.
            assignments[member] = shuffled_roles[i % len(shuffled_roles)]
            
        return assignments
