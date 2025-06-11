from dash import Dash

app = Dash(__name__)
server = app.server

app.layout = "Hello"

if __name__ == "__main__":
    app.run_server(debug=True)
