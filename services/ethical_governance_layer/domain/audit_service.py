# 2025-10-22: Service for logging audit trails
# Authors: Cascade

import datetime

class AuditService:
    """
    # 2025-10-22: A service to log audit events.
    """
    def log_event(self, event_name, user_id, details={}):
        """
        # 2025-10-22: Logs an event. In a real system, this would write to a secure, immutable log.
        """
        log_entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event_name": event_name,
            "user_id": user_id,
            "details": details
        }
        # 2025-10-22: For now, we just print to the console.
        print(f"AUDIT LOG: {log_entry}")
        return log_entry
