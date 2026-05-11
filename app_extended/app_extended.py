"""
COVID-19 Data Analysis Platform — Extended Edition
Adds 5 advanced analysis tabs on top of the original 8.
Run: python app_extended.py
Original app.py is NOT modified.
"""

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import os, pickle, time

# ── Original imports ──────────────────────────────────────────────────
from src.data_loader import load_data, get_countries, get_continents, get_date_range, get_numeric_columns
from src.data_cleaner import clean_data, handle_missing_values
from src.data_analysis import (
    global_trend, country_trend, compare_countries, top_countries, descriptive_stats,
    growth_rate_analysis, cumulative_analysis, correlation_analysis, continent_comparison,
    vaccination_impact, get_peak_dates
)
from src.visualization import (
    plot_choropleth_map, plot_trend_line, plot_bar_chart,
    plot_dual_axis, plot_growth_rate, plot_scatter
)

# ── Advanced imports ──────────────────────────────────────────────────
from src.advanced_analysis import (
    moving_average, anomaly_detection, fatality_trend, cross_lag_correlation,
    simple_clustering, country_summary_report, multi_metric_summary
)

# ═══════════════════════════════════════════════════════════════════════
# Data Loading (shared cache with app.py)
# ═══════════════════════════════════════════════════════════════════════
DATA_PATH = 'compact.csv'
CACHE_PATH = 'data_cache.pkl'

print("Loading data...", end=' ', flush=True)
t0 = time.time()

if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, 'rb') as f:
        df_raw, df = pickle.load(f)
else:
    df_raw = load_data(DATA_PATH)
    df = clean_data(df_raw)
    df = handle_missing_values(df, strategy='ffill')
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump((df_raw, df), f)

countries = get_countries(df)
continents = get_continents(df)
date_min, date_max = get_date_range(df)
numeric_cols = get_numeric_columns(df)
all_dates = sorted(df['date'].dt.strftime('%Y-%m-%d').unique())
MONTHLY_DATES = all_dates[::30]
if all_dates[-1] not in MONTHLY_DATES:
    MONTHLY_DATES.append(all_dates[-1])
df_sorted = df.sort_values('date').reset_index(drop=True)
date_values = df_sorted['date'].values

print(f"done ({time.time()-t0:.1f}s)")
print(f"Data: {len(df):,} rows, {len(countries)} countries, {date_min.date()} to {date_max.date()}")

# ── Constants ─────────────────────────────────────────────────────────
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

# ═══════════════════════════════════════════════════════════════════════
# App Init
# ═══════════════════════════════════════════════════════════════════════
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    title='COVID-19 Data Explorer — Extended'
)

PLOTLY_CONFIG = {'displayModeBar': True, 'displaylogo': False,
                 'modeBarButtonsToRemove': ['sendDataToCloud', 'lasso2d', 'select2d',
                                            'autoScale2d', 'toggleSpikelines',
                                            'hoverClosestCartesian', 'hoverCompareCartesian',
                                            'zoomIn2d', 'zoomOut2d']}

# ═══════════════════════════════════════════════════════════════════════
# Tabs (original 8 + advanced 5 = 13)
# ═══════════════════════════════════════════════════════════════════════
TABS = [
    {'label': 'Data Pipeline', 'value': 'tab-pipeline'},
    {'label': 'Overview', 'value': 'tab-overview'},
    {'label': 'Global Trends', 'value': 'tab-global'},
    {'label': 'Country Comparison', 'value': 'tab-compare'},
    {'label': 'Country Deep Dive', 'value': 'tab-deepdive'},
    {'label': 'Rankings', 'value': 'tab-rankings'},
    {'label': 'Correlation', 'value': 'tab-correlation'},
    {'label': 'Continent Analysis', 'value': 'tab-continent'},
    # ── NEW advanced tabs ──
    {'label': ' Moving Avg', 'value': 'tab-ma'},
    {'label': ' Anomalies', 'value': 'tab-anomaly'},
    {'label': ' Fatality', 'value': 'tab-fatality'},
    {'label': ' Lead-Lag', 'value': 'tab-lag'},
    {'label': ' Clusters', 'value': 'tab-cluster'},
]

