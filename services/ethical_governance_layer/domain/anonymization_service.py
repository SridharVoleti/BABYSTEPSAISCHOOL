# 2025-10-22: Service for data anonymization
# Authors: Cascade

import hashlib

class AnonymizationService:
    """
    # 2025-10-22: A service to anonymize user data.
    """
    def anonymize(self, data, fields_to_anonymize=None):
        """
        # 2025-10-22: Anonymizes specified fields in a data dictionary.
        """
        if fields_to_anonymize is None:
            fields_to_anonymize = ['user_id', 'name', 'email']
        
        anonymized_data = data.copy()
        for field in fields_to_anonymize:
            if field in anonymized_data:
                # 2025-10-22: Replace with a hashed value (a simple form of anonymization).
                hashed_value = hashlib.sha256(str(anonymized_data[field]).encode()).hexdigest()
                anonymized_data[field] = f"ANON_{hashed_value[:8]}"
        
        return anonymized_data
