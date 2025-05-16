import dash
from dash import dcc, html, dash_table, Input, Output 
import pandas as pd
import plotly.graph_objects as go
import redis
import json


redis_client = redis.Redis(host='redis', port=6379, db=0)


app = dash.Dash(__name__)
app.title = "Fraud Detection Dashboard"
server = app.server


app.layout = html.Div([
    html.H2("Real-Time Fraud Detection Dashboard", style={'textAlign': 'center', 'color': '#4CAF50'}),

    # Metrics display
    html.Div(id='metrics', style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '20px'}),

    # Filter for number of transactions
    html.Div([
        html.Label("Number of Transactions to Fetch:"),
        dcc.Dropdown(
            id='limit-dropdown',
            options=[{'label': str(i), 'value': i} for i in [50, 100, 200, 300, 400, 500]],
            value=200,
            clearable=False,
            style={'width': '100px'}
        )
    ], style={'padding': '20px'}),


    dcc.Graph(id='histogram-graph'),

    html.Div([
        html.H4("Transactions Table"),
        html.Label("Records Per Page:"),
        dcc.Dropdown(
            id='page-size-dropdown',
            options=[{'label': str(i), 'value': i} for i in [10, 20, 50, 100]],
            value=20,
            clearable=False,
            style={'width': '85px'}
        )
    ], style={'padding': '10px'}),

    html.Div(id='table-container'),

    # Auto-refresh every 15 seconds
    dcc.Interval(id='interval', interval=15000, n_intervals=0)
])

# Helper to get data from Redis
def get_transactions(limit):
    raw_data = redis_client.lrange("tx_cache", 0, limit - 1)
    parsed = []
    for item in raw_data:
        try:
            tx = json.loads(item)
            parsed.append(tx)
        except Exception:
            continue
    return pd.DataFrame(parsed)

# Callback
@app.callback(
    [Output('metrics', 'children'),
     Output('histogram-graph', 'figure'),
     Output('table-container', 'children')],
    [Input('interval', 'n_intervals'),
     Input('limit-dropdown', 'value'),
     Input('page-size-dropdown', 'value')]
)
def update_dashboard(_, limit, page_size):
    df = get_transactions(limit)
    if df.empty or 'is_fraud' not in df.columns:
        return html.Div("No data available."), go.Figure(), "No transactions to display."


    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['is_fraud'] = df['is_fraud'].astype(int)

    total = len(df)
    fraud = df['is_fraud'].sum()
    legit = total - fraud

    # Metrics
    metrics = [
        html.Div([
            html.H4("Total Transactions"),
            html.P(f"{total}", style={"fontSize": "24px", "fontWeight": "bold"})
        ], style={"backgroundColor": "#f0f0f0", "padding": "15px", "borderRadius": "8px"}),

        html.Div([
            html.H4("Fraudulent"),
            html.P(f"{fraud}", style={"fontSize": "24px", "color": "red", "fontWeight": "bold"})
        ], style={"backgroundColor": "#fff0f0", "padding": "15px", "borderRadius": "8px"}),

        html.Div([
            html.H4("Legitimate"),
            html.P(f"{legit}", style={"fontSize": "24px", "color": "green", "fontWeight": "bold"})
        ], style={"backgroundColor": "#f0fff0", "padding": "15px", "borderRadius": "8px"}),
    ]

    # Graph
    fraud_df = df[df['is_fraud'] == 1]
    legit_df = df[df['is_fraud'] == 0]
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=fraud_df['timestamp'], name='Fraudulent', marker_color='red', nbinsx=20))
    fig.add_trace(go.Histogram(x=legit_df['timestamp'], name='Legitimate', marker_color='green', nbinsx=20))
    fig.update_layout(barmode='overlay', title="Transaction Volume Over Time", xaxis_title="Time", yaxis_title="Count", template='plotly_dark')

    # Select columns to display
    display_columns = [
        'timestamp', 'sender_wallet', 'receiver_wallet', 'amount',
        'currency', 'location', 'device_type', 'is_fraud'
    ]
    df = df[display_columns]

    table = dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df.columns],
        data=df.to_dict('records'),
        page_size=page_size,
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'minWidth': '120px', 'whiteSpace': 'normal'},
        style_header={'backgroundColor': '#e1e1e1', 'fontWeight': 'bold'}
    )

    return metrics, fig, table

# Run app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
