# 2025-10-22: Main application file for AI Examiner Dashboard
# Authors: Cascade

# 2025-10-22: Main application file for AI Examiner Dashboard
# Authors: Cascade

import dash
from components.layout import create_layout
from callbacks.register_callbacks import register_callbacks

# 2025-10-22: Initialize the Dash application
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server # Expose server for Gunicorn

# 2025-10-22: Set the layout of the application
app.layout = create_layout()

# 2025-10-22: Register all callbacks
register_callbacks(app)

# 2025-10-22: Run the app
if __name__ == '__main__':
    # 2025-10-22: Run the Dash app server
    app.run_server(debug=True, host='0.0.0.0', port=8050)
