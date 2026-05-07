"""
Visualization Module
OWID-style scientific data visualizations for COVID-19 analysis.
Minimal, clean, academic style with high information density.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Scientific color scales
COLOR_SCALES = {
    'cases': 'Reds',
    'deaths': 'Greys',
    'vaccinations': 'Blues',
    'testing': 'Purples',
    'default': 'YlOrRd'
}

# OWID-inspired minimal palette for line charts
LINE_COLORS = ['#2a4d8f', '#b91f1f', '#1a7a3a', '#d4a017', '#6b3fa0',
               '#c85a17', '#1a5b7a', '#8b4513', '#2d6a4f', '#9b2226']

# Base style - only font and background, no axis/hover conflicts
OWID_BASE = {
    'font': {'family': 'Arial, Helvetica, sans-serif', 'size': 12, 'color': '#333'},
    'plot_bgcolor': '#fafafa',
    'paper_bgcolor': '#ffffff',
}


def _apply_base(fig):
    """Apply base OWID style (font + background only)."""
    fig.update_layout(**OWID_BASE)
    return fig


def _apply_axes(fig):
    """Apply standard axis styling."""
    fig.update_xaxes(
        gridcolor='#e8e8e8', zerolinecolor='#ddd',
        tickfont={'size': 11}, showgrid=True
    )
    fig.update_yaxes(
        gridcolor='#e8e8e8', zerolinecolor='#ddd',
        tickfont={'size': 11}, showgrid=True
    )


def plot_choropleth_map(df, metric, date_str, title=None):
    """
    Create a choropleth map for a specific date.
    Scientific color scale, clean borders.
    """
    map_df = df[df['date'] == date_str].copy() if date_str else df
    
    # Determine color scale based on metric type
    if 'death' in metric.lower():
        color_scale = 'Greys'
    elif 'vaccin' in metric.lower():
        color_scale = 'Blues'
    elif 'case' in metric.lower():
        color_scale = 'Reds'
    else:
        color_scale = 'YlOrRd'
    
    fig = px.choropleth(
        map_df, locations='code', color=metric,
        hover_name='country',
        hover_data={
            'code': False,
            'continent': True,
            'population': ':,.0f',
            metric: ':,.0f'
        },
        color_continuous_scale=color_scale,
        range_color=[map_df[metric].quantile(0.05), map_df[metric].quantile(0.95)] 
                     if map_df[metric].notna().sum() > 10 else None,
        template='none'
    )
    
    fig.update_geos(
        projection_type='natural earth',
        showcountries=True, countrycolor='rgba(180,180,180,0.5)',
        showocean=True, oceancolor='#f0f2f5',
        showland=True, landcolor='#f5f5f5',
        showframe=False,
        lataxis_range=[-55, 75],
        lonaxis_range=[-170, 190],
        coastlinecolor='rgba(180,180,180,0.3)',
    )
    
    fig.update_layout(
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        coloraxis_colorbar={
            'title': {'text': metric.replace('_', ' ').title(), 'font': {'size': 10}},
            'tickformat': ',.0f',
            'len': 0.4,
            'thickness': 10,
            'x': 1.02,
            'yanchor': 'middle',
            'y': 0.5
        },
        hoverlabel={
            'bgcolor': 'white',
            'font_size': 13,
            'font_family': 'Arial',
            'bordercolor': '#ccc'
        },
        paper_bgcolor='#fafafa',
        geo={'bgcolor': '#fafafa'}
    )
    
    return fig


def plot_sparkline(series, height=30, width=120):
    """
    Create a small sparkline figure for tooltip display.
    Returns a Plotly figure optimized for small size.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index, y=series.values,
        mode='lines',
        line=dict(color='#2a4d8f', width=1.5),
        showlegend=False,
        hovertemplate='%{y:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        margin={'l': 0, 'r': 0, 't': 0, 'b': 0},
        height=height, width=width,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis={'visible': False, 'showgrid': False},
        yaxis={'visible': False, 'showgrid': False},
        showlegend=False
    )
    
    return fig


def plot_trend_line(df, countries, metric, title=None):
    """
    Clean line chart for trend visualization.
    Minimal style, high readability.
    """
    plot_df = df[df['country'].isin(countries)][['date', 'country', metric]].copy()
    plot_df = plot_df.dropna(subset=[metric])
    
    fig = px.line(
        plot_df, x='date', y=metric, color='country',
        title=title,
        color_discrete_sequence=LINE_COLORS,
        template='none'
    )
    
    fig.update_traces(
        line=dict(width=1.5),
        hovertemplate='%{x}<br>%{y:,.0f}<extra>%{fullData.name}</extra>'
    )
    
    _apply_base(fig)
    _apply_axes(fig)
    
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center', 
               'font': {'size': 14, 'color': '#222'}},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 
                'xanchor': 'right', 'x': 1, 'font': {'size': 10}},
        hovermode='x unified',
        hoverlabel={'bgcolor': 'white', 'font_size': 12, 'bordercolor': '#ccc'},
        margin={'l': 40, 'r': 20, 't': 40, 'b': 40}
    )
    
    return fig


