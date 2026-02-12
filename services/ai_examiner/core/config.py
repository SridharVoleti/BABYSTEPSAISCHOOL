# 2025-10-22: Configuration for the AI Examiner
# Authors: Cascade

import os
from dotenv import load_dotenv

# 2025-10-22: Load environment variables.
load_dotenv()

class Settings:
    """
    # 2025-10-22: Application settings.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()
