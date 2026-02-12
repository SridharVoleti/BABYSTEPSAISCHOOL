# 2025-10-22: Callbacks for the AI Examiner Dashboard
# Authors: Cascade

from dash.dependencies import Input, Output
import plotly.express as px
from data.source import load_data

def register_callbacks(app):
    """
    # 2025-10-22: Registers all callbacks for the application.
    """
    @app.callback(
        Output('performance-graph', 'figure'),
        [Input('subject-dropdown', 'value')]
    )
    def update_graph(selected_subject):
        """
        # 2025-10-22: Updates the performance graph based on the selected subject.
        """
        df = load_data()
        filtered_df = df[df.Subject == selected_subject]
        
        fig = px.bar(
            filtered_df, 
            x="Student", 
            y="Score", 
            title=f'Performance in {selected_subject}'
        )
        
        return fig
