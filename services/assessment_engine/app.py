# 2025-10-22: Main application file for Assessment Engine
# Authors: Cascade

# 2025-10-22: Main application file for Assessment Engine
# Authors: Cascade

# 2025-10-22: Import create_app factory function
from core.app_factory import create_app

# 2025-10-22: Create the Flask app instance using the factory
app = create_app()

# 2025-10-22: Run the app
if __name__ == '__main__':
    # 2025-10-22: Run the Flask app. Host and port are configured in the factory.
    app.run()
