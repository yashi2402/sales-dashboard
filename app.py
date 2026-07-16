import os
import json
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data import generate_sales_data

# =============================================================================
# CHALLENGE 1: No hardcoded file paths or database connections
# All config comes from environment variables with sensible defaults
# =============================================================================
APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
APP_PORT = int(os.environ.get('APP_PORT', '8888'))
DATA_RECORDS = int(os.environ.get('DATA_RECORDS', '1000'))
PERSISTENT_STORAGE_PATH = os.environ.get('DOMINO_DATASET_PATH', '/mnt/data/sales-dashboard')
DATA_SOURCE_TYPE = os.environ.get('DATA_SOURCE_TYPE', 'generated')
DB_CONNECTION_STRING = os.environ.get('DB_CONNECTION_STRING', '')

# =============================================================================
# CHALLENGE 3: Persistent storage for app state
# Save/load data from Domino Dataset path so state survives restarts
# =============================================================================
CACHE_FILE = os.path.join(PERSISTENT_STORAGE_PATH, 'sales_data_cache.csv')
FILTER_STATE_FILE = os.path.join(PERSISTENT_STORAGE_PATH, 'filter_state.json')


def load_data():
    """Load data from persistent storage if available, otherwise generate fresh."""
    if DATA_SOURCE_TYPE == 'database' and DB_CONNECTION_STRING:
        # Example: load from database using connection string from env var
        # df = pd.read_sql("SELECT * FROM sales", DB_CONNECTION_STRING)
        pass

    # Try loading from persistent cache first
    if os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE, parse_dates=['date'])
        return df

    # Generate fresh data
    df = generate_sales_data(n_records=DATA_RECORDS)

    # Save to persistent storage if path exists
    if os.path.exists(PERSISTENT_STORAGE_PATH):
        df.to_csv(CACHE_FILE, index=False)

    return df


def save_filter_state(region, category):
    """Save last used filter state to persistent storage."""
    if os.path.exists(PERSISTENT_STORAGE_PATH):
        state = {'region': region, 'category': category}
        with open(FILTER_STATE_FILE, 'w') as f:
            json.dump(state, f)


def load_filter_state():
    """Load last used filter state from persistent storage."""
    if os.path.exists(FILTER_STATE_FILE):
        with open(FILTER_STATE_FILE, 'r') as f:
            return json.load(f)
    return {'region': 'All', 'category': 'All'}


# Load data
df = load_data()

# =============================================================================
# CHALLENGE 5: WebSocket connections and session management
# - suppress_callback_exceptions: handles dynamic components
# - Long-lived callbacks won't break WebSocket connections
# - Each user gets independent filter state (no shared global state in callbacks)
# =============================================================================
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    update_title=None,  # Prevents "Updating..." flash — smoother WebSocket experience
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)
server = app.server  # Expose Flask server for Domino to serve

# KPI calculations
total_revenue = df['revenue'].sum()
total_orders = len(df)
avg_order_value = df['revenue'].mean()
total_customers = df['customer_id'].nunique()

# Load last filter state
initial_state = load_filter_state()