def plot_bar_chart(df, x_col, y_col, title, color_col=None):
    """
    Clean horizontal bar chart for rankings.
    """
    plot_df = df.sort_values(y_col, ascending=True)
    
    fig = px.bar(
        plot_df, x=y_col, y=x_col, color=color_col,
        title=title, orientation='h',
        color_discrete_sequence=LINE_COLORS,
        template='none'
    )
    
    fig.update_traces(
        marker_line_color='rgba(0,0,0,0.05)',
        marker_line_width=0.5,
        hovertemplate='%{y}<br>%{x:,.0f}<extra></extra>'
    )
    
    _apply_base(fig)
    _apply_axes(fig)
    
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 14, 'color': '#222'}},
        xaxis={'tickformat': ',.0f', 'gridcolor': '#e8e8e8'},
        yaxis={'gridcolor': '#e8e8e8'},
        showlegend=False,
        hovermode='y unified',
        hoverlabel={'bgcolor': 'white', 'font_size': 12, 'bordercolor': '#ccc'},
        margin={'l': 120, 'r': 20, 't': 40, 'b': 40}
    )
    
    return fig


def plot_dual_axis(df, country, metric_left, metric_right):
    """
    Dual-axis chart comparing two metrics over time.
    """
    country_df = df[df['country'] == country].sort_values('date')
    
    fig = make_subplots(specs=[[{'secondary_y': True}]])
    
    fig.add_trace(
        go.Scatter(
            x=country_df['date'], y=country_df[metric_left],
            name=metric_left.replace('_', ' ').title(),
            line=dict(color=LINE_COLORS[0], width=1.5),
            hovertemplate='%{x}<br>%{y:,.0f}<extra></extra>'
        ),
        secondary_y=False
    )
    
    fig.add_trace(
        go.Scatter(
            x=country_df['date'], y=country_df[metric_right],
            name=metric_right.replace('_', ' ').title(),
            line=dict(color=LINE_COLORS[1], width=1.5),
            hovertemplate='%{x}<br>%{y:.1f}<extra></extra>'
        ),
        secondary_y=True
    )
    
    _apply_base(fig)
    _apply_axes(fig)
    
    fig.update_layout(
        title={'text': f'{country}', 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 14, 'color': '#222'}},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02,
                'xanchor': 'right', 'x': 1, 'font': {'size': 10}},
        hovermode='x unified',
        hoverlabel={'bgcolor': 'white', 'font_size': 12, 'bordercolor': '#ccc'},
        margin={'l': 40, 'r': 40, 't': 40, 'b': 40}
    )
    
    return fig


def plot_growth_rate(df, country, metric):
    """
    Two-panel chart: values + growth rate.
    """
    from src.data_analysis import growth_rate_analysis
    growth_df = growth_rate_analysis(df, country, metric).dropna()
    
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08,
        subplot_titles=('Daily Values', 'Daily Growth Rate (%)')
    )
    
    fig.add_trace(
        go.Scatter(
            x=growth_df['date'], y=growth_df[metric],
            line=dict(color=LINE_COLORS[0], width=1.5),
            showlegend=False,
            hovertemplate='%{x}<br>%{y:,.0f}<extra></extra>'
        ),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(
            x=growth_df['date'], y=growth_df['growth_rate'],
            marker_color=LINE_COLORS[1],
            showlegend=False,
            hovertemplate='%{x}<br>%{y:.1f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    _apply_base(fig)
    _apply_axes(fig)
    
    fig.update_layout(
        title={'text': f'{country}: Growth Analysis', 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 14, 'color': '#222'}},
        hovermode='x unified',
        hoverlabel={'bgcolor': 'white', 'font_size': 12, 'bordercolor': '#ccc'},
        height=400,
        margin={'l': 40, 'r': 20, 't': 40, 'b': 40}
    )
    
    return fig


def plot_scatter(df, x_col, y_col, color_col=None, title=None):
    """
    Scientific scatter plot for relationship analysis.
    """
    fig = px.scatter(
        df, x=x_col, y=y_col, color=color_col,
        hover_name='country',
        title=title,
        color_discrete_sequence=LINE_COLORS,
        template='none',
        size_max=12
    )
    
    fig.update_traces(
        marker=dict(
            line=dict(width=0.5, color='rgba(0,0,0,0.2)'),
            size=8
        ),
        hovertemplate='%{x:,.0f}<br>%{y:,.0f}<extra>%{hovertext}</extra>'
    )
    
    _apply_base(fig)
    _apply_axes(fig)
    
    fig.update_layout(
        title={'text': title, 'x': 0.5, 'xanchor': 'center',
               'font': {'size': 14, 'color': '#222'}},
        hovermode='closest',
        hoverlabel={'bgcolor': 'white', 'font_size': 12, 'bordercolor': '#ccc'},
        margin={'l': 50, 'r': 20, 't': 40, 'b': 50}
    )
    
    return fig
