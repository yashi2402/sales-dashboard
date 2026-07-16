import os
import json
import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from data import generate_sales_data

# =============================================================================
# CHALLENGE 1: Environment variables — no hardcoded paths
# =============================================================================
APP_HOST = os.environ.get('APP_HOST', '0.0.0.0')
APP_PORT = int(os.environ.get('APP_PORT', '8888'))
DATA_RECORDS = int(os.environ.get('DATA_RECORDS', '2500'))
PERSISTENT_STORAGE_PATH = os.environ.get('DOMINO_DATASET_PATH', '/mnt/data/sales-dashboard')
DB_CONNECTION_STRING = os.environ.get('DB_CONNECTION_STRING', '')

# =============================================================================
# CHALLENGE 3: Persistent storage
# =============================================================================
CACHE_FILE = os.path.join(PERSISTENT_STORAGE_PATH, 'sales_data_cache.csv')


def load_data():
    """Load from persistent cache or generate fresh data."""
    if os.path.exists(CACHE_FILE):
        return pd.read_csv(CACHE_FILE, parse_dates=['date'])
    df = generate_sales_data(n_records=DATA_RECORDS)
    if os.path.exists(PERSISTENT_STORAGE_PATH):
        df.to_csv(CACHE_FILE, index=False)
    return df


df = load_data()

# =============================================================================
# CHALLENGE 5: Session management & WebSocket handling
# =============================================================================
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    update_title=None,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}]
)
server = app.server

# Color theme
COLORS = {
    'primary': '#1a1a2e',
    'secondary': '#16213e',
    'accent': '#0f3460',
    'highlight': '#e94560',
    'success': '#00b894',
    'warning': '#fdcb6e',
    'info': '#74b9ff',
    'purple': '#a29bfe',
    'bg': '#f8f9fa',
    'card_bg': '#ffffff',
    'text': '#2d3436',
    'text_light': '#636e72',
}

# Calculate KPIs
total_revenue = df['revenue'].sum()
total_profit = df['profit'].sum()
total_orders = len(df)
avg_order_value = df['revenue'].mean()
total_customers = df['customer_id'].nunique()
avg_satisfaction = df['satisfaction'].mean()


def create_kpi_card(title, value, icon, color, trend=None):
    """Create a styled KPI card."""
    trend_element = html.Div()
    if trend:
        arrow = "+" if trend > 0 else ""
        trend_color = COLORS['success'] if trend > 0 else COLORS['highlight']
        trend_element = html.P(
            f"{arrow}{trend:.1f}% vs last period",
            style={'color': trend_color, 'fontSize': '12px', 'margin': '5px 0 0 0'}
        )

    return html.Div([
        html.Div([
            html.Div(icon, style={
                'fontSize': '28px', 'marginBottom': '8px'
            }),
            html.P(title, style={
                'color': COLORS['text_light'], 'fontSize': '13px',
                'margin': '0', 'textTransform': 'uppercase', 'letterSpacing': '1px'
            }),
            html.H3(value, style={
                'color': COLORS['text'], 'margin': '8px 0 0 0',
                'fontSize': '24px', 'fontWeight': '700'
            }),
            trend_element
        ], style={'padding': '24px', 'textAlign': 'center'})
    ], style={
        'backgroundColor': COLORS['card_bg'],
        'borderRadius': '12px',
        'boxShadow': '0 4px 6px rgba(0,0,0,0.07)',
        'flex': '1',
        'margin': '0 8px',
        'borderTop': f'4px solid {color}',
        'transition': 'transform 0.2s',
    })


