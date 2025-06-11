import base64
import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Excel File')]),
        style={
            'width': '300px',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),
    dcc.Store(id='stored-data'),
    html.Div(id='charts-container')  # Here we will place all charts and maps
])

def parse_excel(contents):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    # Read excel file to pandas dataframe
    df = pd.read_excel(io.BytesIO(decoded))
    return df

@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents')
)
def store_uploaded_file(contents):
    if contents is None:
        return None
    df = parse_excel(contents)
    return df.to_json(date_format='iso', orient='split')

@app.callback(
    Output('charts-container', 'children'),
    Input('stored-data', 'data')
)
def update_charts(jsonified_data):
    if jsonified_data is None:
        return html.Div("Please upload an Excel file to see the charts.")
    
    df = pd.read_json(jsonified_data, orient='split')
    
    charts = []
    # For example, assume your df has these columns for 5 charts
    # You can loop and create charts dynamically here
    for i in range(1, 6):
        # Create line chart for Signal Level i
        line_fig = go.Figure()
        y_col = f'Signal Level {i}'
        if y_col not in df.columns:
            continue  # Skip if column doesn't exist
        
        line_fig.add_trace(go.Scatter(x=df['Point ID'], y=df[y_col], mode='lines+markers', name=y_col))
        line_fig.update_layout(hovermode='x unified', title=f'Signal Levels Over Points - {y_col}')
        
        # Create map chart
        map_fig = px.scatter_mapbox(
            df,
            lat='Latitude',
            lon='Longitude',
            hover_name='Point ID',
            zoom=10,
            height=300
        )
        map_fig.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":30,"l":0,"b":0})
        
        # Append chart and map to container
        charts.append(html.Div([
            dcc.Graph(figure=line_fig),
            dcc.Graph(figure=map_fig)
        ], style={'marginBottom': '50px'}))
    
    return charts

if __name__ == '__main__':
    app.run_server(debug=True)
