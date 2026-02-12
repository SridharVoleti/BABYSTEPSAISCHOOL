# 2025-10-22: Data source for the dashboard
# Authors: Cascade

import pandas as pd

def load_data():
    """
    # 2025-10-22: Loads data for the dashboard.
    # This is a placeholder; in a real app, this would connect to a database (e.g., PostgreSQL).
    """
    df = pd.DataFrame({
        "Student": ["Alex", "Beth", "Chris", "Diana", "Ethan", "Alex", "Beth", "Chris", "Diana", "Ethan"],
        "Score": [85, 92, 78, 88, 95, 90, 81, 85, 94, 89],
        "Subject": ["Math", "Math", "Math", "Math", "Math", "Science", "Science", "Science", "Science", "Science"],
    })
    return df
