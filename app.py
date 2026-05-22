"""
COVID-19 Data Analysis Platform
Multi-tab layout with OWID-style scientific visualizations.
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from src.data_loader import (
    load_data, get_countries, get_continents, get_date_range,
    get_numeric_columns
)
from src.data_cleaner import (
    clean_data, handle_missing_values, filter_by_date,
    filter_by_country, CovidDataPreprocessor
)
from src.data_analysis import (
    global_trend, country_trend, compare_countries,
    top_countries, descriptive_stats
)
from src.visualization import (
    plot_choropleth_map, plot_trend_line, plot_bar_chart,
    plot_dual_axis, plot_growth_rate, plot_scatter
)

# ============================================================================
# Data Loading (with cache) - done before app starts
# ============================================================================
import os
import pickle
import time

DATA_PATH = 'compact.csv'
CACHE_PATH = 'data_cache.pkl'

print("Loading data...", end=' ', flush=True)
t0 = time.time()

if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, 'rb') as f:
        df_raw, df = pickle.load(f)
else:
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(
            f"Required dataset '{DATA_PATH}' was not found. "
            "Add compact.csv to the project root before starting the app; "
            "data_cache.pkl is optional and can be regenerated from compact.csv."
        )
    # Use the team member's CovidDataPreprocessor for cleaning
    print("Running full preprocessing pipeline...")
    processor = CovidDataPreprocessor(DATA_PATH)
    df_raw = processor.load_data()
    processor.clean_data()
    # Keep ALL columns (pass variables=None)
    df = processor.prepare_for_analysis(variables=None)
    # Apply missing value handling (ffill within each country)
    df = handle_missing_values(df, strategy='ffill')
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump((df_raw, df), f)

countries = get_countries(df)
continents = get_continents(df)
date_min, date_max = get_date_range(df)
numeric_cols = get_numeric_columns(df)

all_dates = sorted(df['date'].dt.strftime('%Y-%m-%d').unique())

# For timeline: use monthly sampling to reduce slider lag
MONTHLY_DATES = all_dates[::30]
if all_dates[-1] not in MONTHLY_DATES:
    MONTHLY_DATES.append(all_dates[-1])

# Pre-sort index for fast date filtering
df_sorted = df.sort_values('date').reset_index(drop=True)
date_values = df_sorted['date'].values

print(f"done ({time.time()-t0:.1f}s)")
print(f"Data: {len(df):,} rows, {len(countries)} countries, {date_min.date()} to {date_max.date()}")

# Metric definitions
METRICS = [
    {'id': 'new_cases_smoothed', 'label': 'Daily New Cases', 'group': 'Cases'},
    {'id': 'new_deaths_smoothed', 'label': 'Daily New Deaths', 'group': 'Deaths'},
    {'id': 'new_cases_smoothed_per_million', 'label': 'New Cases per Million', 'group': 'Cases'},
    {'id': 'new_deaths_smoothed_per_million', 'label': 'New Deaths per Million', 'group': 'Deaths'},
    {'id': 'total_cases_per_million', 'label': 'Total Cases per Million', 'group': 'Cases'},
    {'id': 'total_deaths_per_million', 'label': 'Total Deaths per Million', 'group': 'Deaths'},
    {'id': 'people_fully_vaccinated_per_hundred', 'label': 'Fully Vaccinated (%)', 'group': 'Vaccination'},
    {'id': 'people_vaccinated_per_hundred', 'label': 'Vaccinated (%)', 'group': 'Vaccination'},
    {'id': 'total_boosters_per_hundred', 'label': 'Boosters (%)', 'group': 'Vaccination'},
    {'id': 'positive_rate', 'label': 'Positive Test Rate', 'group': 'Testing'},
    {'id': 'stringency_index', 'label': 'Stringency Index', 'group': 'Policy'},
    {'id': 'reproduction_rate', 'label': 'Reproduction Rate', 'group': 'Epidemiology'},
]

DEFAULT_METRIC = 'new_cases_smoothed'
DEFAULT_COUNTRIES = ['United States', 'United Kingdom', 'India', 'Brazil', 'Germany']

print(f"Data loaded: {len(df):,} rows, {len(countries)} countries")
print(f"Date range: {date_min.date()} to {date_max.date()}")

# Pre-compute pipeline tab data (avoids recomputation on every tab switch)
from src.data_cleaner import get_cleaning_summary
PIPELINE_SUMMARY = get_cleaning_summary(df_raw, df)
PIPELINE_COLS_INFO = []
for col in df.columns:
    sample = df[col].dropna().iloc[:3].tolist()
    PIPELINE_COLS_INFO.append({
        'name': col,
        'dtype': str(df[col].dtype),
        'non_null': int(df[col].notna().sum()),
        'null_count': int(df[col].isna().sum()),
        'sample_values': sample
    })
print(f"Pipeline data pre-computed: {len(PIPELINE_COLS_INFO)} columns")

# ============================================================================
# App Initialization
# ============================================================================
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title='COVID-19 Data Explorer'
)

# Remove Plotly logo from all graphs
PLOTLY_CONFIG = {'displayModeBar': True, 'displaylogo': False, 
                 'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d',
                                            'autoScale2d', 'toggleSpikelines',
                                            'hoverClosestCartesian', 'hoverCompareCartesian',
                                            'zoomIn2d', 'zoomOut2d']}

server = app.server

# ============================================================================
# Tab Definitions
# ============================================================================
TABS = [
    {'label': 'Data Pipeline', 'value': 'tab-pipeline'},
    {'label': 'Overview', 'value': 'tab-overview'},
    {'label': 'Global Trends', 'value': 'tab-global'},
    {'label': 'Country Comparison', 'value': 'tab-compare'},
    {'label': 'Country Deep Dive', 'value': 'tab-deepdive'},
    {'label': 'Rankings', 'value': 'tab-rankings'},
    {'label': 'Correlation', 'value': 'tab-correlation'},
    {'label': 'Continent Analysis', 'value': 'tab-continent'},
]

# ============================================================================
# Layout
# ============================================================================
app.layout = html.Div([
    # Header
    html.Div([
        html.Div([
            html.Span('COVID-19 Data Explorer', 
                     style={'fontSize': '20px', 'fontWeight': '700', 'color': '#222'}),
            html.Span('  |  Our World in Data', 
                     style={'fontSize': '13px', 'color': '#888', 'marginLeft': '8px'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Button('Exit', id='exit-btn', n_clicks=0,
                   style={'padding': '6px 20px', 'background': '#fff',
                          'border': '1px solid #ccc', 'borderRadius': '3px',
                          'cursor': 'pointer', 'fontSize': '12px', 'color': '#666'})
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
              'padding': '12px 24px', 'borderBottom': '1px solid #e8e8e8', 
              'background': '#fff'}),
    
    # Global controls
    html.Div([
        html.Div([
            html.Span('Metric:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(
                id='global-metric',
                options=[{'label': m['label'], 'value': m['id']} for m in METRICS],
                value=DEFAULT_METRIC, clearable=False,
                style={'width': '260px', 'fontSize': '13px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Span('Country:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(
                id='global-country',
                options=[{'label': c, 'value': c} for c in countries],
                value=DEFAULT_COUNTRIES[0], clearable=False,
                style={'width': '180px', 'fontSize': '13px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Span('Compare:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(
                id='global-compare',
                options=[{'label': c, 'value': c} for c in countries],
                value=DEFAULT_COUNTRIES[1:4], multi=True,
                style={'width': '260px', 'fontSize': '13px'}
            )
        ], style={'display': 'flex', 'alignItems': 'center'})
    ], style={'display': 'flex', 'gap': '16px', 'padding': '8px 24px',
              'background': '#fafafa', 'borderBottom': '1px solid #e8e8e8',
              'flexWrap': 'wrap'}),
    
    # Tabs
    dcc.Tabs(
        id='main-tabs',
        value='tab-overview',
        children=[dcc.Tab(label=t['label'], value=t['value']) for t in TABS],
        style={'fontSize': '13px', 'fontWeight': '500'}
    ),
    
    # Tab content
    html.Div(id='tab-content', style={'padding': '16px 24px', 'background': '#f5f5f5',
                                       'minHeight': 'calc(100vh - 180px)'}),
    
    # Footer
    html.Div([
        html.Hr(style={'margin': '0'}),
        html.Div('Data: Our World in Data | COVID-19 Data Explorer',
                style={'textAlign': 'center', 'padding': '12px', 'fontSize': '11px', 
                       'color': '#999', 'background': '#fafafa'})
    ])
], style={'fontFamily': 'Arial, Helvetica, sans-serif', 'background': '#f5f5f5',
          'minHeight': '100vh'})


# ============================================================================
# Callbacks
# ============================================================================

@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def render_tab(tab, metric, country, compare_list):
    if tab == 'tab-pipeline':
        return build_pipeline_tab()
    elif tab == 'tab-overview':
        return build_overview_tab(metric)
    elif tab == 'tab-global':
        return build_global_tab(metric)
    elif tab == 'tab-compare':
        return build_compare_tab(metric, country, compare_list)
    elif tab == 'tab-deepdive':
        return build_deepdive_tab(metric, country)
    elif tab == 'tab-rankings':
        return build_rankings_tab(metric)
    elif tab == 'tab-correlation':
        return build_correlation_tab(metric)
    elif tab == 'tab-continent':
        return build_continent_tab(metric)
    return html.Div()


# ============================================================================
# Tab Builders
# ============================================================================

def build_pipeline_tab():
    """Data Pipeline tab: shows data loading and cleaning steps."""
    # Use pre-computed data (computed once at startup)
    summary = PIPELINE_SUMMARY
    cols_info = PIPELINE_COLS_INFO
    
    return html.Div([
        # Step 1: Data Loading
        html.Div([
            html.Div([
                html.Span('Step 1', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#1a76d2', 'padding': '2px 8px',
                         'borderRadius': '10px', 'marginRight': '8px'}),
                html.Span('Data Loading', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px',
                      'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
            html.Div([
                html.Div([
                    html.Div('Source File', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div('compact.csv', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Div('Total Rows Loaded', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{len(df_raw):,}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Div('Total Columns', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{len(df_raw.columns)}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Div('Date Range', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{date_min.date()} to {date_max.date()}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222'})
                ], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'})
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '12px'}),
        
        # Step 2: Data Cleaning
        html.Div([
            html.Div([
                html.Span('Step 2', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#28a745', 'padding': '2px 8px',
                         'borderRadius': '10px', 'marginRight': '8px'}),
                html.Span('Data Cleaning', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px',
                      'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
            html.Div([
                html.Div([
                    html.Div('Cleaning Actions', style={'fontSize': '11px', 'color': '#888', 'marginBottom': '8px'}),
                    html.Ul([
                        html.Li(f'Removed {summary["duplicates_removed"]:,} duplicate rows'),
                        html.Li('Sorted by country and date'),
                        html.Li('Forward-filled missing values within each country'),
                        html.Li('Backward-filled remaining NaNs at start of series'),
                    ], style={'fontSize': '13px', 'color': '#444', 'margin': '0', 'paddingLeft': '20px'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Div('Cleaning Results', style={'fontSize': '11px', 'color': '#888', 'marginBottom': '8px'}),
                    html.Div([
                        html.Div([
                            html.Div('Rows Before', style={'fontSize': '11px', 'color': '#888'}),
                            html.Div(f'{summary["original_rows"]:,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#222'})
                        ], style={'textAlign': 'center', 'padding': '8px'}),
                        html.Div([
                            html.Div('Rows After', style={'fontSize': '11px', 'color': '#888'}),
                            html.Div(f'{summary["cleaned_rows"]:,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#222'})
                        ], style={'textAlign': 'center', 'padding': '8px'}),
                        html.Div([
                            html.Div('Missing Values (before)', style={'fontSize': '11px', 'color': '#888'}),
                            html.Div(f'{summary["missing_before"]:,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#d9534f'})
                        ], style={'textAlign': 'center', 'padding': '8px'}),
                        html.Div([
                            html.Div('Missing Values (after)', style={'fontSize': '11px', 'color': '#888'}),
                            html.Div(f'{summary["missing_after"]:,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#28a745'})
                        ], style={'textAlign': 'center', 'padding': '8px'}),
                    ], style={'display': 'flex', 'gap': '8px'})
                ], style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '24px', 'flexWrap': 'wrap'})
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '12px'}),
        
        # Step 3: Column Overview
        html.Div([
            html.Div([
                html.Span('Step 3', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#ffc107', 'padding': '2px 8px',
                         'borderRadius': '10px', 'marginRight': '8px'}),
                html.Span('Column Overview', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333'})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px',
                      'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
            html.Div([
                dash_table.DataTable(
                    columns=[
                        {'name': 'Column', 'id': 'name'},
                        {'name': 'Type', 'id': 'dtype'},
                        {'name': 'Non-Null Count', 'id': 'non_null'},
                        {'name': 'Null Count', 'id': 'null_count'},
                        {'name': 'Sample Values', 'id': 'sample_values'},
                    ],
                    data=[{
                        'name': c['name'],
                        'dtype': c['dtype'],
                        'non_null': f'{c["non_null"]:,}',
                        'null_count': f'{c["null_count"]:,}',
                        'sample_values': ', '.join(str(v) for v in c['sample_values'])
                    } for c in cols_info],
                    page_size=15,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'fontSize': '12px', 'fontFamily': 'Arial',
                        'padding': '6px 12px', 'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#fafafa', 'fontWeight': '600',
                        'borderBottom': '1px solid #e8e8e8'
                    },
                    style_data={'borderBottom': '1px solid #f0f0f0'},
                    style_cell_conditional=[
                        {'if': {'column_id': 'null_count'}, 'color': '#d9534f' if any(c['null_count'] > 0 for c in cols_info) else '#28a745'},
                    ]
                )
            ])
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_overview_tab(metric):
    """Overview tab: dataset info + data table."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    
    stats = descriptive_stats(df, metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    
    return html.Div([
        # Stats cards row
        html.Div([
            stat_card('Total Countries', f'{len(countries)}', ''),
            stat_card('Date Range', f'{date_min.date()}', f'to {date_max.date()}'),
            stat_card('Total Rows', f'{len(df):,}', 'data points'),
            stat_card('Global Total', f'{latest[metric].sum():,.0f}', metric_label),
        ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '16px',
                  'flexWrap': 'wrap'}),
        
        # Data preview
        html.Div([
            html.Div('Data Preview', style={'fontSize': '14px', 'fontWeight': '600',
                     'color': '#444', 'marginBottom': '8px',
                     'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
            html.Div([
                dash_table.DataTable(
                    id='data-table',
                    columns=[{'name': c, 'id': c} for c in ['country', 'date', 'continent', 
                                                             'new_cases_smoothed', 'new_deaths_smoothed',
                                                             'people_fully_vaccinated_per_hundred']],
                    data=df.head(100).to_dict('records'),
                    page_size=10,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'fontSize': '12px', 'fontFamily': 'Arial',
                        'padding': '6px 12px', 'textAlign': 'left'
                    },
                    style_header={
                        'backgroundColor': '#fafafa', 'fontWeight': '600',
                        'borderBottom': '1px solid #e8e8e8'
                    },
                    style_data={'borderBottom': '1px solid #f0f0f0'}
                )
            ], style={'background': '#fff', 'padding': '12px', 'borderRadius': '4px',
                      'border': '1px solid #e8e8e8'})
        ])
    ])


def build_global_tab(metric):
    """Global Trends tab: map + timeline + trend."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    
    return html.Div([
        # Map + Stats row
        html.Div([
            html.Div([
                dcc.Graph(id='global-map', style={'height': '450px'}, config=PLOTLY_CONFIG)
            ], style={'flex': '1', 'minWidth': '0'}),
            html.Div([
                html.Div([
                    html.Div('Global Statistics', style={'fontSize': '13px', 'fontWeight': '600',
                             'color': '#555', 'marginBottom': '8px',
                             'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '6px'}),
                    html.Div(id='global-stats')
                ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                          'border': '1px solid #e8e8e8'})
            ], style={'width': '280px', 'flexShrink': '0'})
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '16px'}),
        
        # Timeline slider
        html.Div([
            html.Span(id='global-date-label', children=f'Date: {MONTHLY_DATES[-1]}',
                     style={'fontSize': '13px', 'fontWeight': '600', 'color': '#333',
                            'minWidth': '150px'}),
            html.Div([
                dcc.Slider(
                    id='global-slider',
                    min=0, max=len(MONTHLY_DATES) - 1, value=len(MONTHLY_DATES) - 1,
                    marks={i: MONTHLY_DATES[i][:7] for i in range(0, len(MONTHLY_DATES), 
                                                                    max(1, len(MONTHLY_DATES)//6))},
                    step=1, updatemode='drag'
                )
            ], style={'flex': '1', 'margin': '0 16px'}),
            html.Button('▶ Play', id='global-play', n_clicks=0,
                       style={'padding': '4px 16px', 'background': '#fff',
                              'border': '1px solid #ccc', 'borderRadius': '3px',
                              'cursor': 'pointer', 'fontSize': '12px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'padding': '8px 16px',
                  'background': '#fff', 'border': '1px solid #e8e8e8',
                  'borderRadius': '4px', 'marginBottom': '16px'}),
        
        # Global trend chart
        html.Div([
            dcc.Graph(id='global-trend-chart', style={'height': '300px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '12px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_compare_tab(metric, country, compare_list):
    """Country Comparison tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    
    all_c = [country]
    if compare_list:
        all_c.extend([c for c in compare_list if c != country])
    all_c = list(dict.fromkeys(all_c))[:6]
    
    return html.Div([
        html.Div([
            dcc.Graph(
                figure=plot_trend_line(df, all_c, metric, 
                                       title=f'{metric_label} — Country Comparison'),
                style={'height': '450px'},
                config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_deepdive_tab(metric, country):
    """Country Deep Dive tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    vacc_metric = 'people_fully_vaccinated_per_hundred'
    
    return html.Div([
        html.Div(f'Deep Dive: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Div([
                html.Div(f'{metric_label} vs Vaccination Rate',
                        style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px'}),
                dcc.Graph(
                    figure=plot_dual_axis(df, country, metric, vacc_metric),
                    style={'height': '320px'},
                    config=PLOTLY_CONFIG
                )
            ], style={'flex': '1', 'minWidth': '0'}),
            html.Div([
                html.Div('Growth Rate Analysis',
                        style={'fontSize': '12px', 'color': '#666', 'marginBottom': '4px'}),
                dcc.Graph(
                    figure=plot_growth_rate(df, country, metric),
                    style={'height': '320px'},
                    config=PLOTLY_CONFIG
                )
            ], style={'width': '420px', 'flexShrink': '0'})
        ], style={'display': 'flex', 'gap': '16px'})
    ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
              'border': '1px solid #e8e8e8'})


def build_rankings_tab(metric):
    """Rankings tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    top_df = top_countries(df, metric=metric, n=20)
    
    return html.Div([
        html.Div([
            dcc.Graph(
                figure=plot_bar_chart(top_df, x_col='country', y_col=metric,
                                     title=f'Top 20 — {metric_label}',
                                     color_col='continent'),
                style={'height': '550px'},
                config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_correlation_tab(metric):
    """Correlation tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()].copy()
    
    # Pick related metric
    if 'case' in metric.lower():
        compare = 'new_deaths_smoothed'
    elif 'death' in metric.lower():
        compare = 'new_cases_smoothed'
    elif 'vaccin' in metric.lower():
        compare = 'new_cases_smoothed_per_million'
    else:
        compare = 'new_cases_smoothed'
    
    compare_label = next((m['label'] for m in METRICS if m['id'] == compare), compare)
    plot_df = latest.dropna(subset=[metric, compare, 'continent'])
    
    return html.Div([
        html.Div([
            dcc.Graph(
                figure=plot_scatter(plot_df, x_col=metric, y_col=compare,
                                   color_col='continent',
                                   title=f'{metric_label} vs {compare_label}'),
                style={'height': '500px'},
                config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_continent_tab(metric):
    """Continent Analysis tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    
    # Aggregate by continent
    cont_df = latest.groupby('continent')[metric].agg(['sum', 'mean', 'max', 'count']).reset_index()
    cont_df.columns = ['continent', 'total', 'average', 'maximum', 'count']
    cont_df = cont_df.sort_values('total', ascending=True)
    
    fig = plot_bar_chart(cont_df, x_col='continent', y_col='total',
                         title=f'{metric_label} by Continent',
                         color_col='continent')
    
    return html.Div([
        html.Div([
            dcc.Graph(figure=fig, style={'height': '400px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


# ============================================================================
# Shared Components
# ============================================================================

def stat_card(title, value, subtitle):
    return html.Div([
        html.Div(title, style={'fontSize': '11px', 'color': '#888', 'marginBottom': '2px'}),
        html.Div(value, style={'fontSize': '18px', 'fontWeight': '700', 'color': '#222'}),
        html.Div(subtitle, style={'fontSize': '11px', 'color': '#aaa'})
    ], style={'flex': '1', 'minWidth': '140px', 'background': '#fff', 'padding': '12px 16px',
              'borderRadius': '4px', 'border': '1px solid #e8e8e8'})


# ============================================================================
# Interactive Callbacks
# ============================================================================

# Global tab: map
@app.callback(
    Output('global-map', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-slider', 'value')]
)
def update_global_map(metric, slider_val):
    return plot_choropleth_map(df, metric, MONTHLY_DATES[slider_val])


# Global tab: date label
@app.callback(
    Output('global-date-label', 'children'),
    Input('global-slider', 'value')
)
def update_date_label(val):
    return f'Date: {MONTHLY_DATES[val]}'


# Global tab: stats
@app.callback(
    Output('global-stats', 'children'),
    [Input('global-metric', 'value'),
     Input('global-slider', 'value')]
)
def update_global_stats(metric, slider_val):
    date_str = MONTHLY_DATES[slider_val]
    date_df = df[df['date'] == date_str]
    total = date_df[metric].sum()
    avg = date_df[metric].mean()
    mx = date_df[metric].max()
    mx_country = date_df.loc[date_df[metric].idxmax(), 'country'] if date_df[metric].notna().any() else 'N/A'
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    
    return [
        stat_card('Global Total', f'{total:,.0f}', metric_label),
        stat_card('Average', f'{avg:,.1f}', 'per country'),
        stat_card('Maximum', f'{mx:,.0f}', mx_country),
        stat_card('Countries', f'{date_df[metric].notna().sum():,}', 'with data')
    ]


# Global tab: trend chart (syncs with map timeline)
@app.callback(
    Output('global-trend-chart', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value'),
     Input('global-slider', 'value')]
)
def update_global_trend(metric, country, compare_list, slider_val):
    # Fast filter using binary search on sorted dates
    max_date = pd.Timestamp(MONTHLY_DATES[slider_val])
    idx = np.searchsorted(date_values, max_date, side='right')
    filtered_df = df_sorted.iloc[:idx]
    
    all_c = [country]
    if compare_list:
        all_c.extend([c for c in compare_list if c != country])
    all_c = list(dict.fromkeys(all_c))[:6]
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return plot_trend_line(filtered_df, all_c, metric, title=f'{metric_label} — Trend up to {max_date.date()}')


# Play interval (auto-advance every ~400ms to complete in ~30s)
app.layout.children.append(
    dcc.Interval(id='play-interval', interval=400, n_intervals=0, disabled=True)
)

@app.callback(
    Output('play-interval', 'disabled'),
    Input('global-play', 'n_clicks'),
    State('play-interval', 'disabled')
)
def toggle_play(n_clicks, disabled):
    if n_clicks == 0:
        return True
    return not disabled


@app.callback(
    Output('global-slider', 'value'),
    [Input('play-interval', 'n_intervals')],
    [State('global-slider', 'value')]
)
def advance_play(n_intervals, current):
    if current is None:
        return len(MONTHLY_DATES) - 1
    next_val = current + 1
    if next_val >= len(MONTHLY_DATES):
        return 0
    return next_val


# Exit button: close the browser tab
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.close();
        }
        return 'Exit';
    }
    """,
    Output('exit-btn', 'children'),
    Input('exit-btn', 'n_clicks')
)


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    print("Starting COVID-19 Data Explorer...")
    port = int(os.environ.get("PORT", 8050))
    print(f"Open http://127.0.0.1:{port} in your browser for local testing")
    app.run(debug=False, host='0.0.0.0', port=port)
