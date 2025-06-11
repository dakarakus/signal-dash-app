import pandas as pd
import os
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

app = Dash(__name__)
server = app.server  # Needed by Render

# Load your Excel file
df = pd.read_excel("your_data.xlsx")

# Line chart figure
line_fig = go.Figure()
line_fig.add_trace(go.Scatter(x=df['Point ID'], y=df['Signal Level 1'], mode='lines+markers', name='Signal Level 1'))
line_fig.add_trace(go.Scatter(x=df['Point ID'], y=df['Signal Level 2'], mode='lines+markers', name='Signal Level 2'))
line_fig.update_layout(hovermode='x unified', title='Signal Levels Over Points')

# App layout
app.layout = html.Div([
    dcc.Graph(id='line-chart', figure=line_fig),
    dcc.Graph(id='map-chart')
])

# Callback to update map when hovering on line chart
@app.callback(
    Output('map-chart', 'figure'),
    Input('line-chart', 'hoverData')
)
def update_map(hoverData):
    if hoverData:
        point_id = hoverData['points'][0]['x']
        point = df[df['Point ID'] == point_id].iloc[0]
        map_fig = px.scatter_mapbox(
            df,
            lat='Latitude',
            lon='Longitude',
            hover_name='Point ID',
            zoom=10,
            height=500
        )
        map_fig.update_layout(mapbox_style="open-street-map")
        # Highlight selected point
        map_fig.add_trace(go.Scattermapbox(
            lat=[point['Latitude']],
            lon=[point['Longitude']],
            mode='markers',
            marker=dict(size=15, color='red'),
            name='Selected Point'
        ))
        return map_fig
    else:
        map_fig = px.scatter_mapbox(
            df,
            lat='Latitude',
            lon='Longitude',
            hover_name='Point ID',
            zoom=10,
            height=500
        )
        map_fig.update_layout(mapbox_style="open-street-map")
        return map_fig

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8050))
    app.run_server(debug=False, host='0.0.0.0', port=port)