# App layout
app.layout = html.Div([
    # Session store for multi-user support (Challenge 5)
    dcc.Store(id='session-store', storage_type='session'),
    dcc.Interval(id='refresh-interval', interval=300000, n_intervals=0),  # Auto-refresh every 5 min

    # Header
    html.Div([
        html.Div([
            html.Div([
                html.H1("Sales Analytics", style={
                    'color': '#ffffff', 'margin': '0', 'fontSize': '28px', 'fontWeight': '700'
                }),
                html.P("Real-time Business Intelligence Dashboard", style={
                    'color': 'rgba(255,255,255,0.7)', 'margin': '4px 0 0 0', 'fontSize': '14px'
                })
            ]),
            html.Div([
                html.P(f"Last updated: {pd.Timestamp.now().strftime('%d %b %Y, %H:%M')}",
                       style={'color': 'rgba(255,255,255,0.6)', 'fontSize': '12px', 'margin': '0'}),
                html.P(f"{total_orders:,} orders | {total_customers} customers",
                       style={'color': 'rgba(255,255,255,0.6)', 'fontSize': '12px', 'margin': '4px 0 0 0'})
            ], style={'textAlign': 'right'})
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                  'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 20px'})
    ], style={
        'background': f'linear-gradient(135deg, {COLORS["primary"]}, {COLORS["accent"]})',
        'padding': '24px 0',
        'marginBottom': '24px',
        'boxShadow': '0 4px 12px rgba(0,0,0,0.15)'
    }),

    # Main content container
    html.Div([
        # KPI Cards Row
        html.Div([
            create_kpi_card("Total Revenue", f"${total_revenue:,.0f}", "💰", COLORS['success'], trend=12.5),
            create_kpi_card("Total Profit", f"${total_profit:,.0f}", "📈", COLORS['info'], trend=8.3),
            create_kpi_card("Avg Order Value", f"${avg_order_value:,.0f}", "🛒", COLORS['warning'], trend=3.2),
            create_kpi_card("Satisfaction", f"{avg_satisfaction:.1f}/5.0", "⭐", COLORS['purple'], trend=2.1),
        ], style={'display': 'flex', 'marginBottom': '24px'}),

        # Filters Row
        html.Div([
            html.Div([
                html.Label("Region", style={
                    'fontWeight': '600', 'fontSize': '13px', 'color': COLORS['text_light'],
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'marginBottom': '6px', 'display': 'block'
                }),
                dcc.Dropdown(
                    id='region-filter',
                    options=[{'label': 'All Regions', 'value': 'All'}] +
                            [{'label': r, 'value': r} for r in sorted(df['region'].unique())],
                    value='All',
                    clearable=False,
                    style={'borderRadius': '8px'}
                )
            ], style={'flex': '1', 'margin': '0 8px'}),

            html.Div([
                html.Label("Category", style={
                    'fontWeight': '600', 'fontSize': '13px', 'color': COLORS['text_light'],
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'marginBottom': '6px', 'display': 'block'
                }),
                dcc.Dropdown(
                    id='category-filter',
                    options=[{'label': 'All Categories', 'value': 'All'}] +
                            [{'label': c, 'value': c} for c in sorted(df['category'].unique())],
                    value='All',
                    clearable=False,
                    style={'borderRadius': '8px'}
                )
            ], style={'flex': '1', 'margin': '0 8px'}),

            html.Div([
                html.Label("Channel", style={
                    'fontWeight': '600', 'fontSize': '13px', 'color': COLORS['text_light'],
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'marginBottom': '6px', 'display': 'block'
                }),
                dcc.Dropdown(
                    id='channel-filter',
                    options=[{'label': 'All Channels', 'value': 'All'}] +
                            [{'label': c, 'value': c} for c in sorted(df['channel'].unique())],
                    value='All',
                    clearable=False,
                    style={'borderRadius': '8px'}
                )
            ], style={'flex': '1', 'margin': '0 8px'}),

            html.Div([
                html.Label("Customer Segment", style={
                    'fontWeight': '600', 'fontSize': '13px', 'color': COLORS['text_light'],
                    'textTransform': 'uppercase', 'letterSpacing': '1px', 'marginBottom': '6px', 'display': 'block'
                }),
                dcc.Dropdown(
                    id='segment-filter',
                    options=[{'label': 'All Segments', 'value': 'All'}] +
                            [{'label': s, 'value': s} for s in sorted(df['customer_segment'].unique())],
                    value='All',
                    clearable=False,
                    style={'borderRadius': '8px'}
                )
            ], style={'flex': '1', 'margin': '0 8px'}),
        ], style={
            'display': 'flex', 'marginBottom': '24px', 'padding': '20px',
            'backgroundColor': COLORS['card_bg'], 'borderRadius': '12px',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
        }),

        # Charts Row 1 — Revenue Trend + Region Performance
        html.Div([
            html.Div([
                dcc.Graph(id='revenue-trend', config={'displayModeBar': False})
            ], style={
                'flex': '2', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
            html.Div([
                dcc.Graph(id='region-bar', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
        ], style={'display': 'flex', 'marginBottom': '24px'}),

        # Charts Row 2 — Category + Channel + Satisfaction
        html.Div([
            html.Div([
                dcc.Graph(id='category-pie', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
            html.Div([
                dcc.Graph(id='channel-chart', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
            html.Div([
                dcc.Graph(id='profit-margin-chart', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
        ], style={'display': 'flex', 'marginBottom': '24px'}),

        # Charts Row 3 — Heatmap + Top Products
        html.Div([
            html.Div([
                dcc.Graph(id='monthly-heatmap', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
            html.Div([
                dcc.Graph(id='top-products-chart', config={'displayModeBar': False})
            ], style={
                'flex': '1', 'margin': '0 8px', 'backgroundColor': COLORS['card_bg'],
                'borderRadius': '12px', 'padding': '16px',
                'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
            }),
        ], style={'display': 'flex', 'marginBottom': '24px'}),

        # Data Table
        html.Div([
            html.Div([
                html.H3("Recent Orders", style={
                    'margin': '0', 'color': COLORS['text'], 'fontWeight': '600'
                }),
                html.P("Latest transactions with details", style={
                    'margin': '4px 0 0 0', 'color': COLORS['text_light'], 'fontSize': '13px'
                })
            ], style={'marginBottom': '16px'}),
            dash_table.DataTable(
                id='top-orders-table',
                columns=[
                    {'name': 'Order ID', 'id': 'order_id'},
                    {'name': 'Date', 'id': 'date'},
                    {'name': 'Product', 'id': 'product'},
                    {'name': 'Category', 'id': 'category'},
                    {'name': 'Region', 'id': 'region'},
                    {'name': 'Channel', 'id': 'channel'},
                    {'name': 'Qty', 'id': 'quantity'},
                    {'name': 'Revenue', 'id': 'revenue', 'type': 'numeric',
                     'format': dash_table.FormatTemplate.money(0)},
                    {'name': 'Profit', 'id': 'profit', 'type': 'numeric',
                     'format': dash_table.FormatTemplate.money(0)},
                    {'name': 'Rating', 'id': 'satisfaction'},
                ],
                style_table={'overflowX': 'auto', 'borderRadius': '8px'},
                style_cell={
                    'textAlign': 'left', 'padding': '12px 16px',
                    'fontSize': '13px', 'fontFamily': 'Inter, sans-serif'
                },
                style_header={
                    'backgroundColor': COLORS['primary'], 'color': 'white',
                    'fontWeight': '600', 'fontSize': '12px',
                    'textTransform': 'uppercase', 'letterSpacing': '0.5px'
                },
                style_data_conditional=[
                    {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8f9fa'},
                    {'if': {'state': 'active'}, 'backgroundColor': '#e3f2fd', 'border': '1px solid #90caf9'},
                ],
                page_size=15,
                sort_action='native',
                filter_action='native',
            )
        ], style={
            'backgroundColor': COLORS['card_bg'], 'borderRadius': '12px',
            'padding': '24px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
            'marginBottom': '24px'
        }),

        # Footer
        html.Div([
            html.P("Sales Analytics Dashboard | Domino Use Case 7 | Built with Dash & Plotly",
                   style={'color': COLORS['text_light'], 'fontSize': '12px', 'textAlign': 'center'})
        ], style={'padding': '16px'})

    ], style={'maxWidth': '1400px', 'margin': '0 auto', 'padding': '0 16px'}),

], style={'backgroundColor': COLORS['bg'], 'minHeight': '100vh', 'fontFamily': 'Inter, -apple-system, sans-serif'})


# =============================================================================
# Callbacks — each user gets independent state (Challenge 5)
# =============================================================================
@app.callback(
    [Output('revenue-trend', 'figure'),
     Output('region-bar', 'figure'),
     Output('category-pie', 'figure'),
     Output('channel-chart', 'figure'),
     Output('profit-margin-chart', 'figure'),
     Output('monthly-heatmap', 'figure'),
     Output('top-products-chart', 'figure'),
     Output('top-orders-table', 'data')],
    [Input('region-filter', 'value'),
     Input('category-filter', 'value'),
     Input('channel-filter', 'value'),
     Input('segment-filter', 'value')]
)
def update_dashboard(selected_region, selected_category, selected_channel, selected_segment):
    # Base filter (region + segment only) — for category/channel charts to show all options
    base_df = df.copy()
    if selected_region != 'All':
        base_df = base_df[base_df['region'] == selected_region]
    if selected_segment != 'All':
        base_df = base_df[base_df['customer_segment'] == selected_segment]

    # Fully filtered (all 4 filters) — for trend, table, heatmap, products
    filtered_df = base_df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if selected_channel != 'All':
        filtered_df = filtered_df[filtered_df['channel'] == selected_channel]

    # 1. Revenue & Profit Trend (Area Chart) — uses full filter
    monthly = filtered_df.groupby(filtered_df['date'].dt.to_period('M')).agg(
        revenue=('revenue', 'sum'),
        profit=('profit', 'sum')
    ).reset_index()
    monthly['date'] = monthly['date'].astype(str)

    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=monthly['date'], y=monthly['revenue'], name='Revenue',
        fill='tozeroy', line=dict(color=COLORS['info'], width=2),
        fillcolor='rgba(116, 185, 255, 0.1)'
    ))
    fig_trend.add_trace(go.Scatter(
        x=monthly['date'], y=monthly['profit'], name='Profit',
        fill='tozeroy', line=dict(color=COLORS['success'], width=2),
        fillcolor='rgba(0, 184, 148, 0.1)'
    ))
    fig_trend.update_layout(
        title={'text': 'Revenue & Profit Trend', 'font': {'size': 16, 'color': COLORS['text']}},
        template='plotly_white', margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        height=350
    )

    # 2. Revenue by Region — always shows ALL regions (highlights selected)
    region_source = df.copy()
    if selected_category != 'All':
        region_source = region_source[region_source['category'] == selected_category]
    if selected_channel != 'All':
        region_source = region_source[region_source['channel'] == selected_channel]
    if selected_segment != 'All':
        region_source = region_source[region_source['customer_segment'] == selected_segment]
    region_data = region_source.groupby('region')['revenue'].sum().reset_index().sort_values('revenue', ascending=True)
    bar_colors = [COLORS['highlight'] if r == selected_region else COLORS['info'] for r in region_data['region']]

    fig_region = go.Figure(go.Bar(
        x=region_data['revenue'], y=region_data['region'],
        orientation='h', marker_color=bar_colors,
        text=[f'${v:,.0f}' for v in region_data['revenue']],
        textposition='inside'
    ))
    fig_region.update_layout(
        title={'text': 'Revenue by Region', 'font': {'size': 16, 'color': COLORS['text']}},
        template='plotly_white', margin=dict(l=20, r=20, t=50, b=20),
        height=350, showlegend=False
    )

    # 3. Category Distribution — always shows ALL categories (highlights selected)
    cat_source = df.copy()
    if selected_region != 'All':
        cat_source = cat_source[cat_source['region'] == selected_region]
    if selected_channel != 'All':
        cat_source = cat_source[cat_source['channel'] == selected_channel]
    if selected_segment != 'All':
        cat_source = cat_source[cat_source['customer_segment'] == selected_segment]
    cat_data = cat_source.groupby('category')['revenue'].sum().reset_index()

    pull_values = [0.1 if c == selected_category else 0 for c in cat_data['category']]
    fig_category = px.pie(cat_data, values='revenue', names='category',
                          hole=0.5, color_discrete_sequence=px.colors.qualitative.Set2)
    fig_category.update_traces(pull=pull_values, textposition='inside', textinfo='percent')
    fig_category.update_layout(
        title={'text': 'By Category', 'font': {'size': 16, 'color': COLORS['text']}},
        margin=dict(l=20, r=20, t=50, b=20), height=350,
        legend=dict(orientation='h', yanchor='top', y=-0.1, xanchor='center', x=0.5)
    )

    # 4. Channel Performance — always shows ALL channels (highlights selected)
    ch_source = df.copy()
    if selected_region != 'All':
        ch_source = ch_source[ch_source['region'] == selected_region]
    if selected_category != 'All':
        ch_source = ch_source[ch_source['category'] == selected_category]
    if selected_segment != 'All':
        ch_source = ch_source[ch_source['customer_segment'] == selected_segment]
    channel_data = ch_source.groupby('channel')['revenue'].sum().reset_index().sort_values('revenue', ascending=False)
    ch_colors = [COLORS['highlight'] if c == selected_channel else COLORS['info'] for c in channel_data['channel']]

    fig_channel = go.Figure(go.Bar(
        x=channel_data['channel'], y=channel_data['revenue'],
        marker_color=ch_colors,
        text=[f'${v:,.0f}' for v in channel_data['revenue']],
        textposition='outside'
    ))
    fig_channel.update_layout(
        title={'text': 'By Channel', 'font': {'size': 16, 'color': COLORS['text']}},
        template='plotly_white', margin=dict(l=20, r=20, t=50, b=60),
        height=300, showlegend=False
    )

    # 5. Profit Margin by Category — always shows ALL categories
    margin_data = cat_source.groupby('category')['margin_pct'].mean().reset_index().sort_values('margin_pct', ascending=True)
    colors = [COLORS['highlight'] if m < 30 else COLORS['warning'] if m < 40 else COLORS['success']
              for m in margin_data['margin_pct']]
    fig_margin = go.Figure(go.Bar(
        x=margin_data['margin_pct'], y=margin_data['category'],
        orientation='h', marker_color=colors,
        text=[f'{v:.1f}%' for v in margin_data['margin_pct']],
        textposition='inside'
    ))
    fig_margin.update_layout(
        title={'text': 'Profit Margin %', 'font': {'size': 16, 'color': COLORS['text']}},
        template='plotly_white', margin=dict(l=20, r=20, t=50, b=20),
        height=300, xaxis=dict(range=[0, 60])
    )

    # 6. Revenue Heatmap (Day of Week x Month)
    heatmap_df = filtered_df.copy()
    heatmap_df['month'] = heatmap_df['date'].dt.month_name().str[:3]
    heatmap_df['day_of_week'] = heatmap_df['date'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_pivot = heatmap_df.pivot_table(values='revenue', index='day_of_week', columns='month', aggfunc='sum')
    month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    heatmap_pivot = heatmap_pivot.reindex(columns=[m for m in month_order if m in heatmap_pivot.columns])
    heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])

    fig_heatmap = px.imshow(heatmap_pivot, color_continuous_scale='YlOrRd', aspect='auto')
    fig_heatmap.update_layout(
        title={'text': 'Revenue Heatmap (Day x Month)', 'font': {'size': 16, 'color': COLORS['text']}},
        margin=dict(l=20, r=20, t=50, b=20), height=350
    )

    # 7. Top Products by Revenue
    top_products = filtered_df.groupby('product')['revenue'].sum().reset_index().nlargest(10, 'revenue').sort_values('revenue', ascending=True)
    fig_products = go.Figure(go.Bar(
        x=top_products['revenue'], y=top_products['product'],
        orientation='h', marker_color=COLORS['purple'],
        text=[f'${v:,.0f}' for v in top_products['revenue']],
        textposition='inside'
    ))
    fig_products.update_layout(
        title={'text': 'Top 10 Products', 'font': {'size': 16, 'color': COLORS['text']}},
        template='plotly_white', margin=dict(l=20, r=20, t=50, b=20),
        height=350
    )

    # 8. Table Data (latest orders)
    table_data = filtered_df.nlargest(50, 'date')[
        ['order_id', 'date', 'product', 'category', 'region', 'channel', 'quantity', 'revenue', 'profit', 'satisfaction']
    ].copy()
    table_data['date'] = table_data['date'].dt.strftime('%Y-%m-%d')
    table_data['revenue'] = table_data['revenue'].round(0)
    table_data['profit'] = table_data['profit'].round(0)

    return (fig_trend, fig_region, fig_category, fig_channel, fig_margin,
            fig_heatmap, fig_products, table_data.to_dict('records'))


if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=False)
