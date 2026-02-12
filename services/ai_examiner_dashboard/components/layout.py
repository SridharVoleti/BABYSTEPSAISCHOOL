# 2025-10-22: Layout for the AI Examiner Dashboard
# Authors: Cascade

from dash import dcc, html

def create_layout():
    """
    # 2025-10-22: Creates the layout for the Dash application.
    """
    return html.Div(children=[
        html.H1(children='AI Examiner Dashboard'),
        html.Div(children='A dashboard to visualize student performance analytics.'),
        
        # 2025-10-22: Dropdown for subject selection.
        dcc.Dropdown(
            id='subject-dropdown',
            options=[
                {'label': 'Math', 'value': 'Math'},
                {'label': 'Science', 'value': 'Science'}
            ],
            value='Math', # 2025-10-22: Default value
            clearable=False
        ),

        # 2025-10-22: Graph to display performance.
        dcc.Graph(id='performance-graph')
    ])
