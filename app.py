from dash import Dash, html

app = Dash(__name__)
server = app.server  # For Render

app.layout = html.Div("Hello Dash is working!")

if __name__ == "__main__":
    app.run_server(debug=True)
