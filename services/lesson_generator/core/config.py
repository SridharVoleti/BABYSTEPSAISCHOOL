# 2025-10-22: Configuration for the Lesson JSON Generator
# Authors: Cascade

import os

# 2025-10-22: Load environment variables for configuration.
# In a production environment, use a more robust method like python-decouple.
from dotenv import load_dotenv
load_dotenv()

class Settings:
    """
    # 2025-10-22: Application settings.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

settings = Settings()