# ═══════════════════════════════════════════════════════════════════════
# Layout
# ═══════════════════════════════════════════════════════════════════════
app.layout = html.Div([
    html.Div([
        html.Div([
            html.Span('COVID-19 Data Explorer  |  Extended Edition',
                     style={'fontSize': '20px', 'fontWeight': '700', 'color': '#222'}),
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
              'padding': '12px 24px', 'borderBottom': '1px solid #e8e8e8', 'background': '#fff'}),

    # Global controls
    html.Div([
        html.Div([
            html.Span('Metric:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='global-metric', options=[{'label': m['label'], 'value': m['id']} for m in METRICS],
                         value=DEFAULT_METRIC, clearable=False, style={'width': '260px', 'fontSize': '13px'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Span('Country:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='global-country', options=[{'label': c, 'value': c} for c in countries],
                         value=DEFAULT_COUNTRIES[0], clearable=False, style={'width': '180px', 'fontSize': '13px'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
        html.Div([
            html.Span('Compare:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='global-compare', options=[{'label': c, 'value': c} for c in countries],
                         value=DEFAULT_COUNTRIES[1:4], multi=True, style={'width': '260px', 'fontSize': '13px'})
        ], style={'display': 'flex', 'alignItems': 'center'}),
    ], style={'display': 'flex', 'gap': '16px', 'padding': '8px 24px',
              'background': '#fafafa', 'borderBottom': '1px solid #e8e8e8'}),

    dcc.Tabs(id='main-tabs', value='tab-overview',
             children=[dcc.Tab(label=t['label'], value=t['value']) for t in TABS],
             style={'fontSize': '13px', 'fontWeight': '500'}),

    html.Div(id='tab-content', style={'padding': '16px 24px', 'background': '#f5f5f5',
                                       'minHeight': 'calc(100vh - 160px)'}),
    html.Div([
        html.Hr(style={'margin': '0'}),
        html.Div('Data: Our World in Data | Extended Analysis',
                style={'textAlign': 'center', 'padding': '8px', 'fontSize': '11px', 'color': '#999'})
    ])
], style={'fontFamily': 'Arial, Helvetica, sans-serif', 'background': '#f5f5f5', 'minHeight': '100vh'})

# ═══════════════════════════════════════════════════════════════════════
# Shared components
# ═══════════════════════════════════════════════════════════════════════
def stat_card(title, value, subtitle):
    return html.Div([
        html.Div(title, style={'fontSize': '11px', 'color': '#888', 'marginBottom': '2px'}),
        html.Div(value, style={'fontSize': '18px', 'fontWeight': '700', 'color': '#222'}),
        html.Div(subtitle, style={'fontSize': '11px', 'color': '#aaa'})
    ], style={'flex': '1', 'minWidth': '140px', 'background': '#fff', 'padding': '12px 16px',
              'borderRadius': '4px', 'border': '1px solid #e8e8e8'})

# ═══════════════════════════════════════════════════════════════════════
# Tab Renderer
# ═══════════════════════════════════════════════════════════════════════
@app.callback(
    Output('tab-content', 'children'),
    [Input('main-tabs', 'value'),
     Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def render_tab(tab, metric, country, compare_list):
    if tab == 'tab-pipeline':   return build_pipeline()
    if tab == 'tab-overview':   return build_overview(metric)
    if tab == 'tab-global':     return build_global(metric, compare_list)
    if tab == 'tab-compare':    return build_compare(metric, country, compare_list)
    if tab == 'tab-deepdive':   return build_deepdive(metric, country)
    if tab == 'tab-rankings':   return build_rankings(metric)
    if tab == 'tab-correlation': return build_correlation(metric)
    if tab == 'tab-continent':  return build_continent(metric)
    # Advanced tabs
    if tab == 'tab-ma':         return build_ma_tab(metric, country)
    if tab == 'tab-anomaly':    return build_anomaly_tab(metric, country)
    if tab == 'tab-fatality':   return build_fatality_tab(country)
    if tab == 'tab-lag':        return build_lag_tab(country)
    if tab == 'tab-cluster':    return build_cluster_tab()
    return html.Div()

# ═══════════════════════════════════════════════════════════════════════
# Original Tab Builders (condensed)
# ═══════════════════════════════════════════════════════════════════════

def build_pipeline():
    from src.data_cleaner import get_cleaning_summary
    summary = get_cleaning_summary(df_raw, df)
    cols_info = []
    for col in df.columns:
        sample = df[col].dropna().iloc[:3].tolist()
        cols_info.append({'name': col, 'dtype': str(df[col].dtype),
                          'non_null': int(df[col].notna().sum()),
                          'null_count': int(df[col].isna().sum()), 'sample_values': sample})
    return html.Div([
        section_card('Data Loading', [
            html.Div([stat_card('Total Rows', f'{len(df_raw):,}', ''),
                      stat_card('Columns', str(len(df_raw.columns)), ''),
                      stat_card('Date Range', f'{date_min.date()} to {date_max.date()}', '')],
                     style={'display': 'flex', 'gap': '12px'})
        ]),
        section_card('Data Cleaning', [
            html.Ul([
                html.Li(f'Removed {summary["duplicates_removed"]:,} duplicate rows'),
                html.Li('Forward/backward-filled missing values within each country'),
                html.Li(f'Missing values: {summary["missing_before"]:,} → {summary["missing_after"]:,}'),
            ], style={'fontSize': '13px', 'color': '#444'})
        ]),
        section_card('Column Overview', [
            dash_table.DataTable(
                columns=[{'name': c, 'id': c} for c in ['name', 'dtype', 'non_null', 'null_count', 'sample_values']],
                data=[{**c, 'non_null': f'{c["non_null"]:,}', 'null_count': f'{c["null_count"]:,}',
                       'sample_values': ', '.join(str(v) for v in c['sample_values'])} for c in cols_info],
                page_size=15, style_table={'overflowX': 'auto'},
                style_cell={'fontSize': '12px', 'padding': '6px 12px'},
                style_header={'backgroundColor': '#fafafa', 'fontWeight': '600'})
        ])
    ])

def build_overview(metric):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    stats = descriptive_stats(df, metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    return html.Div([
        html.Div([
            stat_card('Countries', f'{len(countries)}', ''),
            stat_card('Date Range', f'{date_min.date()}', f'to {date_max.date()}'),
            stat_card('Global Total', f'{latest[metric].sum():,.0f}', metric_label),
            stat_card('Mean (latest)', f'{stats["mean"]:,.1f}', metric_label),
        ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '16px'}),
        dash_table.DataTable(
            columns=[{'name': c, 'id': c} for c in ['country', 'date', 'continent', metric]],
            data=df[['country', 'date', 'continent', metric]].head(50).to_dict('records'),
            page_size=10, style_table={'overflowX': 'auto'},
            style_cell={'fontSize': '12px', 'padding': '6px 12px'},
            style_header={'backgroundColor': '#fafafa', 'fontWeight': '600'})
    ])

def build_global(metric, compare_list=None):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return html.Div([
        html.Div([
            html.Div([dcc.Graph(id='global-map', style={'height': '400px'}, config=PLOTLY_CONFIG)],
                     style={'flex': '1'}),
            html.Div([html.Div(id='global-stats')], style={'width': '260px'})
        ], style={'display': 'flex', 'gap': '16px', 'marginBottom': '12px'}),
        html.Div([
            dcc.Slider(id='global-slider', min=0, max=len(MONTHLY_DATES)-1, value=len(MONTHLY_DATES)-1,
                       marks={i: MONTHLY_DATES[i][:7] for i in range(0, len(MONTHLY_DATES), max(1, len(MONTHLY_DATES)//6))},
                       step=1, updatemode='drag')
        ], style={'padding': '8px 16px', 'background': '#fff', 'border': '1px solid #e8e8e8', 'borderRadius': '4px', 'marginBottom': '12px'}),
        html.Div([dcc.Graph(id='global-trend-chart', style={'height': '300px'}, config=PLOTLY_CONFIG)],
                 style={'background': '#fff', 'padding': '12px'})
    ])

def build_compare(metric, country, compare_list=None):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    all_c = [country]
    if compare_list:
        all_c.extend([c for c in compare_list if c != country])
    else:
        all_c.extend([c for c in DEFAULT_COUNTRIES if c != country])
    all_c = list(dict.fromkeys(all_c))[:6]
    return html.Div([
        dcc.Graph(figure=plot_trend_line(df, all_c, metric, f'{metric_label} — Comparison'),
                  style={'height': '450px'}, config=PLOTLY_CONFIG)
    ], style={'background': '#fff', 'padding': '16px'})

def build_deepdive(metric, country):
    vacc_metric = 'people_fully_vaccinated_per_hundred'
    return html.Div([
        html.Div(f'Deep Dive: {country}', style={'fontSize': '15px', 'fontWeight': '600', 'marginBottom': '12px'}),
        html.Div([
            html.Div([dcc.Graph(figure=plot_dual_axis(df, country, metric, vacc_metric),
                                style={'height': '320px'}, config=PLOTLY_CONFIG)], style={'flex': '1'}),
            html.Div([dcc.Graph(figure=plot_growth_rate(df, country, metric),
                                style={'height': '320px'}, config=PLOTLY_CONFIG)], style={'width': '420px'})
        ], style={'display': 'flex', 'gap': '16px'})
    ], style={'background': '#fff', 'padding': '16px'})

def build_rankings(metric):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    top_df = top_countries(df, metric=metric, n=20)
    return html.Div([
        dcc.Graph(figure=plot_bar_chart(top_df, 'country', metric, f'Top 20 — {metric_label}', 'continent'),
                  style={'height': '550px'}, config=PLOTLY_CONFIG)
    ], style={'background': '#fff', 'padding': '16px'})

def build_correlation(metric):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    if 'case' in metric.lower(): compare = 'new_deaths_smoothed'
    elif 'death' in metric.lower(): compare = 'new_cases_smoothed'
    elif 'vaccin' in metric.lower(): compare = 'new_cases_smoothed_per_million'
    else: compare = 'new_cases_smoothed'
    latest = df.loc[df.groupby('country')['date'].idxmax()].dropna(subset=[metric, compare, 'continent'])
    return html.Div([
        dcc.Graph(figure=plot_scatter(latest, metric, compare, 'continent', f'{metric_label} vs {compare}'),
                  style={'height': '500px'}, config=PLOTLY_CONFIG)
    ], style={'background': '#fff', 'padding': '16px'})

def build_continent(metric):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    cont_df = latest.groupby('continent')[metric].agg(['sum', 'mean', 'count']).reset_index()
    cont_df.columns = ['continent', 'total', 'average', 'count']
    cont_df = cont_df.sort_values('total', ascending=True)
    return html.Div([
        dcc.Graph(figure=plot_bar_chart(cont_df, 'continent', 'total', f'{metric_label} by Continent', 'continent'),
                  style={'height': '400px'}, config=PLOTLY_CONFIG)
    ], style={'background': '#fff', 'padding': '16px'})

def section_card(title, children):
    return html.Div([
        html.Div(title, style={'fontSize': '14px', 'fontWeight': '600', 'color': '#444',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px', 'marginBottom': '12px'}),
        html.Div(children)
    ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
              'border': '1px solid #e8e8e8', 'marginBottom': '12px'})

# ═══════════════════════════════════════════════════════════════════════
# ADVANCED Tab: Moving Average
# ═══════════════════════════════════════════════════════════════════════
def build_ma_tab(metric, country):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return html.Div([
        html.Div(f'Moving Average Analysis: {country}', style={'fontSize': '15px', 'fontWeight': '600', 'marginBottom': '12px'}),
        html.Div([
            dcc.Graph(id='ma-chart', style={'height': '400px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px'})
    ])

@app.callback(
    Output('ma-chart', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-country', 'value')]
)
def update_ma_chart(metric, country):
    import plotly.graph_objects as go
    ma_df = moving_average(df, country, metric)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ma_df['date'], y=ma_df[metric], name='Raw',
                             line=dict(color='#ddd', width=1), opacity=0.5))
    colors = ['#2a4d8f', '#b91f1f', '#1a7a3a']
    for i, w in enumerate([7, 14, 30]):
        col = f'ma_{w}d'
        fig.add_trace(go.Scatter(x=ma_df['date'], y=ma_df[col],
                                 name=f'{w}-day MA', line=dict(color=colors[i], width=2)))
    fig.update_layout(title=f'{country}: {metric.replace("_"," ").title()} Moving Averages',
                      template='none', hovermode='x unified', margin={'l': 40, 'r': 20, 't': 40, 'b': 40})
    return fig

# ═══════════════════════════════════════════════════════════════════════
# ADVANCED Tab: Anomaly Detection
# ═══════════════════════════════════════════════════════════════════════
def build_anomaly_tab(metric, country):
    return html.Div([
        html.Div([
            html.Span('Window:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='anomaly-window', options=[{'label': f'{w} days', 'value': w} for w in [7, 14, 30]],
                         value=14, clearable=False, style={'width': '140px', 'fontSize': '13px'}),
            html.Span('Threshold:', style={'fontSize': '12px', 'color': '#666', 'marginLeft': '16px', 'marginRight': '6px'}),
            dcc.Dropdown(id='anomaly-threshold', options=[{'label': f'{t}σ', 'value': t} for t in [1.5, 2.0, 2.5, 3.0]],
                         value=2.0, clearable=False, style={'width': '120px', 'fontSize': '13px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px', 'gap': '8px'}),
        html.Div([dcc.Graph(id='anomaly-chart', style={'height': '400px'}, config=PLOTLY_CONFIG)],
                 style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px'}),
    ])

@app.callback(
    Output('anomaly-chart', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('anomaly-window', 'value'),
     Input('anomaly-threshold', 'value')]
)
def update_anomaly_chart(metric, country, window, threshold):
    import plotly.graph_objects as go
    anom_df = anomaly_detection(df, country, metric, threshold=threshold, window=window)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anom_df['date'], y=anom_df[metric], name=metric.replace('_', ' ').title(),
                             line=dict(color='#2a4d8f', width=1)))
    # Rolling mean band
    fig.add_trace(go.Scatter(x=anom_df['date'], y=anom_df['rolling_mean'],
                             name=f'{window}d mean', line=dict(color='#999', width=1, dash='dot')))
    # Anomaly markers
    anom_pts = anom_df[anom_df['is_anomaly']]
    fig.add_trace(go.Scatter(x=anom_pts['date'], y=anom_pts[metric], mode='markers',
                             name=f'Anomalies ({len(anom_pts)})',
                             marker=dict(color='#b91f1f', size=8, symbol='x')))
    fig.update_layout(title=f'{country}: Anomaly Detection ({len(anom_pts)} anomalies)',
                      template='none', hovermode='x unified', margin={'l': 40, 'r': 20, 't': 40, 'b': 40})
    return fig

# ═══════════════════════════════════════════════════════════════════════
# ADVANCED Tab: Fatality Analysis
# ═══════════════════════════════════════════════════════════════════════
def build_fatality_tab(country):
    return html.Div([
        html.Div(f'Fatality & Mortality: {country}', style={'fontSize': '15px', 'fontWeight': '600', 'marginBottom': '12px'}),
        html.Div([
            html.Div([dcc.Graph(id='fatality-chart', style={'height': '350px'}, config=PLOTLY_CONFIG)],
                     style={'flex': '1'}),
            html.Div([html.Div(id='fatality-stats')], style={'width': '280px'})
        ], style={'display': 'flex', 'gap': '16px'})
    ])

@app.callback(
    [Output('fatality-chart', 'figure'),
     Output('fatality-stats', 'children')],
    Input('global-country', 'value')
)
def update_fatality(country):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    fat_df = fatality_trend(df, country)
    rpt = country_summary_report(df, country)

    fig = make_subplots(specs=[[{'secondary_y': True}]])
    fig.add_trace(go.Scatter(x=fat_df['date'], y=fat_df['total_cases'], name='Total Cases',
                             line=dict(color='#2a4d8f', width=1.5)), secondary_y=False)
    fig.add_trace(go.Scatter(x=fat_df['date'], y=fat_df['cfr_14d_ma'], name='CFR (14d MA) %',
                             line=dict(color='#b91f1f', width=2)), secondary_y=True)
    fig.update_layout(title=f'{country}: Cases & Case Fatality Rate', template='none',
                      hovermode='x unified', margin={'l': 40, 'r': 40, 't': 40, 'b': 40})
    fig.update_yaxes(title_text='Total Cases', secondary_y=False)
    fig.update_yaxes(title_text='CFR %', secondary_y=True)

    stats = [
        stat_card('CFR (latest)', f'{rpt.get("cfr_percent", 0):.3f}%', ''),
        stat_card('Total Cases', f'{rpt.get("total_cases", 0):,.0f}', ''),
        stat_card('Total Deaths', f'{rpt.get("total_deaths", 0):,.0f}', ''),
    ]
    if 'peak_new_cases' in rpt:
        stats.append(stat_card('Peak Cases', f'{rpt["peak_new_cases"]["value"]:,.0f}',
                                rpt['peak_new_cases']['date']))
    if 'peak_new_deaths' in rpt:
        stats.append(stat_card('Peak Deaths', f'{rpt["peak_new_deaths"]["value"]:,.0f}',
                                rpt['peak_new_deaths']['date']))
    if 'recent_trend' in rpt:
        stats.append(stat_card('Recent Trend', f'{rpt["recent_trend"]["change_pct"]:+.1f}%', 'last 30 days'))
    return fig, stats

# ═══════════════════════════════════════════════════════════════════════
# ADVANCED Tab: Lead-Lag Correlation
# ═══════════════════════════════════════════════════════════════════════
def build_lag_tab(country):
    lag_metrics = [
        {'id': 'new_cases_smoothed', 'label': 'New Cases'},
        {'id': 'new_deaths_smoothed', 'label': 'New Deaths'},
        {'id': 'people_fully_vaccinated_per_hundred', 'label': 'Vaccination %'},
        {'id': 'stringency_index', 'label': 'Stringency'},
    ]
    return html.Div([
        html.Div(f'Lead-Lag Analysis: {country}', style={'fontSize': '15px', 'fontWeight': '600', 'marginBottom': '12px'}),
        html.Div([
            html.Span('Lead:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='lag-x', options=[{'label': m['label'], 'value': m['id']} for m in lag_metrics],
                         value='new_cases_smoothed', clearable=False, style={'width': '200px', 'fontSize': '13px'}),
            html.Span('Lag:', style={'fontSize': '12px', 'color': '#666', 'marginLeft': '16px', 'marginRight': '6px'}),
            dcc.Dropdown(id='lag-y', options=[{'label': m['label'], 'value': m['id']} for m in lag_metrics],
                         value='new_deaths_smoothed', clearable=False, style={'width': '200px', 'fontSize': '13px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
        html.Div([dcc.Graph(id='lag-chart', style={'height': '350px'}, config=PLOTLY_CONFIG)],
                 style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px'}),
    ])

@app.callback(
    Output('lag-chart', 'figure'),
    [Input('global-country', 'value'),
     Input('lag-x', 'value'),
     Input('lag-y', 'value')]
)
def update_lag_chart(country, metric_x, metric_y):
    import plotly.graph_objects as go
    lag_df = cross_lag_correlation(df, country, metric_x, metric_y, max_lag=21)
    best_lag = lag_df.loc[lag_df['correlation'].idxmax()]
    fig = go.Figure()
    colors = ['#b91f1f' if c > 0.7 else '#2a4d8f' for c in lag_df['correlation']]
    fig.add_trace(go.Bar(x=lag_df['lag_days'], y=lag_df['correlation'], marker_color=colors,
                         hovertemplate='Lag: %{x}d<br>r = %{y:.3f}<extra></extra>'))
    fig.add_hline(y=0, line_color='#ccc', line_width=1)
    fig.update_layout(
        title=f'{country}: {metric_x.replace("_"," ").title()} leads {metric_y.replace("_"," ").title()} '
              f'(best lag={int(best_lag["lag_days"])}d, r={best_lag["correlation"]:.3f})',
        template='none', xaxis_title='Lag (days)', yaxis_title='Correlation (r)',
        margin={'l': 40, 'r': 20, 't': 40, 'b': 40})
    return fig

# ═══════════════════════════════════════════════════════════════════════
# ADVANCED Tab: Country Clustering
# ═══════════════════════════════════════════════════════════════════════
def build_cluster_tab():
    return html.Div([
        html.Div([
            html.Span('Clusters:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='cluster-n', options=[{'label': str(k), 'value': k} for k in [3, 4, 5, 6, 7]],
                         value=5, clearable=False, style={'width': '100px', 'fontSize': '13px'}),
        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
        html.Div([
            html.Div([dcc.Graph(id='cluster-scatter', style={'height': '420px'}, config=PLOTLY_CONFIG)],
                     style={'flex': '1'}),
            html.Div([html.Div(id='cluster-summary')], style={'width': '300px'})
        ], style={'display': 'flex', 'gap': '16px'})
    ])

@app.callback(
    [Output('cluster-scatter', 'figure'),
     Output('cluster-summary', 'children')],
    Input('cluster-n', 'value')
)
def update_cluster(n_clusters):
    import plotly.express as px
    clust_df = simple_clustering(df, n_clusters=n_clusters)
    fig = px.scatter(clust_df, x='total_cases_per_million', y='total_deaths_per_million',
                     color='cluster', hover_name='country', size='population',
                     color_continuous_scale='Viridis' if n_clusters > 5 else None,
                     title=f'Country Clusters (k={n_clusters})')
    fig.update_traces(marker=dict(line=dict(width=0.5, color='rgba(0,0,0,0.2)')))
    fig.update_layout(template='none', margin={'l': 40, 'r': 20, 't': 40, 'b': 40})

    # Summary per cluster
    summary = clust_df.groupby('cluster').agg(
        countries=('country', 'count'),
        avg_cases=('total_cases_per_million', 'mean'),
        avg_deaths=('total_deaths_per_million', 'mean'),
        avg_vacc=('people_fully_vaccinated_per_hundred', 'mean'),
    ).round(1).reset_index()

    cards = []
    for _, row in summary.iterrows():
        top_countries = clust_df[clust_df['cluster'] == row['cluster']]['country'].head(3).tolist()
        cards.append(html.Div([
            html.Div(f'Cluster {int(row["cluster"])}', style={'fontSize': '13px', 'fontWeight': '700', 'color': '#222'}),
            html.Div(f'{int(row["countries"])} countries', style={'fontSize': '11px', 'color': '#888'}),
            html.Div(f'Avg cases/m: {row["avg_cases"]:,.0f}', style={'fontSize': '11px', 'color': '#555'}),
            html.Div(f'Avg deaths/m: {row["avg_deaths"]:,.0f}', style={'fontSize': '11px', 'color': '#555'}),
            html.Div(f'Avg vacc: {row["avg_vacc"]:.1f}%', style={'fontSize': '11px', 'color': '#555'}),
            html.Div('Top: ' + ', '.join(top_countries), style={'fontSize': '10px', 'color': '#aaa', 'marginTop': '4px'}),
        ], style={'background': '#fff', 'padding': '10px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '8px'}))
    return fig, cards

# ═══════════════════════════════════════════════════════════════════════
# Original Global callbacks
# ═══════════════════════════════════════════════════════════════════════
@app.callback(Output('global-map', 'figure'), [Input('global-metric', 'value'), Input('global-slider', 'value')])
def update_global_map(metric, slider_val):
    return plot_choropleth_map(df, metric, MONTHLY_DATES[slider_val])

@app.callback(Output('global-stats', 'children'), [Input('global-metric', 'value'), Input('global-slider', 'value')])
def update_global_stats(metric, slider_val):
    date_str = MONTHLY_DATES[slider_val]
    date_df = df[df['date'] == date_str]
    total = date_df[metric].sum()
    avg = date_df[metric].mean()
    mx = date_df[metric].max()
    mx_country = date_df.loc[date_df[metric].idxmax(), 'country'] if date_df[metric].notna().any() else 'N/A'
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return [stat_card('Global Total', f'{total:,.0f}', metric_label),
            stat_card('Average', f'{avg:,.1f}', 'per country'),
            stat_card('Maximum', f'{mx:,.0f}', mx_country),
            stat_card('Countries', f'{date_df[metric].notna().sum():,}', 'with data')]

@app.callback(Output('global-trend-chart', 'figure'),
              [Input('global-metric', 'value'), Input('global-country', 'value'),
               Input('global-compare', 'value'), Input('global-slider', 'value')])
def update_global_trend(metric, country, compare_list, slider_val):
    max_date = pd.Timestamp(MONTHLY_DATES[slider_val])
    idx = np.searchsorted(date_values, max_date, side='right')
    filtered_df = df_sorted.iloc[:idx]
    all_c = [country]
    if compare_list:
        all_c.extend([c for c in compare_list if c != country])
    else:
        all_c.extend([c for c in DEFAULT_COUNTRIES[1:3] if c != country])
    all_c = list(dict.fromkeys(all_c))[:6]
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return plot_trend_line(filtered_df, all_c, metric,
                           title=f'{metric_label} — Trend up to {max_date.date()}')

# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Starting COVID-19 Data Explorer — Extended Edition...")
    print(f"Open http://127.0.0.1:8051 in your browser")
    app.run(debug=False, host='127.0.0.1', port=8051)