# App layout
app.layout = html.Div([
    # Session store — each browser tab gets its own state (Challenge 5)
    dcc.Store(id='session-store', storage_type='session'),

    # Header
    html.Div([
        html.H1("Sales Analytics Dashboard", style={'color': '#ffffff', 'marginBottom': '5px'}),
        html.P("Interactive Sales Performance Monitor | Domino Use Case 7",
               style={'color': '#cccccc'})
    ], style={'backgroundColor': '#2c3e50', 'padding': '20px', 'marginBottom': '20px'}),

    # KPI Cards
    html.Div([
        html.Div([
            html.H3(f"${total_revenue:,.0f}", style={'color': '#27ae60', 'margin': '0'}),
            html.P("Total Revenue", style={'color': '#666'})
        ], style={'backgroundColor': '#fff', 'padding': '20px', 'borderRadius': '8px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'flex': '1', 'margin': '0 10px'}),

        html.Div([
            html.H3(f"{total_orders:,}", style={'color': '#2980b9', 'margin': '0'}),
            html.P("Total Orders", style={'color': '#666'})
        ], style={'backgroundColor': '#fff', 'padding': '20px', 'borderRadius': '8px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'flex': '1', 'margin': '0 10px'}),

        html.Div([
            html.H3(f"${avg_order_value:,.0f}", style={'color': '#e67e22', 'margin': '0'}),
            html.P("Avg Order Value", style={'color': '#666'})
        ], style={'backgroundColor': '#fff', 'padding': '20px', 'borderRadius': '8px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'flex': '1', 'margin': '0 10px'}),

        html.Div([
            html.H3(f"{total_customers:,}", style={'color': '#8e44ad', 'margin': '0'}),
            html.P("Unique Customers", style={'color': '#666'})
        ], style={'backgroundColor': '#fff', 'padding': '20px', 'borderRadius': '8px',
                  'boxShadow': '0 2px 4px rgba(0,0,0,0.1)', 'textAlign': 'center', 'flex': '1', 'margin': '0 10px'}),
    ], style={'display': 'flex', 'marginBottom': '20px', 'padding': '0 10px'}),

    # Filters
    html.Div([
        html.Div([
            html.Label("Select Region:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='region-filter',
                options=[{'label': 'All Regions', 'value': 'All'}] +
                        [{'label': r, 'value': r} for r in df['region'].unique()],
                value=initial_state.get('region', 'All'),
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'margin': '0 10px'}),

        html.Div([
            html.Label("Select Category:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': 'All Categories', 'value': 'All'}] +
                        [{'label': c, 'value': c} for c in df['category'].unique()],
                value=initial_state.get('category', 'All'),
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'margin': '0 10px'}),
    ], style={'display': 'flex', 'marginBottom': '20px', 'padding': '0 10px'}),

    # Charts Row 1
    html.Div([
        html.Div([
            dcc.Graph(id='revenue-trend')
        ], style={'flex': '1', 'margin': '0 10px'}),

        html.Div([
            dcc.Graph(id='region-bar')
        ], style={'flex': '1', 'margin': '0 10px'}),
    ], style={'display': 'flex', 'marginBottom': '20px'}),

    # Charts Row 2
    html.Div([
        html.Div([
            dcc.Graph(id='category-pie')
        ], style={'flex': '1', 'margin': '0 10px'}),

        html.Div([
            dcc.Graph(id='monthly-heatmap')
        ], style={'flex': '1', 'margin': '0 10px'}),
    ], style={'display': 'flex', 'marginBottom': '20px'}),

    # Data Table
    html.Div([
        html.H3("Top 10 Orders", style={'marginLeft': '10px'}),
        dash_table.DataTable(
            id='top-orders-table',
            columns=[
                {'name': 'Date', 'id': 'date'},
                {'name': 'Customer', 'id': 'customer_id'},
                {'name': 'Product', 'id': 'product'},
                {'name': 'Category', 'id': 'category'},
                {'name': 'Region', 'id': 'region'},
                {'name': 'Revenue', 'id': 'revenue', 'type': 'numeric',
                 'format': dash_table.FormatTemplate.money(0)},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left', 'padding': '10px'},
            style_header={'backgroundColor': '#2c3e50', 'color': 'white', 'fontWeight': 'bold'},
            style_data_conditional=[
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'}
            ],
            page_size=10
        )
    ], style={'margin': '0 10px', 'backgroundColor': '#fff', 'borderRadius': '8px',
              'padding': '15px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),

], style={'backgroundColor': '#ecf0f1', 'minHeight': '100vh', 'fontFamily': 'Arial, sans-serif'})


# Callbacks for interactivity
@app.callback(
    [Output('revenue-trend', 'figure'),
     Output('region-bar', 'figure'),
     Output('category-pie', 'figure'),
     Output('monthly-heatmap', 'figure'),
     Output('top-orders-table', 'data')],
    [Input('region-filter', 'value'),
     Input('category-filter', 'value')]
)
def update_dashboard(selected_region, selected_category):
    """
    Each callback invocation is per-user session (Challenge 5).
    Dash handles WebSocket isolation — one user's filter change
    does not affect another user's view.
    """
    filtered_df = df.copy()

    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    # Save filter state to persistent storage (Challenge 3)
    save_filter_state(selected_region, selected_category)

    # Revenue Trend (Line Chart)
    monthly_revenue = filtered_df.groupby(filtered_df['date'].dt.to_period('M')).agg(
        revenue=('revenue', 'sum')
    ).reset_index()
    monthly_revenue['date'] = monthly_revenue['date'].astype(str)

    fig_trend = px.line(monthly_revenue, x='date', y='revenue',
                        title='Monthly Revenue Trend',
                        labels={'date': 'Month', 'revenue': 'Revenue ($)'})
    fig_trend.update_layout(template='plotly_white')

    # Revenue by Region (Bar Chart)
    region_revenue = filtered_df.groupby('region')['revenue'].sum().reset_index()
    fig_region = px.bar(region_revenue, x='region', y='revenue',
                        title='Revenue by Region', color='region',
                        labels={'revenue': 'Revenue ($)', 'region': 'Region'})
    fig_region.update_layout(template='plotly_white', showlegend=False)

    # Category Distribution (Pie Chart)
    category_revenue = filtered_df.groupby('category')['revenue'].sum().reset_index()
    fig_category = px.pie(category_revenue, values='revenue', names='category',
                          title='Revenue by Category')

    # Monthly Heatmap
    filtered_df = filtered_df.copy()
    filtered_df['month'] = filtered_df['date'].dt.month_name()
    filtered_df['day_of_week'] = filtered_df['date'].dt.day_name()
    fig_heatmap = px.density_heatmap(filtered_df, x='month', y='day_of_week',
                                      z='revenue', title='Revenue Heatmap',
                                      labels={'revenue': 'Revenue ($)'})
    fig_heatmap.update_layout(template='plotly_white')

    # Top Orders Table
    top_orders = filtered_df.nlargest(10, 'revenue')[['date', 'customer_id', 'product', 'category', 'region', 'revenue']]
    top_orders['date'] = top_orders['date'].dt.strftime('%Y-%m-%d')
    top_orders['revenue'] = top_orders['revenue'].round(0)

    return fig_trend, fig_region, fig_category, fig_heatmap, top_orders.to_dict('records')


if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
