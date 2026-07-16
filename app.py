import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data import generate_sales_data

# Generate sample data
df = generate_sales_data()

# Initialize Dash app
app = dash.Dash(__name__)

# KPI calculations
total_revenue = df['revenue'].sum()
total_orders = len(df)
avg_order_value = df['revenue'].mean()
total_customers = df['customer_id'].nunique()

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Sales Analytics Dashboard", style={'color': '#ffffff', 'marginBottom': '5px'}),
        html.P("Interactive Sales Performance Monitor", style={'color': '#cccccc'})
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
                value='All',
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'margin': '0 10px'}),

        html.Div([
            html.Label("Select Category:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='category-filter',
                options=[{'label': 'All Categories', 'value': 'All'}] +
                        [{'label': c, 'value': c} for c in df['category'].unique()],
                value='All',
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
    filtered_df = df.copy()

    if selected_region != 'All':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

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
    filtered_df['month'] = filtered_df['date'].dt.month_name()
    filtered_df['day_of_week'] = filtered_df['date'].dt.day_name()
    heatmap_data = filtered_df.groupby(['day_of_week', 'month'])['revenue'].sum().reset_index()
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
    app.run(host='0.0.0.0', port=8888, debug=False)
