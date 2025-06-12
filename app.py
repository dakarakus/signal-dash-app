import base64
import io
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, State, ALL

app = Dash(__name__)
server = app.server

fixed_cols = ['Point ID', 'Longitude', 'Latitude']

def create_multi_line_chart(df, title='Chart Name'):
    fig = go.Figure()
    for col in df.columns:
        if col not in fixed_cols:
            fig.add_trace(go.Scatter(
                x=df['Point ID'], y=df[col],
                mode='lines+markers',
                name=col
            ))
    fig.update_layout(title=title, hovermode='x unified')
    return fig

chart_titles = {
    'ss-rsrp': 'Signal Strength Levels [dBm]',
    'dl-sinr': 'PDSCH C/(I+N) [dB]',
    'dl-thrp': 'Downlink Throughput [kbps]',
    'ul-sinr': 'PUSCH & PUCCH C/(I+N) [dB]',
    'ul-thrp': 'Uplink Throughput [kbps]',
    # You can add more mappings if needed
}

app.layout = html.Div([
    html.H1("Multi-Sheet Signal Dashboard with File Upload"),
    
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select Excel File')]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        multiple=False
    ),

    dcc.Store(id='stored-data'),

    html.Div(id='output-charts')
])

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            xls = pd.ExcelFile(io.BytesIO(decoded))
            dfs = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
            return dfs
        else:
            return None
    except Exception as e:
        print(e)
        return None

@app.callback(
    Output('stored-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def store_uploaded_file(contents, filename):
    if contents is not None:
        dfs = parse_contents(contents, filename)
        if dfs is None:
            return {}
        jsonified = {sheet: dfs[sheet].to_json(date_format='iso', orient='split') for sheet in dfs}
        return jsonified
    return {}

@app.callback(
    Output('output-charts', 'children'),
    Input('stored-data', 'data')
)
def update_output_charts(data):
    if not data:
        return html.Div("Upload an Excel file to see charts.")
    
    dfs = {sheet: pd.read_json(data[sheet], orient='split') for sheet in data}
    
    children = []
    for sheet in dfs:
        if sheet == 'sites':
            continue
        df = dfs[sheet]
        children.append(html.Div([
            html.H2(chart_titles.get(sheet, sheet)),
            dcc.Graph(
                id={'type': 'line-chart', 'sheet': sheet},
                figure=create_multi_line_chart(df, title=chart_titles.get(sheet, sheet))
            ),
            dcc.Graph(id={'type': 'map-chart', 'sheet': sheet})
        ], style={'marginBottom': '50px'}))
    return children

@app.callback(
    Output({'type': 'map-chart', 'sheet': ALL}, 'figure'),
    Input({'type': 'line-chart', 'sheet': ALL}, 'hoverData'),
    State('stored-data', 'data'),
    prevent_initial_call=True
)
def update_maps(all_hover_data, stored_data):
    results = []
    if not stored_data:
        return [go.Figure() for _ in all_hover_data]
    
    dfs = {sheet: pd.read_json(stored_data[sheet], orient='split') for sheet in stored_data}
    sites_df = dfs.get('sites')

    sheets = [s for s in dfs if s != 'sites']

    for sheet, hoverData in zip(sheets, all_hover_data):
        df = dfs[sheet]
        point = None
        if hoverData is not None:
            try:
                point_id = hoverData['points'][0]['x']
                filtered = df[df['Point ID'] == point_id]
                if not filtered.empty:
                    point = filtered.iloc[0]
            except Exception:
                pass

        # Base map with measurement points
        map_fig = px.scatter_mapbox(
            df,
            lat='Latitude',
            lon='Longitude',
            hover_name='Point ID',
            zoom=10,
            height=400
        )
        map_fig.update_traces(marker=dict(size=9, color='gray'))
        map_fig.update_layout(mapbox_style="open-street-map")

        # Add site markers (blue with icon)
        if sites_df is not None:
            map_fig.add_trace(go.Scattermapbox(
                lat=sites_df['Latitude'],
                lon=sites_df['Longitude'],
                mode='markers+text',
                marker=dict(size=22, color='blue', symbol='triangle-up-dot'),
                text=sites_df['Name'],
                textposition='top right',
                name='Sites'
            ))

        # Highlight hovered point
        if point is not None:
            map_fig.add_trace(go.Scattermapbox(
                lat=[point['Latitude']],
                lon=[point['Longitude']],
                mode='markers',
                marker=dict(size=15, color='red'),
                name='Selected Point'
            ))

        results.append(map_fig)

    return results

if __name__ == '__main__':
    app.run(debug=True)
