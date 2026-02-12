# 2025-10-22: Application Factory for the Lesson JSON Generator
# Authors: Cascade

from flask import Flask

def create_app():
    """
    # 2025-10-22: Application factory pattern to create and configure the Flask app.
    """
    # 2025-10-22: Initialize the Flask application
    app = Flask(__name__)

    # 2025-10-22: Import and register blueprints for API endpoints
    from api.endpoints import api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # 2025-10-22: Set configuration for the app
    app.config['DEBUG'] = True
    app.config['HOST'] = '0.0.0.0'
    app.config['PORT'] = 5003

    return app
