"""
COVID-19 Data Analysis Platform — Extended Edition
Adds 5 advanced analysis tabs on top of the original 8.
Run: python app_extended.py
Original app.py is NOT modified.
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import os, pickle, time
import plotly.graph_objects as go
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ── Original imports ──────────────────────────────────────────────────
from src.data_loader import load_data, get_countries, get_continents, get_date_range, get_numeric_columns
from src.data_cleaner import (
    clean_data, handle_missing_values, filter_by_date,
    filter_by_country, CovidDataPreprocessor
)
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
    print("Running full preprocessing pipeline...")
    processor = CovidDataPreprocessor(DATA_PATH)
    df_raw = processor.load_data()
    processor.clean_data()
    df = processor.prepare_for_analysis(variables=None)
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

# Precompute country-level cluster inputs once; clustering pages should not scan
# the full 570k-row time series on every tab switch or k change.
CLUSTER_FEATURES = [
    'total_cases_per_million',
    'total_deaths_per_million',
    'people_fully_vaccinated_per_hundred',
    'population',
]
CLUSTER_BASE_DF = df.loc[df.groupby('country')['date'].idxmax()].dropna(subset=CLUSTER_FEATURES).copy()
CLUSTER_CACHE = {}

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

MA_PERIOD_OPTIONS = [
    {'label': 'Full Dataset', 'value': 'all'},
    {'label': '2020 Initial Spread', 'value': '2020_initial'},
    {'label': '2021 Vaccination / Delta', 'value': '2021_delta'},
    {'label': '2022 Omicron Wave', 'value': '2022_omicron'},
    {'label': '2023-2026 Post-Peak Period', 'value': '2023_post_peak'},
    {'label': 'Latest 180 Days in Dataset', 'value': 'latest_180'},
]

CORRELATION_METRICS = METRICS + [
    {'id': 'population_density', 'label': 'Population Density', 'group': 'Demographics'},
    {'id': 'median_age', 'label': 'Median Age', 'group': 'Demographics'},
    {'id': 'life_expectancy', 'label': 'Life Expectancy', 'group': 'Demographics'},
    {'id': 'gdp_per_capita', 'label': 'GDP per Capita', 'group': 'Economy'},
    {'id': 'diabetes_prevalence', 'label': 'Diabetes Prevalence', 'group': 'Health'},
    {'id': 'hospital_beds_per_thousand', 'label': 'Hospital Beds per Thousand', 'group': 'Health'},
    {'id': 'human_development_index', 'label': 'Human Development Index', 'group': 'Economy'},
]

CORRELATION_COLOR_OPTIONS = [
    {'label': 'Continent', 'value': 'continent'},
    {'label': 'Population Size', 'value': 'population_group'},
    {'label': 'GDP Level', 'value': 'gdp_group'},
    {'label': 'Median Age Group', 'value': 'age_group'},
    {'label': 'HDI Level', 'value': 'hdi_group'},
    {'label': 'Life Expectancy Group', 'value': 'life_expectancy_group'},
]

# ═══════════════════════════════════════════════════════════════════════
# Sidebar Navigation Definition
# ═══════════════════════════════════════════════════════════════════════
SIDEBAR_GROUPS = [
    {
        'icon': '📊',
        'label': 'Overview',
        'group_id': 'group-overview',
        'items': [
            {'label': 'Global Trends', 'nav_id': 'global', 'value': 'tab-global'},
            {'label': 'Summary Statistics', 'nav_id': 'summary', 'value': 'tab-overview'},
            {'label': 'Pandemic Timeline', 'nav_id': 'timeline', 'value': 'tab-pipeline'},
        ]
    },
    {
        'icon': '📈',
        'label': 'Comparison Analysis',
        'group_id': 'group-comparison',
        'items': [
            {'label': 'Country Comparison', 'nav_id': 'country-comparison', 'value': 'tab-compare'},
            {'label': 'Continent Comparison', 'nav_id': 'continent-comparison', 'value': 'tab-continent'},
            {'label': 'Rankings', 'nav_id': 'rankings', 'value': 'tab-rankings'},
        ]
    },
    {
        'icon': '🔬',
        'label': 'Trend Analysis',
        'group_id': 'group-trend',
        'items': [
            {'label': 'Time Series', 'nav_id': 'time-series', 'value': 'tab-deepdive'},
            {'label': 'Moving Average', 'nav_id': 'moving-average', 'value': 'tab-ma'},
            {'label': 'Growth Rate', 'nav_id': 'growth-rate', 'value': 'tab-deepdive'},
            {'label': 'Fatality Trend', 'nav_id': 'fatality-trend', 'value': 'tab-fatality'},
        ]
    },
    {
        'icon': 'R',
        'label': 'Relationship Analysis',
        'group_id': 'group-relationship',
        'items': [
            {'label': 'Correlation', 'nav_id': 'correlation', 'value': 'tab-correlation'},
            {'label': 'Lead-Lag Analysis', 'nav_id': 'lead-lag', 'value': 'tab-lag'},
        ]
    },
    {
        'icon': 'AI',
        'label': 'Advanced Analytics',
        'group_id': 'group-advanced',
        'items': [
            {'label': 'Clustering', 'nav_id': 'clustering', 'value': 'tab-cluster'},
            {'label': 'Anomaly Detection', 'nav_id': 'anomaly-detection', 'value': 'tab-anomaly'},
        ]
    }
]

ALL_TAB_VALUES = [item['value'] for group in SIDEBAR_GROUPS for item in group['items']]
DEFAULT_TAB = 'tab-global'
DEFAULT_NAV = 'global'

SIDEBAR_ICON_BY_GROUP = {
    'group-overview': 'O',
    'group-comparison': 'C',
    'group-trend': 'T',
    'group-relationship': 'R',
    'group-advanced': 'AI',
}
SHORT_LABEL_BY_NAV = {
    'global': 'Global',
    'summary': 'Stats',
    'timeline': 'Time',
    'country-comparison': 'Cntry',
    'continent-comparison': 'Cont',
    'rankings': 'Rank',
    'time-series': 'Series',
    'moving-average': 'MA',
    'growth-rate': 'Growth',
    'fatality-trend': 'Fatal',
    'correlation': 'Corr',
    'lead-lag': 'Lag',
    'clustering': 'Clus',
    'anomaly-detection': 'Anom',
}
for _group in SIDEBAR_GROUPS:
    _group['icon'] = SIDEBAR_ICON_BY_GROUP[_group['group_id']]
    for _item in _group['items']:
        _item['short'] = SHORT_LABEL_BY_NAV[_item['nav_id']]
ALL_TAB_ITEMS = [item for group in SIDEBAR_GROUPS for item in group['items']]

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
# Layout
# ═══════════════════════════════════════════════════════════════════════

def sidebar_container_style(collapsed=False):
    return {
        'background': '#2c2c2c', 'color': '#fff',
        'width': '64px' if collapsed else '220px',
        'height': '100vh',
        'minHeight': '100vh',
        'position': 'sticky',
        'top': '0',
        'alignSelf': 'flex-start',
        'flexShrink': '0',
        'overflowY': 'auto', 'overflowX': 'hidden',
        'borderRight': '1px solid #3a3a3a',
        'display': 'flex', 'flexDirection': 'column',
        'transition': 'width 0.15s ease'
    }


def sidebar_item_style(active=False):
    return {
        'display': 'block',
        'padding': '8px 14px 8px 38px',
        'fontSize': '12px',
        'cursor': 'pointer',
        'borderRadius': '4px',
        'color': '#fff' if active else '#aaa',
        'background': '#1a76d2' if active else 'transparent',
        'borderLeft': '3px solid #80bdff' if active else '3px solid transparent',
        'marginBottom': '2px',
        'whiteSpace': 'nowrap',
        'writingMode': 'horizontal-tb',
        'textOrientation': 'mixed',
        'transform': 'none',
        'transition': 'background 0.12s ease, color 0.12s ease',
        'userSelect': 'none'
    }


def collapsed_item_style(active=False):
    return {
        'height': '42px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'fontSize': '11px',
        'fontWeight': '700' if active else '600',
        'cursor': 'pointer',
        'borderRadius': '6px',
        'margin': '4px 7px',
        'color': '#fff' if active else '#bbb',
        'background': '#1a76d2' if active else 'transparent',
        'border': '1px solid #4ea1ff' if active else '1px solid transparent',
        'userSelect': 'none'
    }


def collapsed_toggle_style():
    return {
        'height': '38px',
        'display': 'flex',
        'alignItems': 'center',
        'justifyContent': 'center',
        'fontSize': '18px',
        'fontWeight': '700',
        'cursor': 'pointer',
        'color': '#d8d8d8',
        'borderBottom': '1px solid #3a3a3a',
        'marginBottom': '6px',
        'position': 'sticky',
        'top': '0',
        'background': '#2c2c2c',
        'zIndex': '2',
        'userSelect': 'none'
    }


def group_arrow_style(expanded=False):
    return {
        'marginLeft': 'auto', 'fontSize': '10px', 'color': '#888',
        'transition': 'none',
        'transform': 'none'
    }


def group_items_style(expanded=False):
    return {
        'display': 'block' if expanded else 'none',
        'writingMode': 'horizontal-tb',
        'textOrientation': 'mixed',
        'transform': 'none',
        'transition': 'none'
    }


# Build sidebar inline
_collapsed_children = [
    html.Div('>', id='sidebar-toggle-collapsed', n_clicks=0,
             style=collapsed_toggle_style(), title='Expand sidebar')
] + [
    html.Div(
        _item['short'],
        id=f'collapsed-item-{_item["nav_id"]}',
        n_clicks=0,
        style=collapsed_item_style(_item['nav_id'] == DEFAULT_NAV),
        title=_item['label']
    )
    for _item in ALL_TAB_ITEMS
]

_expanded_children = []
for _gi, _group in enumerate(SIDEBAR_GROUPS):
    _expanded_children.append(
        html.Div(
            [
                html.Span(_group['icon'], style={'marginRight': '8px', 'fontSize': '16px'}),
                html.Span(_group['label'], style={'fontSize': '13px', 'fontWeight': '600', 'color': '#ccc'}),
                html.Span('v' if _gi == 0 else '>', id=f'group-arrow-{_group["group_id"]}',
                         style={'marginLeft': 'auto', 'fontSize': '10px', 'color': '#888',
                                'transition': 'none', 'transform': 'none'})
            ],
            id=f'group-header-{_group["group_id"]}',
            n_clicks=0,
            style={'display': 'flex', 'alignItems': 'center', 'padding': '10px 14px',
                   'cursor': 'pointer', 'borderRadius': '4px', 'marginBottom': '2px',
                   'userSelect': 'none'}
        )
    )
    _item_divs = []
    for _item in _group['items']:
        _item_divs.append(
            html.Div(
                _item['label'],
                id=f'sidebar-item-{_item["nav_id"]}',
                n_clicks=0,
                style=sidebar_item_style(_item['nav_id'] == DEFAULT_NAV)
            )
        )
    _expanded_children.append(
        html.Div(
            _item_divs,
            id=f'group-items-{_group["group_id"]}',
            style=group_items_style(_gi == 0)
        )
    )

_sidebar = html.Div([
    html.Div(_collapsed_children, id='sidebar-collapsed',
             style={'display': 'none', 'padding': '8px 0'}),
    html.Div(_expanded_children + [
        html.Div('◀', id='sidebar-toggle', n_clicks=0,
                style={'textAlign': 'center', 'padding': '8px', 'cursor': 'pointer',
                       'fontSize': '14px', 'color': '#888',
                       'borderTop': '1px solid #3a3a3a', 'marginTop': 'auto'},
                title='Collapse sidebar')
    ], id='sidebar-expanded',
       style={'display': 'flex', 'flexDirection': 'column', 'height': '100%'})
], id='sidebar-container', style={
    **sidebar_container_style(False)
})

app.layout = html.Div([
    dcc.Store(id='sidebar-state', data={'collapsed': False, 'active_tab': DEFAULT_TAB, 'active_nav': DEFAULT_NAV}),
    dcc.Store(id='group-states', data={group['group_id']: (gi == 0) for gi, group in enumerate(SIDEBAR_GROUPS)}),

    html.Div([
        _sidebar,

        html.Div([
            html.Div([
                html.Div([
                    html.Span('COVID-19 Data Explorer  |  Extended Edition',
                             style={'fontSize': '20px', 'fontWeight': '700', 'color': '#222'}),
                ], style={'display': 'flex', 'alignItems': 'center'}),
                html.Button('Exit', id='exit-btn', n_clicks=0,
                           style={'padding': '6px 20px', 'background': '#fff',
                                  'border': '1px solid #ccc', 'borderRadius': '3px',
                                  'cursor': 'pointer', 'fontSize': '12px', 'color': '#666'})
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                      'padding': '12px 24px', 'borderBottom': '1px solid #e8e8e8', 'background': '#fff'}),

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

            html.Div(id='tab-content', style={'padding': '16px 24px', 'background': '#f5f5f5',
                                               'minHeight': 'calc(100vh - 120px)'}),

            html.Div([
                html.Hr(style={'margin': '0'}),
                html.Div('Data: Our World in Data | Extended Analysis',
                        style={'textAlign': 'center', 'padding': '8px', 'fontSize': '11px', 'color': '#999'})
            ])
        ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'minWidth': '0'})
    ], style={'display': 'flex', 'minHeight': '100vh', 'alignItems': 'stretch'})
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
# Sidebar Callbacks
# ═══════════════════════════════════════════════════════════════════════

@app.callback(
    Output('sidebar-state', 'data'),
    [Input('sidebar-toggle', 'n_clicks'),
     Input('sidebar-toggle-collapsed', 'n_clicks')] +
    [Input(f'sidebar-item-{item["nav_id"]}', 'n_clicks') for item in ALL_TAB_ITEMS] +
    [Input(f'collapsed-item-{item["nav_id"]}', 'n_clicks') for item in ALL_TAB_ITEMS],
    State('sidebar-state', 'data'),
    prevent_initial_call=True
)
def update_sidebar_state(*args):
    state = dict(args[-1] or {'collapsed': False, 'active_tab': DEFAULT_TAB, 'active_nav': DEFAULT_NAV})
    trigger_id = dash.callback_context.triggered[0]['prop_id'].split('.')[0]

    if trigger_id in ('sidebar-toggle', 'sidebar-toggle-collapsed'):
        state['collapsed'] = not state.get('collapsed', False)
        return state

    for item in ALL_TAB_ITEMS:
        if trigger_id in (f'sidebar-item-{item["nav_id"]}', f'collapsed-item-{item["nav_id"]}'):
            state['active_tab'] = item['value']
            state['active_nav'] = item['nav_id']
            return state

    return dash.no_update


@app.callback(
    [Output('sidebar-container', 'style'),
     Output('sidebar-collapsed', 'style'),
     Output('sidebar-expanded', 'style')] +
    [Output(f'sidebar-item-{item["nav_id"]}', 'style') for item in ALL_TAB_ITEMS] +
    [Output(f'collapsed-item-{item["nav_id"]}', 'style') for item in ALL_TAB_ITEMS],
    Input('sidebar-state', 'data')
)
def sync_sidebar_layout(state):
    state = state or {'collapsed': False, 'active_tab': DEFAULT_TAB, 'active_nav': DEFAULT_NAV}
    collapsed = state.get('collapsed', False)
    active_nav = state.get('active_nav', DEFAULT_NAV)

    expanded_style = {'display': 'none'} if collapsed else {
        'display': 'flex', 'flexDirection': 'column', 'height': '100%'
    }
    collapsed_style = {
        'display': 'flex' if collapsed else 'none',
        'flexDirection': 'column',
        'padding': '0 0 8px 0',
        'height': '100%'
    }

    return (
        [sidebar_container_style(collapsed), collapsed_style, expanded_style] +
        [sidebar_item_style(item['nav_id'] == active_nav) for item in ALL_TAB_ITEMS] +
        [collapsed_item_style(item['nav_id'] == active_nav) for item in ALL_TAB_ITEMS]
    )


@app.callback(
    [Output(f'group-items-{group["group_id"]}', 'style') for group in SIDEBAR_GROUPS] +
    [Output(f'group-arrow-{group["group_id"]}', 'style') for group in SIDEBAR_GROUPS] +
    [Output(f'group-arrow-{group["group_id"]}', 'children') for group in SIDEBAR_GROUPS] +
    [Output('group-states', 'data')],
    [Input(f'group-header-{group["group_id"]}', 'n_clicks') for group in SIDEBAR_GROUPS],
    State('group-states', 'data'),
    prevent_initial_call=True
)
def toggle_group(*args):
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update] * (len(SIDEBAR_GROUPS) * 3 + 1)

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    group_states = args[-1]

    for group in SIDEBAR_GROUPS:
        if trigger_id == f'group-header-{group["group_id"]}':
            group_states[group['group_id']] = not group_states.get(group['group_id'], False)
            break

    item_styles = []
    arrow_styles = []
    arrow_labels = []
    for group in SIDEBAR_GROUPS:
        is_expanded = group_states.get(group['group_id'], False)
        item_styles.append(group_items_style(is_expanded))
        arrow_styles.append(group_arrow_style(is_expanded))
        arrow_labels.append('v' if is_expanded else '>')
    return item_styles + arrow_styles + arrow_labels + [group_states]


# ═══════════════════════════════════════════════════════════════════════
# Tab Renderer
# ═══════════════════════════════════════════════════════════════════════
def render_tab_content(tab, metric, country, compare_list):
    if tab == 'tab-pipeline':   return build_pipeline()
    if tab == 'tab-overview':   return build_overview(metric)
    if tab == 'tab-global':     return build_global(metric, compare_list)
    if tab == 'tab-compare':    return build_compare(metric, country, compare_list)
    if tab == 'tab-deepdive':   return build_deepdive(metric, country)
    if tab == 'tab-rankings':   return build_rankings(metric)
    if tab == 'tab-correlation': return build_correlation(metric)
    if tab == 'tab-continent':  return build_continent(metric)
    if tab == 'tab-ma':         return build_ma_tab(metric, country)
    if tab == 'tab-anomaly':    return build_anomaly_tab(metric, country)
    if tab == 'tab-fatality':   return build_fatality_tab(country)
    if tab == 'tab-lag':        return build_lag_tab(country)
    if tab == 'tab-cluster':    return build_cluster_tab()
    return html.Div()


@app.callback(
    Output('tab-content', 'children'),
    [Input('sidebar-state', 'data'),
     Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def render_active_tab(sidebar_state, metric, country, compare_list):
    tab = (sidebar_state or {}).get('active_tab', DEFAULT_TAB)
    if tab not in ALL_TAB_VALUES:
        tab = DEFAULT_TAB
    return render_tab_content(tab, metric, country, compare_list)


# ═══════════════════════════════════════════════════════════════════════
# Original Tab Builders (condensed)
# ═══════════════════════════════════════════════════════════════════════

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


def build_pipeline():
    summary = PIPELINE_SUMMARY
    cols_info = PIPELINE_COLS_INFO

    return html.Div([
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


def build_overview(metric):
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    stats = descriptive_stats(df, metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]

    country_summary = latest[['country', 'continent', 'total_cases', 'total_deaths',
                              'people_fully_vaccinated_per_hundred',
                              'new_cases_smoothed', 'new_deaths_smoothed']].copy()
    country_summary = country_summary.fillna(0)
    country_summary['total_cases'] = country_summary['total_cases'].astype(int)
    country_summary['total_deaths'] = country_summary['total_deaths'].astype(int)
    country_summary = country_summary.sort_values('total_cases', ascending=False)

    return html.Div([
        html.Div([
            stat_card('Total Countries', f'{len(countries)}', ''),
            stat_card('Date Range', f'{date_min.date()}', f'to {date_max.date()}'),
            stat_card('Total Rows', f'{len(df):,}', 'data points'),
            stat_card('Global Total', f'{latest[metric].sum():,.0f}', metric_label),
        ], style={'display': 'flex', 'gap': '12px', 'marginBottom': '16px', 'flexWrap': 'wrap'}),
        html.Div([
            html.Div('Key Metrics', style={'fontSize': '14px', 'fontWeight': '600',
                     'color': '#444', 'marginBottom': '10px',
                     'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
            html.Div(id='overview-key-metrics', children=[
                html.Div([
                    html.Div('Total Cases', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{int(df["total_cases"].max()):,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#2a4d8f'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '8px'}),
                html.Div([
                    html.Div('Total Deaths', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{int(df["total_deaths"].max()):,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#b91f1f'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '8px'}),
                html.Div([
                    html.Div('Fully Vaccinated', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{int(df["people_fully_vaccinated"].max()):,}', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#1a7a3a'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '8px'}),
                html.Div([
                    html.Div('Vaccination Rate', style={'fontSize': '11px', 'color': '#888'}),
                    html.Div(f'{round(df["people_fully_vaccinated_per_hundred"].max(), 1)}%', style={'fontSize': '16px', 'fontWeight': '700', 'color': '#1a7a3a'})
                ], style={'flex': '1', 'textAlign': 'center', 'padding': '8px'}),
            ], style={'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'})
        ], style={'background': '#fff', 'padding': '12px 16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '12px'}),
        html.Div([
            html.Div([
                html.Span('Country Summary', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#444'}),
                html.Div([
                    html.Span('Filter by country:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
                    dcc.Dropdown(
                        id='overview-country-filter',
                        options=[{'label': 'All Countries (summary)', 'value': 'ALL'}] +
                                [{'label': c, 'value': c} for c in countries],
                        value='ALL', clearable=False,
                        style={'width': '200px', 'fontSize': '13px', 'display': 'inline-block'}
                    ),
                    html.Span('Date range:', style={'fontSize': '12px', 'color': '#666', 'marginLeft': '12px', 'marginRight': '6px'}),
                    dcc.DatePickerRange(
                        id='overview-date-range',
                        min_date_allowed=date_min.date(),
                        max_date_allowed=date_max.date(),
                        start_date=date_min.date(),
                        end_date=date_max.date()
                    ),
                ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '8px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between',
                      'marginBottom': '8px', 'flexWrap': 'wrap'}),
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


def build_global(metric, compare_list):
    """Global Trends tab: map + timeline + trend."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)

    return html.Div([
        html.Div([
            dcc.Graph(
                id='global-map',
                style={'height': '620px', 'width': '100%'},
                config=PLOTLY_CONFIG
            )
        ], style={'width': '100%', 'marginBottom': '10px'}),

        html.Div([
            html.Div('Global Statistics', style={'fontSize': '13px', 'fontWeight': '600',
                     'color': '#555', 'marginBottom': '8px'}),
            html.Div(id='global-stats', style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'})
        ], style={'marginBottom': '12px'}),

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

        html.Div([
            dcc.Graph(id='global-trend-chart', style={'height': '300px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '12px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_compare(metric, country, compare_list):
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
                style={'height': '450px'}, config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_deepdive(metric, country):
    """Country Deep Dive tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    vacc_metric = 'people_fully_vaccinated_per_hundred'
    return html.Div([
        html.Div(f'Deep Dive: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Div(f'{metric_label} vs Vaccination Rate',
                    style={'fontSize': '13px', 'fontWeight': '600', 'color': '#555',
                           'marginBottom': '6px'}),
            dcc.Graph(
                figure=plot_dual_axis(df, country, metric, vacc_metric),
                style={'height': '480px', 'width': '100%'}, config=PLOTLY_CONFIG
            )
        ], style={'marginBottom': '18px'}),
        html.Div([
            html.Div('Growth Rate Analysis',
                    style={'fontSize': '13px', 'fontWeight': '600', 'color': '#555',
                           'marginBottom': '6px'}),
            dcc.Graph(
                figure=plot_growth_rate(df, country, metric),
                style={'height': '560px', 'width': '100%'}, config=PLOTLY_CONFIG
            )
        ])
    ], style={'background': '#fff', 'padding': '20px', 'borderRadius': '4px',
              'border': '1px solid #e8e8e8'})


def build_rankings(metric):
    """Rankings tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    top_df = top_countries(df, metric=metric, n=20)
    return html.Div([
        html.Div([
            dcc.Graph(
                figure=plot_bar_chart(top_df, x_col='country', y_col=metric,
                                     title=f'Top 20 — {metric_label}',
                                     color_col='continent'),
                style={'height': '550px'}, config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def metric_label(metric):
    return next((m['label'] for m in CORRELATION_METRICS if m['id'] == metric), metric)


def default_correlation_y(metric):
    if 'case' in metric.lower():
        return 'new_deaths_smoothed'
    if 'death' in metric.lower():
        return 'new_cases_smoothed'
    if 'vaccin' in metric.lower():
        return 'new_cases_smoothed_per_million'
    if metric == 'gdp_per_capita':
        return 'total_deaths_per_million'
    if metric in ('median_age', 'life_expectancy', 'human_development_index'):
        return 'total_cases_per_million'
    return 'new_cases_smoothed'


def add_correlation_groups(latest):
    plot_df = latest.copy()

    plot_df['population_group'] = pd.cut(
        plot_df['population'],
        bins=[0, 1_000_000, 10_000_000, 50_000_000, 200_000_000, np.inf],
        labels=['<1M', '1M-10M', '10M-50M', '50M-200M', '200M+']
    )
    plot_df['gdp_group'] = pd.cut(
        plot_df['gdp_per_capita'],
        bins=[0, 5_000, 15_000, 35_000, np.inf],
        labels=['Low GDP', 'Lower-middle GDP', 'Upper-middle GDP', 'High GDP']
    )
    plot_df['age_group'] = pd.cut(
        plot_df['median_age'],
        bins=[0, 25, 35, 45, np.inf],
        labels=['Young', 'Mid-age', 'Older', 'Oldest']
    )
    plot_df['hdi_group'] = pd.cut(
        plot_df['human_development_index'],
        bins=[0, 0.55, 0.7, 0.8, np.inf],
        labels=['Low HDI', 'Medium HDI', 'High HDI', 'Very high HDI']
    )
    plot_df['life_expectancy_group'] = pd.cut(
        plot_df['life_expectancy'],
        bins=[0, 65, 75, 82, np.inf],
        labels=['<65', '65-75', '75-82', '82+']
    )
    return plot_df


def make_correlation_figure(x_metric, y_metric, color_col):
    latest = df.loc[df.groupby('country')['date'].idxmax()].copy()
    latest = add_correlation_groups(latest)

    required = [x_metric, y_metric]
    if color_col:
        required.append(color_col)
    plot_df = latest.dropna(subset=required)

    return plot_scatter(
        plot_df,
        x_col=x_metric,
        y_col=y_metric,
        color_col=color_col,
        title=f'{metric_label(x_metric)} vs {metric_label(y_metric)}'
    )


def build_correlation(metric):
    """Correlation tab."""
    compare = default_correlation_y(metric)
    return html.Div([
        html.Div([
            html.Div([
                html.Span('X Metric:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
                dcc.Dropdown(
                    id='corr-x',
                    options=[{'label': m['label'], 'value': m['id']} for m in CORRELATION_METRICS if m['id'] in df.columns],
                    value=metric if metric in df.columns else 'new_cases_smoothed',
                    clearable=False,
                    style={'width': '260px', 'fontSize': '13px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Div([
                html.Span('Y Metric:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
                dcc.Dropdown(
                    id='corr-y',
                    options=[{'label': m['label'], 'value': m['id']} for m in CORRELATION_METRICS if m['id'] in df.columns],
                    value=compare,
                    clearable=False,
                    style={'width': '260px', 'fontSize': '13px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
            html.Div([
                html.Span('Color by:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
                dcc.Dropdown(
                    id='corr-color',
                    options=CORRELATION_COLOR_OPTIONS,
                    value='continent',
                    clearable=False,
                    style={'width': '220px', 'fontSize': '13px'}
                )
            ], style={'display': 'flex', 'alignItems': 'center'}),
        ], style={'display': 'flex', 'gap': '16px', 'alignItems': 'center',
                  'flexWrap': 'wrap', 'marginBottom': '12px'}),
        html.Div([
            dcc.Graph(
                id='correlation-chart',
                figure=make_correlation_figure(metric, compare, 'continent'),
                style={'height': '560px'}, config=PLOTLY_CONFIG
            )
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_continent(metric):
    """Continent Analysis tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
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


# ═══════════════════════════════════════════════════════════════════════
# Advanced Tab Builders
# ═══════════════════════════════════════════════════════════════════════

def empty_figure(message='No data available'):
    fig = go.Figure()
    fig.add_annotation(
        text=message, x=0.5, y=0.5, xref='paper', yref='paper',
        showarrow=False, font={'size': 14, 'color': '#666'}
    )
    fig.update_layout(template='plotly_white')
    return fig


def moving_average_base_series(country, metric):
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date').dropna(subset=[metric])
    if country_df.empty:
        return country_df, metric, metric_label(metric), False

    base_metric = metric
    value_label = metric_label(metric)
    is_derived = False

    if metric.endswith('_smoothed'):
        candidate = metric.replace('_smoothed', '')
        if candidate in df.columns:
            base_metric = candidate
            country_df = df[df['country'] == country][['date', base_metric]].copy()
            country_df = country_df.sort_values('date').dropna(subset=[base_metric])
            value_label = metric_label(base_metric)
    elif metric.startswith('total_'):
        country_df['daily_change'] = country_df[metric].diff().clip(lower=0)
        base_metric = 'daily_change'
        value_label = f'Daily Change in {metric_label(metric)}'
        is_derived = True

    country_df = country_df[['date', base_metric]].copy()
    for window in [7, 14, 30]:
        country_df[f'ma_{window}d'] = country_df[base_metric].rolling(window=window, min_periods=1).mean()
    country_df['ma_diff_7_30'] = country_df['ma_7d'] - country_df['ma_30d']
    return country_df, base_metric, value_label, is_derived


def ma_range_label(view_range):
    return next((option['label'] for option in MA_PERIOD_OPTIONS if option['value'] == view_range), 'Full Dataset')


def ma_range_bounds(ma_df, view_range):
    if ma_df.empty:
        return None, None

    data_min = ma_df['date'].min()
    data_max = ma_df['date'].max()
    period_bounds = {
        '2020_initial': (pd.Timestamp('2020-01-01'), pd.Timestamp('2020-12-31')),
        '2021_delta': (pd.Timestamp('2021-01-01'), pd.Timestamp('2021-12-31')),
        '2022_omicron': (pd.Timestamp('2022-01-01'), pd.Timestamp('2022-12-31')),
        '2023_post_peak': (pd.Timestamp('2023-01-01'), data_max),
        'latest_180': (data_max - pd.Timedelta(days=179), data_max),
    }

    start, end = period_bounds.get(view_range, (data_min, data_max))
    return max(start, data_min), min(end, data_max)


def filter_ma_range(ma_df, view_range):
    if ma_df.empty or view_range == 'all':
        return ma_df
    start, end = ma_range_bounds(ma_df, view_range)
    if start is None or end is None:
        return ma_df
    return ma_df[(ma_df['date'] >= start) & (ma_df['date'] <= end)]


def style_ma_figure(fig, title, height=360):
    fig.update_layout(
        title=title,
        template='plotly_white',
        hovermode='x unified',
        height=height,
        margin={'l': 60, 'r': 24, 't': 54, 'b': 46},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1}
    )
    fig.update_xaxes(gridcolor='#e8e8e8')
    fig.update_yaxes(gridcolor='#e8e8e8')
    return fig


def ma_trend_summary(latest):
    ma_7 = latest['ma_7d']
    ma_30 = latest['ma_30d']
    diff = latest['ma_diff_7_30']

    if pd.isna(ma_7) or pd.isna(ma_30):
        return 'Stable', 'insufficient data', diff
    if ma_30 == 0:
        if ma_7 > 0:
            return 'Rising', '30-day baseline is zero', diff
        return 'Stable', 'both averages are zero', diff
    if ma_7 > ma_30 * 1.05:
        status = 'Rising'
    elif ma_7 < ma_30 * 0.95:
        status = 'Falling'
    else:
        status = 'Stable'
    pct_diff = (diff / ma_30) * 100
    return status, f'{pct_diff:+.1f}% vs 30-day MA', diff


def latest_active_ma_row(ma_df, base_metric):
    raw_nonzero_df = ma_df[ma_df[base_metric].fillna(0) != 0]
    if not raw_nonzero_df.empty:
        return raw_nonzero_df.iloc[-1]
    ma_nonzero_df = ma_df[ma_df['ma_7d'].fillna(0) != 0]
    if not ma_nonzero_df.empty:
        return ma_nonzero_df.iloc[-1]
    return ma_df.iloc[-1]


def make_moving_average_outputs(country, metric, view_range='all', show_raw=True):
    ma_df, base_metric, value_label, is_derived = moving_average_base_series(country, metric)
    if ma_df.empty:
        empty = empty_figure('No moving average data available')
        return empty, empty, empty, []

    plot_df = filter_ma_range(ma_df, view_range)
    if plot_df.empty:
        plot_df = ma_df

    range_label = ma_range_label(view_range)
    main_fig = go.Figure()
    if show_raw:
        main_fig.add_trace(go.Scatter(
            x=plot_df['date'], y=plot_df[base_metric], mode='lines',
            name='Raw daily value' if not is_derived else 'Daily change',
            line={'color': 'rgba(120,120,120,0.35)', 'width': 1}
        ))
    main_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['ma_7d'], mode='lines',
                                  name='7-day MA', line={'color': '#2a4d8f', 'width': 1.8}))
    main_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['ma_30d'], mode='lines',
                                  name='30-day MA', line={'color': '#b91f1f', 'width': 1.8}))
    style_ma_figure(main_fig, f'Trend Overview: {value_label} - {country} ({range_label})', height=420)

    window_fig = go.Figure()
    for window, color in [(7, '#2a4d8f'), (14, '#1a7a3a'), (30, '#b91f1f')]:
        window_fig.add_trace(go.Scatter(
            x=plot_df['date'], y=plot_df[f'ma_{window}d'], mode='lines',
            name=f'{window}-day MA', line={'color': color, 'width': 1.8}
        ))
    style_ma_figure(window_fig, f'Window Comparison: {range_label}', height=340)

    diff_fig = go.Figure()
    diff_fig.add_trace(go.Bar(
        x=plot_df['date'], y=plot_df['ma_diff_7_30'],
        name='7-day minus 30-day',
        marker_color=np.where(plot_df['ma_diff_7_30'] >= 0, '#b91f1f', '#2a4d8f')
    ))
    diff_fig.add_hline(y=0, line_width=1, line_dash='dash', line_color='#777')
    style_ma_figure(diff_fig, f'Momentum: 7-day MA minus 30-day MA ({range_label})', height=300)

    selected_valid_df = plot_df.dropna(subset=[base_metric, 'ma_7d', 'ma_30d'])
    if selected_valid_df.empty:
        selected_valid_df = ma_df.dropna(subset=[base_metric, 'ma_7d', 'ma_30d'])
    latest = latest_active_ma_row(selected_valid_df, base_metric)
    peak_source = selected_valid_df
    peak = peak_source.loc[peak_source['ma_7d'].idxmax()]
    days_since_peak = max((latest['date'] - peak['date']).days, 0)
    trend_status, trend_detail, diff = ma_trend_summary(latest)
    stats_cards = [
        stat_card('Latest Raw', f'{latest[base_metric]:,.0f}', value_label),
        stat_card('Latest 7-day MA', f'{latest["ma_7d"]:,.0f}', 'short-term trend'),
        stat_card('Latest 30-day MA', f'{latest["ma_30d"]:,.0f}', 'long-term baseline'),
        stat_card('7 vs 30 Difference', f'{diff:,.0f}', trend_detail),
        stat_card('Peak 7-day MA', f'{peak["ma_7d"]:,.0f}', str(peak['date'].date())),
        stat_card('Trend Status', trend_status, f'{days_since_peak} days since peak'),
    ]
    return main_fig, window_fig, diff_fig, stats_cards


def make_anomaly_figure(country, metric, window=14, threshold=2.0):
    anomaly_df = anomaly_detection(df, country, metric, threshold=threshold, window=window)
    if anomaly_df.empty:
        return empty_figure('No anomaly data available')

    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    anomalies = anomaly_df[anomaly_df['is_anomaly']]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=anomaly_df['date'], y=anomaly_df[metric], mode='lines', name=metric_label))
    fig.add_trace(go.Scatter(x=anomaly_df['date'], y=anomaly_df['upper_bound'], mode='lines',
                             name='Upper bound', line={'dash': 'dash', 'color': '#d9534f'}))
    fig.add_trace(go.Scatter(x=anomaly_df['date'], y=anomaly_df['lower_bound'], mode='lines',
                             name='Lower bound', line={'dash': 'dash', 'color': '#d9534f'}))
    fig.add_trace(go.Scatter(x=anomalies['date'], y=anomalies[metric], mode='markers',
                             name='Anomalies', marker={'size': 8, 'color': '#d9534f'}))
    fig.update_layout(
        title=f'{metric_label} Anomalies - {country}',
        template='plotly_white',
        margin={'l': 40, 'r': 20, 't': 50, 'b': 40},
        legend={'orientation': 'h'}
    )
    return fig


def make_fatality_outputs(country):
    fatality_df = fatality_trend(df, country)
    if fatality_df.empty:
        return empty_figure('No fatality data available'), []

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fatality_df['date'], y=fatality_df['cfr'], mode='lines',
                             name='CFR', line={'color': '#b91f1f'}))
    fig.add_trace(go.Scatter(x=fatality_df['date'], y=fatality_df['cfr_14d_ma'], mode='lines',
                             name='14-day MA', line={'color': '#2a4d8f'}))
    fig.update_layout(
        title=f'Case Fatality Rate - {country}',
        yaxis_title='CFR (%)',
        template='plotly_white',
        margin={'l': 40, 'r': 20, 't': 50, 'b': 40},
        legend={'orientation': 'h'}
    )

    latest = fatality_df.iloc[-1]
    peak = fatality_df.loc[fatality_df['cfr'].idxmax()]
    recent = fatality_df.tail(30)['cfr'].mean()
    stats_cards = [
        stat_card('CFR (Latest)', f'{latest["cfr"]:.2f}%', 'latest record'),
        stat_card('Total Cases', f'{latest["total_cases"]:,.0f}', ''),
        stat_card('Total Deaths', f'{latest["total_deaths"]:,.0f}', ''),
        stat_card('Peak CFR', f'{peak["cfr"]:.2f}%', str(peak['date'].date())),
        stat_card('Recent CFR', f'{recent:.2f}%', 'last 30 days avg'),
    ]
    return fig, stats_cards


def make_lag_figure(country, x_metric, y_metric):
    lag_df = cross_lag_correlation(df, country, x_metric, y_metric, max_lag=60)
    if lag_df.empty:
        return empty_figure('No lead-lag data available')

    x_label = next((m['label'] for m in METRICS if m['id'] == x_metric), x_metric)
    y_label = next((m['label'] for m in METRICS if m['id'] == y_metric), y_metric)
    fig = px.bar(lag_df, x='lag_days', y='correlation', title=f'{x_label} vs {y_label} - {country}')
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Lag days',
        yaxis_title='Correlation',
        margin={'l': 40, 'r': 20, 't': 50, 'b': 40}
    )
    return fig


def get_cluster_df(k):
    if k not in CLUSTER_CACHE:
        if CLUSTER_BASE_DF.empty:
            CLUSTER_CACHE[k] = CLUSTER_BASE_DF.copy()
        else:
            clust_df = CLUSTER_BASE_DF.copy()
            scaler = StandardScaler()
            scaled = scaler.fit_transform(clust_df[CLUSTER_FEATURES].fillna(0))
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clust_df['cluster'] = kmeans.fit_predict(scaled)
            CLUSTER_CACHE[k] = clust_df
    return CLUSTER_CACHE[k]


for _cluster_k in range(3, 8):
    get_cluster_df(_cluster_k)


def make_cluster_outputs(k):
    cluster_df = get_cluster_df(k)
    if cluster_df.empty:
        return empty_figure('No clustering data available'), []

    fig = px.scatter(
        cluster_df,
        x='total_cases_per_million',
        y='total_deaths_per_million',
        color=cluster_df['cluster'].astype(str),
        hover_name='country',
        size='population',
        title='Country Clusters'
    )
    fig.update_layout(
        template='plotly_white',
        xaxis_title='Total cases per million',
        yaxis_title='Total deaths per million',
        margin={'l': 40, 'r': 20, 't': 50, 'b': 40},
        legend_title='Cluster'
    )

    summary_cards = []
    for label, group in cluster_df.groupby('cluster'):
        summary_cards.append(
            html.Div([
                html.Div(f'Cluster {label}', style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555'}),
                html.Div(f'{len(group)} countries', style={'fontSize': '14px', 'fontWeight': '700', 'color': '#222'}),
                html.Div(f'Cases: {group["total_cases_per_million"].mean():,.0f}', style={'fontSize': '11px', 'color': '#888'}),
                html.Div(f'Deaths: {group["total_deaths_per_million"].mean():,.0f}', style={'fontSize': '11px', 'color': '#888'}),
                html.Div(f'Vaccination: {group["people_fully_vaccinated_per_hundred"].mean():.1f}%', style={'fontSize': '11px', 'color': '#888'}),
            ], style={'flex': '1', 'minWidth': '150px', 'background': '#f9f9f9', 'padding': '12px',
                      'borderRadius': '4px', 'border': '1px solid #e8e8e8'})
        )
    return fig, summary_cards


def build_ma_tab(metric, country):
    """Moving Average tab."""
    main_fig, recent_fig, diff_fig, stats_cards = make_moving_average_outputs(country, metric)
    return html.Div([
        html.Div(f'Moving Average Trend Analysis: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Div([
                html.Span('View Range:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
                dcc.Dropdown(
                    id='ma-range',
                    options=MA_PERIOD_OPTIONS,
                    value='all',
                    clearable=False,
                    style={'width': '260px', 'fontSize': '13px', 'display': 'inline-block'}
                ),
                dcc.Checklist(
                    id='ma-show-raw',
                    options=[{'label': 'Show Raw', 'value': 'raw'}],
                    value=['raw'],
                    inputStyle={'marginRight': '6px'},
                    labelStyle={'fontSize': '12px', 'color': '#666', 'marginLeft': '16px'}
                ),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '12px'}),
            html.Div(id='ma-stats', children=stats_cards,
                     style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap', 'marginBottom': '12px'}),
            dcc.Graph(id='ma-main-chart', figure=main_fig, style={'height': '420px'}, config=PLOTLY_CONFIG),
            dcc.Graph(id='ma-recent-chart', figure=recent_fig, style={'height': '340px'}, config=PLOTLY_CONFIG),
            dcc.Graph(id='ma-diff-chart', figure=diff_fig, style={'height': '300px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_anomaly_tab(metric, country):
    """Anomaly Detection tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return html.Div([
        html.Div(f'Anomaly Detection: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Span('Window:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='anomaly-window', options=[{'label': f'{w} days', 'value': w} for w in [7, 14, 30]],
                         value=14, clearable=False, style={'width': '120px', 'fontSize': '13px', 'display': 'inline-block'}),
            html.Span('Threshold:', style={'fontSize': '12px', 'color': '#666', 'marginLeft': '12px', 'marginRight': '6px'}),
            dcc.Dropdown(id='anomaly-threshold',
                         options=[{'label': f'{t}σ', 'value': t} for t in [1.5, 2.0, 2.5, 3.0]],
                         value=2.0, clearable=False, style={'width': '100px', 'fontSize': '13px', 'display': 'inline-block'}),
        ], style={'marginBottom': '12px'}),
        html.Div([
            dcc.Graph(id='anomaly-chart', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_fatality_tab(country):
    """Fatality Analysis tab."""
    return html.Div([
        html.Div(f'Fatality Analysis: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            dcc.Graph(id='fatality-chart', style={'height': '400px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '12px'}),
        html.Div(id='fatality-stats', style={'background': '#fff', 'padding': '16px',
                  'borderRadius': '4px', 'border': '1px solid #e8e8e8'})
    ])


def build_lag_tab(country):
    """Lead-Lag Correlation tab."""
    return html.Div([
        html.Div(f'Lead-Lag Analysis: {country}', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Span('X (leading):', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='lag-x', options=[{'label': m['label'], 'value': m['id']} for m in METRICS],
                         value='new_cases_smoothed', clearable=False,
                         style={'width': '200px', 'fontSize': '13px', 'display': 'inline-block'}),
            html.Span('Y (lagging):', style={'fontSize': '12px', 'color': '#666', 'marginLeft': '12px', 'marginRight': '6px'}),
            dcc.Dropdown(id='lag-y', options=[{'label': m['label'], 'value': m['id']} for m in METRICS],
                         value='new_deaths_smoothed', clearable=False,
                         style={'width': '200px', 'fontSize': '13px', 'display': 'inline-block'}),
        ], style={'marginBottom': '12px'}),
        html.Div([
            dcc.Graph(id='lag-chart', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8'})
    ])


def build_cluster_tab():
    """Clustering tab."""
    return html.Div([
        html.Div('Country Clustering', style={'fontSize': '15px', 'fontWeight': '600',
                 'color': '#444', 'marginBottom': '12px',
                 'borderBottom': '1px solid #e8e8e8', 'paddingBottom': '8px'}),
        html.Div([
            html.Span('Number of clusters:', style={'fontSize': '12px', 'color': '#666', 'marginRight': '6px'}),
            dcc.Dropdown(id='cluster-n', options=[{'label': f'k={k}', 'value': k} for k in range(3, 8)],
                         value=4, clearable=False, style={'width': '100px', 'fontSize': '13px', 'display': 'inline-block'}),
        ], style={'marginBottom': '12px'}),
        html.Div([
            dcc.Graph(id='cluster-scatter', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ], style={'background': '#fff', 'padding': '16px', 'borderRadius': '4px',
                  'border': '1px solid #e8e8e8', 'marginBottom': '12px'}),
        html.Div(id='cluster-summary', style={'background': '#fff', 'padding': '16px',
                  'borderRadius': '4px', 'border': '1px solid #e8e8e8'})
    ])


# ═══════════════════════════════════════════════════════════════════════
# Interactive Callbacks (Global Trends, Advanced tabs, etc.)
# ═══════════════════════════════════════════════════════════════════════

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


# Correlation tab callback
@app.callback(
    Output('correlation-chart', 'figure'),
    [Input('corr-x', 'value'),
     Input('corr-y', 'value'),
     Input('corr-color', 'value')]
)
def update_correlation_chart(x_metric, y_metric, color_col):
    return make_correlation_figure(x_metric, y_metric, color_col)


# Moving Average tab callback
@app.callback(
    [Output('ma-main-chart', 'figure'),
     Output('ma-recent-chart', 'figure'),
     Output('ma-diff-chart', 'figure'),
     Output('ma-stats', 'children')],
    [Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('ma-range', 'value'),
     Input('ma-show-raw', 'value')]
)
def update_moving_average(metric, country, view_range, show_raw_values):
    show_raw = bool(show_raw_values and 'raw' in show_raw_values)
    main_fig, recent_fig, diff_fig, stats_cards = make_moving_average_outputs(
        country, metric, view_range=view_range, show_raw=show_raw
    )
    return main_fig, recent_fig, diff_fig, stats_cards


# Anomaly tab callback
@app.callback(
    Output('anomaly-chart', 'figure'),
    [Input('global-metric', 'value'),
     Input('global-country', 'value'),
     Input('anomaly-window', 'value'),
     Input('anomaly-threshold', 'value')]
)
def update_anomaly(metric, country, window, threshold):
    return make_anomaly_figure(country, metric, window=window, threshold=threshold)


# Fatality tab callback
@app.callback(
    [Output('fatality-chart', 'figure'),
     Output('fatality-stats', 'children')],
    [Input('global-country', 'value')]
)
def update_fatality(country):
    fig, stats_cards = make_fatality_outputs(country)
    return fig, html.Div(stats_cards, style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'})


# Lead-Lag tab callback
@app.callback(
    Output('lag-chart', 'figure'),
    [Input('global-country', 'value'),
     Input('lag-x', 'value'),
     Input('lag-y', 'value')]
)
def update_lag(country, x_metric, y_metric):
    return make_lag_figure(country, x_metric, y_metric)


# Clustering tab callback
@app.callback(
    [Output('cluster-scatter', 'figure'),
     Output('cluster-summary', 'children')],
    [Input('cluster-n', 'value')]
)
def update_cluster(k):
    fig, summary_cards = make_cluster_outputs(k)
    return fig, html.Div(summary_cards, style={'display': 'flex', 'gap': '12px', 'flexWrap': 'wrap'})


# Overview tab: country filter + date range
@app.callback(
    Output('data-table', 'data'),
    [Input('overview-country-filter', 'value'),
     Input('overview-date-range', 'start_date'),
     Input('overview-date-range', 'end_date')]
)
def update_overview_table(country_filter, start_date, end_date):
    filtered = df.copy()
    if country_filter and country_filter != 'ALL':
        filtered = filtered[filtered['country'] == country_filter]
    if start_date:
        filtered = filtered[filtered['date'] >= start_date]
    if end_date:
        filtered = filtered[filtered['date'] <= end_date]
    return filtered.head(100).to_dict('records')


# ═══════════════════════════════════════════════════════════════════════
# Exit button: close the browser tab
# ═══════════════════════════════════════════════════════════════════════
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


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Starting COVID-19 Data Explorer — Extended Edition...")
    print(f"Open http://127.0.0.1:8051 in your browser")
    app.run(debug=False, host='127.0.0.1', port=8051)
