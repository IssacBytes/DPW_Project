"""
COVID-19 Data Analysis Platform
Adds advanced analysis tabs on top of the original 8.
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
from plotly.subplots import make_subplots
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
from src.start_page import build_start_page

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
# Dashboard Design Tokens
# ═══════════════════════════════════════════════════════════════════════

FONT_FAMILY = "'Inter', 'Segoe UI', Arial, sans-serif"

TYPOGRAPHY = {
    'page_title': {'fontFamily': FONT_FAMILY, 'fontSize': '30px', 'fontWeight': '700', 'color': '#111827', 'letterSpacing': '0'},
    'page_subtitle': {'fontFamily': FONT_FAMILY, 'fontSize': '14px', 'fontWeight': '500', 'color': '#6b7280', 'letterSpacing': '0'},
    'section_title': {'fontFamily': FONT_FAMILY, 'fontSize': '20px', 'fontWeight': '650', 'color': '#111827', 'letterSpacing': '0'},
    'section_subtitle': {'fontFamily': FONT_FAMILY, 'fontSize': '14px', 'fontWeight': '400', 'color': '#6b7280', 'letterSpacing': '0'},
    'kpi_number': {'fontFamily': FONT_FAMILY, 'fontSize': '32px', 'fontWeight': '700', 'color': '#17172e', 'fontVariantNumeric': 'tabular-nums', 'letterSpacing': '0'},
    'kpi_label': {'fontFamily': FONT_FAMILY, 'fontSize': '11px', 'fontWeight': '700', 'color': '#7b8190', 'textTransform': 'uppercase', 'letterSpacing': '0'},
    'kpi_subtitle': {'fontFamily': FONT_FAMILY, 'fontSize': '13px', 'fontWeight': '400', 'color': '#9ca3af', 'letterSpacing': '0'},
    'body_text': {'fontFamily': FONT_FAMILY, 'fontSize': '14px', 'fontWeight': '400', 'color': '#4b5563', 'letterSpacing': '0'},
    'control_label': {'fontFamily': FONT_FAMILY, 'fontSize': '11px', 'fontWeight': '700', 'color': '#6b7280', 'textTransform': 'uppercase', 'letterSpacing': '0'},
}

CARD_STYLE = {
    'background': '#ffffff',
    'borderRadius': '12px',
    'boxShadow': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
    'padding': '22px 24px',
    'border': 'none',
}

BG_COLOR = '#f0f2f5'
CONTENT_PADDING = '28px 40px'

DROPDOWN_STYLE = {'width': '240px', 'fontSize': '14px', 'fontFamily': FONT_FAMILY}
DROPDOWN_STYLE_SMALL = {'width': '180px', 'fontSize': '14px', 'fontFamily': FONT_FAMILY}

# Sidebar tokens
SIDEBAR_BG = '#1e1e2e'
SIDEBAR_HOVER = '#2a2a3e'
SIDEBAR_ACTIVE_BG = '#2563eb'
SIDEBAR_ACTIVE_BORDER = '#60a5fa'
SIDEBAR_TEXT = '#c8c8d0'
SIDEBAR_TEXT_MUTED = '#6b6b80'


def card(children=None, style_extra=None, **kwargs):
    """Dashboard card container with consistent styling."""
    base_style = dict(CARD_STYLE)
    if style_extra:
        base_style.update(style_extra)
    existing_class = kwargs.pop('className', '')
    class_name = f'dashboard-card animate-card {existing_class}'.strip()
    return html.Div(children, style=base_style, className=class_name, **kwargs)


def stat_card(label, value, subtitle=''):
    """Modern KPI stat card with clear hierarchy."""
    return html.Div([
        html.Div(label, style=TYPOGRAPHY['kpi_label']),
        html.Div(value, style={
            **TYPOGRAPHY['kpi_number'],
            'lineHeight': '1.08',
            'marginTop': '8px',
            'marginBottom': '8px',
            'whiteSpace': 'nowrap',
            'overflow': 'hidden',
            'textOverflow': 'ellipsis',
        }),
        html.Div(subtitle, style=TYPOGRAPHY['kpi_subtitle']) if subtitle else None
    ], className='stat-card animate-card', style={
        'flex': '1 1 190px', 'minWidth': '190px',
        'background': '#ffffff', 'padding': '20px 24px',
        'borderRadius': '12px', 'border': 'none',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'overflow': 'hidden',
    })


def section_header(title, subtitle=None, subtitle_class=None):
    """Section header with optional subtitle and animation class."""
    children = [html.Div(title, style=TYPOGRAPHY['section_title'])]
    if subtitle:
        children.append(html.Div(subtitle, style={**TYPOGRAPHY['section_subtitle'], 'marginTop': '2px'}, className=subtitle_class or ''))
    return html.Div(children, style={'marginBottom': '16px'})


# ═══════════════════════════════════════════════════════════════════════
# Sidebar Navigation Definition
# ═══════════════════════════════════════════════════════════════════════
SIDEBAR_GROUPS = [
    {
        'icon': 'O',
        'label': 'Overview',
        'group_id': 'group-overview',
        'items': [
            {'label': 'Global Trends', 'nav_id': 'global', 'value': 'tab-global'},
            {'label': 'Summary Statistics', 'nav_id': 'summary', 'value': 'tab-overview'},
            {'label': 'Pandemic Timeline', 'nav_id': 'timeline', 'value': 'tab-pipeline'},
        ]
    },
    {
        'icon': 'C',
        'label': 'Comparison Analysis',
        'group_id': 'group-comparison',
        'items': [
            {'label': 'Country Comparison', 'nav_id': 'country-comparison', 'value': 'tab-compare'},
            {'label': 'Continent Comparison', 'nav_id': 'continent-comparison', 'value': 'tab-continent'},
            {'label': 'Rankings', 'nav_id': 'rankings', 'value': 'tab-rankings'},
        ]
    },
    {
        'icon': 'T',
        'label': 'Trend Analysis',
        'group_id': 'group-trend',
        'items': [
            {'label': 'Time Series', 'nav_id': 'time-series', 'value': 'tab-timeseries'},
            {'label': 'Moving Average', 'nav_id': 'moving-average', 'value': 'tab-ma'},
            {'label': 'Growth Rate', 'nav_id': 'growth-rate', 'value': 'tab-growthrate'},
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
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
    ],
    suppress_callback_exceptions=True,
    title='COVID-19 Data Explorer'
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
        'background': SIDEBAR_BG, 'color': '#fff',
        'width': '64px' if collapsed else '220px',
        'height': '100vh',
        'minHeight': '100vh',
        'position': 'sticky',
        'top': '0',
        'alignSelf': 'flex-start',
        'flexShrink': '0',
        'overflowY': 'auto', 'overflowX': 'hidden',
        'borderRight': '1px solid #2a2a3e',
        'display': 'flex', 'flexDirection': 'column',
        'transition': 'width 0.15s ease'
    }


def sidebar_item_style(active=False):
    return {
        'display': 'block',
        'padding': '7px 14px 7px 38px',
        'fontSize': '12px', 'fontWeight': '500' if not active else '600',
        'cursor': 'pointer',
        'borderRadius': '6px',
        'color': SIDEBAR_TEXT if active else SIDEBAR_TEXT_MUTED,
        'background': SIDEBAR_ACTIVE_BG if active else 'transparent',
        'borderLeft': '3px solid' + (SIDEBAR_ACTIVE_BORDER if active else ' transparent'),
        'marginBottom': '2px',
        'whiteSpace': 'nowrap',
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
        'fontWeight': '700' if active else '500',
        'cursor': 'pointer',
        'borderRadius': '8px',
        'margin': '4px 7px',
        'color': '#fff' if active else SIDEBAR_TEXT_MUTED,
        'background': SIDEBAR_ACTIVE_BG if active else 'transparent',
        'border': '1px solid' + (SIDEBAR_ACTIVE_BORDER if active else ' transparent'),
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
        'color': SIDEBAR_TEXT,
        'borderBottom': '1px solid #2a2a3e',
        'marginBottom': '6px',
        'position': 'sticky',
        'top': '0',
        'background': SIDEBAR_BG,
        'zIndex': '2',
        'userSelect': 'none'
    }


def group_header_style():
    return {
        'display': 'flex', 'alignItems': 'center',
        'padding': '10px 14px',
        'cursor': 'pointer', 'borderRadius': '8px',
        'marginBottom': '2px',
        'userSelect': 'none',
        'color': SIDEBAR_TEXT,
    }


def group_items_style(expanded=False):
    return {
        'display': 'block' if expanded else 'none',
        'paddingLeft': '0',
        'transition': 'none'
    }


# Build sidebar inline
_collapsed_children = [
    html.Div('>', id='sidebar-toggle-collapsed', n_clicks=0,
             style=collapsed_toggle_style(), className='sidebar-toggle-control', title='Expand sidebar')
] + [
    html.Div(
        _item['short'],
        id=f'collapsed-item-{_item["nav_id"]}',
        n_clicks=0,
        style=collapsed_item_style(_item['nav_id'] == DEFAULT_NAV),
        className='sidebar-item-collapsed',
        title=_item['label']
    )
    for _item in ALL_TAB_ITEMS
]

_expanded_children = []
for _gi, _group in enumerate(SIDEBAR_GROUPS):
    _expanded_children.append(
        html.Div(
            [
                html.Span(_group['icon'], style={'marginRight': '10px', 'fontSize': '15px', 'fontWeight': '700', 'color': SIDEBAR_TEXT}),
                html.Span(_group['label'], style={'fontSize': '13px', 'fontWeight': '600', 'color': SIDEBAR_TEXT}),
                html.Span('▼' if _gi == 0 else '▶', id=f'group-arrow-{_group["group_id"]}',
                         style={'marginLeft': 'auto', 'fontSize': '8px', 'color': SIDEBAR_TEXT_MUTED})
            ],
            id=f'group-header-{_group["group_id"]}',
            n_clicks=0,
            style=group_header_style(),
            className='sidebar-group-header'
        )
    )
    _item_divs = []
    for _item in _group['items']:
        _item_divs.append(
            html.Div(
                _item['label'],
                id=f'sidebar-item-{_item["nav_id"]}',
                n_clicks=0,
                style=sidebar_item_style(_item['nav_id'] == DEFAULT_NAV),
                className='sidebar-nav-item'
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
                style={'textAlign': 'center', 'padding': '10px', 'cursor': 'pointer',
                       'fontSize': '12px', 'color': SIDEBAR_TEXT_MUTED,
                       'borderTop': '1px solid #2a2a3e', 'marginTop': 'auto'},
                className='sidebar-toggle-control',
                title='Collapse sidebar')
    ], id='sidebar-expanded',
       style={'display': 'flex', 'flexDirection': 'column', 'height': '100%'})
], id='sidebar-container', style={
    **sidebar_container_style(False)
})

MAIN_APP_LAYOUT = html.Div([
    dcc.Store(id='sidebar-state', data={'collapsed': False, 'active_tab': DEFAULT_TAB, 'active_nav': DEFAULT_NAV}),
    dcc.Store(id='group-states', data={group['group_id']: (gi == 0) for gi, group in enumerate(SIDEBAR_GROUPS)}),

    html.Div([
        _sidebar,

        html.Div([
            # ── Top Header Bar ──
            html.Div([
                html.Div([
                    html.Span('COVID-19 Data Explorer', style=TYPOGRAPHY['page_title']),
                ], style={'display': 'flex', 'alignItems': 'baseline', 'gap': '0', 'minWidth': '0'}),
                html.Button('Exit', id='exit-btn', n_clicks=0,
                           style={'padding': '8px 22px', 'background': '#fff',
                                  'border': '1px solid #d1d5db', 'borderRadius': '8px',
                                  'cursor': 'pointer', 'fontSize': '14px', 'color': '#6b7280',
                                  'fontFamily': FONT_FAMILY},
                           className='ui-button')
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center',
                      'padding': '22px 40px', 'borderBottom': '1px solid #e5e7eb', 'background': '#fff'}),

            # ── Toolbar Card ──
            html.Div([
                html.Div([
                    html.Span('Metric', style=TYPOGRAPHY['control_label']),
                    dcc.Dropdown(id='global-metric', options=[{'label': m['label'], 'value': m['id']} for m in METRICS],
                                 value=DEFAULT_METRIC, clearable=False, style=DROPDOWN_STYLE)
                ], id='global-metric-control', style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
                html.Div([
                    html.Span('Country', style=TYPOGRAPHY['control_label']),
                    dcc.Dropdown(id='global-country', options=[{'label': c, 'value': c} for c in countries],
                                 value=DEFAULT_COUNTRIES[0], clearable=False, style=DROPDOWN_STYLE_SMALL)
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
                html.Div([
                    html.Span('Compare', style=TYPOGRAPHY['control_label']),
                    dcc.Dropdown(id='global-compare', options=[{'label': c, 'value': c} for c in countries],
                                 value=DEFAULT_COUNTRIES[1:4], multi=True, style=DROPDOWN_STYLE)
                ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
            ], style={
                'display': 'flex', 'gap': '30px', 'alignItems': 'flex-end',
                'padding': '18px 40px',
                'background': '#ffffff', 'border': 'none',
                'borderRadius': '0', 'borderBottom': '1px solid #e5e7eb',
                'boxShadow': '0 1px 3px rgba(0,0,0,0.04)'
            }),

            # ── Tab Content ──
            html.Div(id='tab-content', className='tab-content-frame', style={
                'padding': CONTENT_PADDING, 'background': BG_COLOR,
                'minHeight': 'calc(100vh - 140px)'
            }),

            # ── Footer ──
            html.Div([
                html.Div('Data: Our World in Data | Advanced Analysis',
                        style={'textAlign': 'center', 'padding': '10px', 'fontSize': '11px', 'color': '#aaa', 'fontFamily': FONT_FAMILY})
            ])
        ], style={'flex': '1', 'display': 'flex', 'flexDirection': 'column', 'minWidth': '0'})
    ], style={'display': 'flex', 'minHeight': '100vh', 'alignItems': 'stretch'})
], style={'fontFamily': FONT_FAMILY, 'background': BG_COLOR, 'minHeight': '100vh'})

app.layout = html.Div([
    dcc.Store(id='start-page-state', data={'entered': False}),
    html.Div(build_start_page(), id='app-root')
], style={'minHeight': '100vh'})


@app.callback(
    Output('app-root', 'children'),
    Input('start-page-state', 'data')
)
def render_app_root(start_state):
    if start_state and start_state.get('entered'):
        return MAIN_APP_LAYOUT
    return build_start_page()


@app.callback(
    Output('start-page-state', 'data'),
    [Input('start-enter-btn', 'n_clicks'),
     Input('start-nav-btn', 'n_clicks')],
    State('start-page-state', 'data'),
    prevent_initial_call=True
)
def enter_dashboard(hero_clicks, nav_clicks, start_state):
    if (hero_clicks or 0) > 0 or (nav_clicks or 0) > 0:
        state = dict(start_state or {})
        state['entered'] = True
        return state
    return dash.no_update


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
    Output('global-metric-control', 'style'),
    Input('sidebar-state', 'data')
)
def sync_global_metric_visibility(sidebar_state):
    tab = (sidebar_state or {}).get('active_tab', DEFAULT_TAB)
    if tab == 'tab-fatality':
        return {'display': 'none'}
    return {'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}


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
        arrow_styles.append({'marginLeft': 'auto', 'fontSize': '8px', 'color': SIDEBAR_TEXT_MUTED})
        arrow_labels.append('▼' if is_expanded else '▶')
    return item_styles + arrow_styles + arrow_labels + [group_states]


# ═══════════════════════════════════════════════════════════════════════
# Tab Renderer
# ═══════════════════════════════════════════════════════════════════════
def render_tab_content(tab, metric, country, compare_list):
    if tab == 'tab-pipeline':     return build_pipeline()
    if tab == 'tab-overview':     return build_overview(metric)
    if tab == 'tab-global':       return build_global(metric, compare_list)
    if tab == 'tab-compare':      return build_compare(metric, country, compare_list)
    if tab == 'tab-timeseries':   return build_timeseries(metric, country)
    if tab == 'tab-growthrate':   return build_growth_rate_page(metric, country)
    if tab == 'tab-rankings':     return build_rankings(metric)
    if tab == 'tab-correlation':  return build_correlation(metric)
    if tab == 'tab-continent':    return build_continent(metric)
    if tab == 'tab-ma':           return build_ma_tab(metric, country)
    if tab == 'tab-anomaly':      return build_anomaly_tab(metric, country)
    if tab == 'tab-fatality':     return build_fatality_tab(country)
    if tab == 'tab-lag':          return build_lag_tab(country)
    if tab == 'tab-cluster':      return build_cluster_tab()
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
    return html.Div(
        render_tab_content(tab, metric, country, compare_list),
        className='page-shell page-enter',
        key=f'{tab}-{metric}-{country}'
    )


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
        section_header('Pandemic Timeline', 'Data loading, cleaning, and column overview'),
        card([
            html.Div([
                html.Span('Step 1', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#2563eb', 'padding': '2px 10px',
                         'borderRadius': '10px', 'marginRight': '8px', 'fontWeight': '600'}),
                html.Span('Data Loading', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333', 'fontFamily': FONT_FAMILY})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px',
                      'paddingBottom': '10px', 'borderBottom': '1px solid #f0f0f0'}),
            html.Div([
                html.Div([html.Div('Source File', style=TYPOGRAPHY['kpi_label']), html.Div('compact.csv', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'flex': '1'}),
                html.Div([html.Div('Total Rows Loaded', style=TYPOGRAPHY['kpi_label']), html.Div(f'{len(df_raw):,}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'flex': '1'}),
                html.Div([html.Div('Total Columns', style=TYPOGRAPHY['kpi_label']), html.Div(f'{len(df_raw.columns)}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'flex': '1'}),
                html.Div([html.Div('Date Range', style=TYPOGRAPHY['kpi_label']), html.Div(f'{date_min.date()} to {date_max.date()}', style={'fontSize': '14px', 'fontWeight': '600', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'flex': '1'}),
            ], style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'})
        ], style_extra={'marginBottom': '16px'}),

        card([
            html.Div([
                html.Span('Step 2', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#16a34a', 'padding': '2px 10px',
                         'borderRadius': '10px', 'marginRight': '8px', 'fontWeight': '600'}),
                html.Span('Data Cleaning', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333', 'fontFamily': FONT_FAMILY})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px',
                      'paddingBottom': '10px', 'borderBottom': '1px solid #f0f0f0'}),
            html.Div([
                html.Div([html.Div('Cleaning Actions', style=TYPOGRAPHY['kpi_label']),
                    html.Ul([
                        html.Li(f'Removed {summary["duplicates_removed"]:,} duplicate rows', style={'fontSize': '13px', 'color': '#444', 'fontFamily': FONT_FAMILY}),
                        html.Li('Sorted by country and date', style={'fontSize': '13px', 'color': '#444', 'fontFamily': FONT_FAMILY}),
                        html.Li('Forward-filled missing values within each country', style={'fontSize': '13px', 'color': '#444', 'fontFamily': FONT_FAMILY}),
                        html.Li('Backward-filled remaining NaNs at start of series', style={'fontSize': '13px', 'color': '#444', 'fontFamily': FONT_FAMILY}),
                    ], style={'margin': '8px 0 0', 'paddingLeft': '20px'})
                ], style={'flex': '1'}),
                html.Div([
                    html.Div('Cleaning Results', style=TYPOGRAPHY['kpi_label']),
                    html.Div([
                        html.Div([html.Div('Rows Before', style=TYPOGRAPHY['kpi_label']), html.Div(f'{summary["original_rows"]:,}', style={'fontSize': '18px', 'fontWeight': '700', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'textAlign': 'center', 'padding': '12px', 'flex': '1'}),
                        html.Div([html.Div('Rows After', style=TYPOGRAPHY['kpi_label']), html.Div(f'{summary["cleaned_rows"]:,}', style={'fontSize': '18px', 'fontWeight': '700', 'color': '#222', 'fontFamily': FONT_FAMILY})], style={'textAlign': 'center', 'padding': '12px', 'flex': '1'}),
                        html.Div([html.Div('Missing (before)', style=TYPOGRAPHY['kpi_label']), html.Div(f'{summary["missing_before"]:,}', style={'fontSize': '18px', 'fontWeight': '700', 'color': '#dc2626', 'fontFamily': FONT_FAMILY})], style={'textAlign': 'center', 'padding': '12px', 'flex': '1'}),
                        html.Div([html.Div('Missing (after)', style=TYPOGRAPHY['kpi_label']), html.Div(f'{summary["missing_after"]:,}', style={'fontSize': '18px', 'fontWeight': '700', 'color': '#16a34a', 'fontFamily': FONT_FAMILY})], style={'textAlign': 'center', 'padding': '12px', 'flex': '1'}),
                    ], style={'display': 'flex', 'gap': '8px', 'marginTop': '8px'})
                ], style={'flex': '1'})
            ], style={'display': 'flex', 'gap': '24px', 'flexWrap': 'wrap'})
        ], style_extra={'marginBottom': '16px'}),

        card([
            html.Div([
                html.Span('Step 3', style={'fontSize': '11px', 'color': '#fff',
                         'background': '#d97706', 'padding': '2px 10px',
                         'borderRadius': '10px', 'marginRight': '8px', 'fontWeight': '600'}),
                html.Span('Column Overview', style={'fontSize': '15px', 'fontWeight': '600', 'color': '#333', 'fontFamily': FONT_FAMILY})
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '14px',
                      'paddingBottom': '10px', 'borderBottom': '1px solid #f0f0f0'}),
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
                    'fontSize': '12px', 'fontFamily': FONT_FAMILY,
                    'padding': '6px 12px', 'textAlign': 'left'
                },
                style_header={
                    'backgroundColor': '#fafafa', 'fontWeight': '600',
                    'borderBottom': '1px solid #e8e8e8'
                },
                style_data={'borderBottom': '1px solid #f0f0f0'},
                style_cell_conditional=[
                    {'if': {'column_id': 'null_count'}, 'color': '#dc2626' if any(c['null_count'] > 0 for c in cols_info) else '#16a34a'},
                ]
            )
        ])
    ])


def format_overview_table_records(table_df):
    display_df = table_df[['country', 'date', 'continent', 'new_cases_smoothed',
                           'new_deaths_smoothed', 'people_fully_vaccinated_per_hundred']].copy()
    display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d')
    return display_df.to_dict('records')


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
    initial_table = format_overview_table_records(df.head(100))

    return html.Div([
        section_header('Summary Statistics', f'Key metrics overview — {metric_label}'),
        html.Div([
            stat_card('Total Countries', f'{len(countries)}', ''),
            stat_card('Date Range', f'{date_min.date()}', f'to {date_max.date()}'),
            stat_card('Total Rows', f'{len(df):,}', 'data points'),
            stat_card('Global Total', f'{latest[metric].sum():,.0f}', metric_label),
        ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, minmax(190px, 1fr))',
                  'gap': '18px', 'marginBottom': '24px'}),

        card([
            html.Div('Key Metrics', style={**TYPOGRAPHY['section_title'], 'marginBottom': '18px'}),
            html.Div(id='overview-key-metrics', children=[
                html.Div([html.Div('Total Cases', style=TYPOGRAPHY['kpi_label']), html.Div(f'{int(df["total_cases"].max()):,}', style={'fontSize': '22px', 'fontWeight': '700', 'color': '#2563eb', 'fontFamily': FONT_FAMILY, 'fontVariantNumeric': 'tabular-nums'})], style={'textAlign': 'center', 'padding': '10px 12px'}),
                html.Div([html.Div('Total Deaths', style=TYPOGRAPHY['kpi_label']), html.Div(f'{int(df["total_deaths"].max()):,}', style={'fontSize': '22px', 'fontWeight': '700', 'color': '#dc2626', 'fontFamily': FONT_FAMILY, 'fontVariantNumeric': 'tabular-nums'})], style={'textAlign': 'center', 'padding': '10px 12px'}),
                html.Div([html.Div('Fully Vaccinated', style=TYPOGRAPHY['kpi_label']), html.Div(f'{int(df["people_fully_vaccinated"].max()):,}', style={'fontSize': '22px', 'fontWeight': '700', 'color': '#16a34a', 'fontFamily': FONT_FAMILY, 'fontVariantNumeric': 'tabular-nums'})], style={'textAlign': 'center', 'padding': '10px 12px'}),
                html.Div([html.Div('Vaccination Rate', style=TYPOGRAPHY['kpi_label']), html.Div(f'{round(df["people_fully_vaccinated_per_hundred"].max(), 1)}%', style={'fontSize': '22px', 'fontWeight': '700', 'color': '#16a34a', 'fontFamily': FONT_FAMILY, 'fontVariantNumeric': 'tabular-nums'})], style={'textAlign': 'center', 'padding': '10px 12px'}),
            ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(4, minmax(150px, 1fr))', 'gap': '14px'})
        ], style_extra={'marginBottom': '20px'}),

        card([
            html.Div([
                html.Span('Country Summary', style={**TYPOGRAPHY['section_title']}),
                html.Div([
                    html.Span('Filter by country:', style={'fontSize': '13px', 'color': '#6b7280', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                    dcc.Dropdown(id='overview-country-filter', options=[{'label': 'All Countries', 'value': 'ALL'}] + [{'label': c, 'value': c} for c in countries], value='ALL', clearable=False, style={'width': '220px', 'fontSize': '14px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
                    html.Span('Date range:', style={'fontSize': '13px', 'color': '#6b7280', 'marginLeft': '12px', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                    dcc.DatePickerRange(id='overview-date-range', min_date_allowed=date_min.date(), max_date_allowed=date_max.date(), start_date=date_min.date(), end_date=date_max.date()),
                ], style={'display': 'flex', 'alignItems': 'center', 'flexWrap': 'wrap', 'gap': '8px'})
            ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '16px', 'flexWrap': 'wrap', 'gap': '14px'}),
            dash_table.DataTable(
                id='data-table',
                columns=[{'name': c, 'id': c} for c in ['country', 'date', 'continent', 'new_cases_smoothed', 'new_deaths_smoothed', 'people_fully_vaccinated_per_hundred']],
                data=initial_table,
                page_size=10,
                style_table={'overflowX': 'auto'},
                style_cell={'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'padding': '9px 14px',
                            'textAlign': 'left', 'color': '#374151', 'whiteSpace': 'nowrap'},
                style_header={'backgroundColor': '#f9fafb', 'fontWeight': '700',
                              'borderBottom': '1px solid #e5e7eb', 'color': '#374151'},
                style_data={'borderBottom': '1px solid #edf0f3'}
            )
        ])
    ])


def build_global(metric, compare_list):
    """Global Trends tab: map + timeline + trend."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)

    return html.Div([
        section_header('Global Trends', f'{metric_label} — Worldwide map, timeline, and trend analysis'),
        card([
            dcc.Graph(id='global-map', style={'height': '580px', 'width': '100%'}, config=PLOTLY_CONFIG)
        ], style_extra={'marginBottom': '16px'}),

        html.Div([
            html.Div('Global Statistics', style={**TYPOGRAPHY['section_title'], 'marginBottom': '12px'}),
            html.Div(id='global-stats', style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'})
        ], style={'marginBottom': '16px'}),

        card([
            html.Div([
                html.Span(id='global-date-label', children=f'Date: {MONTHLY_DATES[-1]}', style={'fontSize': '13px', 'fontWeight': '600', 'color': '#333', 'fontFamily': FONT_FAMILY, 'minWidth': '150px'}),
                html.Div([dcc.Slider(id='global-slider', min=0, max=len(MONTHLY_DATES)-1, value=len(MONTHLY_DATES)-1, marks={i: MONTHLY_DATES[i][:7] for i in range(0, len(MONTHLY_DATES), max(1, len(MONTHLY_DATES)//6))}, step=1, updatemode='drag')], style={'flex': '1', 'margin': '0 16px'}),
                html.Button('▶ Play', id='global-play', n_clicks=0, className='ui-button', style={'padding': '4px 16px', 'background': '#fff', 'border': '1px solid #ddd', 'borderRadius': '8px', 'cursor': 'pointer', 'fontSize': '12px', 'fontFamily': FONT_FAMILY}),
            ], style={'display': 'flex', 'alignItems': 'center'})
        ], style_extra={'marginBottom': '16px'}),

        card([
            dcc.Graph(id='global-trend-chart', style={'height': '300px'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_compare(metric, country, compare_list):
    """Country Comparison tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    all_c = [country]
    if compare_list:
        all_c.extend([c for c in compare_list if c != country])
    all_c = list(dict.fromkeys(all_c))[:6]
    return html.Div([
        section_header('Country Comparison', f'{metric_label} — Comparing up to 6 countries'),
        card([
            dcc.Graph(
                figure=plot_trend_line(df, all_c, metric, title=f'{metric_label} — Country Comparison'),
                style={'height': '450px'}, config=PLOTLY_CONFIG
            )
        ])
    ])


def format_metric_value(value, metric):
    if pd.isna(value):
        return 'n/a'
    if any(token in metric for token in ['per_hundred', 'positive_rate', 'stringency_index', 'reproduction_rate']):
        return f'{value:,.2f}'
    return f'{value:,.0f}'


def make_deepdive_stats(country, metric, label):
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date').dropna(subset=[metric])
    if country_df.empty:
        return [stat_card('No Data', 'n/a', country)]

    active_df = country_df[country_df[metric].fillna(0) != 0]
    stat_df = active_df if not active_df.empty else country_df
    latest = stat_df.iloc[-1]
    peak = stat_df.loc[stat_df[metric].idxmax()]
    avg_value = stat_df[metric].mean()
    total_or_area = stat_df[metric].sum()

    growth_df = growth_rate_analysis(df, country, metric).replace([np.inf, -np.inf], np.nan)
    growth_df = growth_df.dropna(subset=['growth_rate'])
    growth_df = growth_df[growth_df[metric].fillna(0) != 0]
    latest_growth = growth_df.iloc[-1]['growth_rate'] if not growth_df.empty else np.nan
    max_growth = growth_df['growth_rate'].clip(upper=500).max() if not growth_df.empty else np.nan

    total_label = 'Total' if metric.startswith('new_') else 'Area'
    return [
        stat_card('Latest Value', format_metric_value(latest[metric], metric), str(latest['date'].date())),
        stat_card('Peak Value', format_metric_value(peak[metric], metric), str(peak['date'].date())),
        stat_card('Average', format_metric_value(avg_value, metric), label),
        stat_card(total_label, format_metric_value(total_or_area, metric), 'selected metric sum'),
        stat_card('Latest Growth', f'{latest_growth:+.1f}%' if not pd.isna(latest_growth) else 'n/a', 'day over day'),
        stat_card('Max Growth', f'{max_growth:+.1f}%' if not pd.isna(max_growth) else 'n/a', 'capped at 500%'),
    ]


def build_timeseries(metric, country):
    """Time Series tab: dual-axis chart only."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    vacc_metric = 'people_fully_vaccinated_per_hundred'
    stats_cards = make_deepdive_stats(country, metric, metric_label)
    return html.Div([
        html.Div(stats_cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(170px, 1fr))',
                                     'gap': '16px', 'marginBottom': '20px'}),
        section_header('Time Series Analysis', f'{country} — {metric_label}'),
        card([
            dcc.Graph(id='timeseries-chart', figure=plot_dual_axis(df, country, metric, vacc_metric), style={'height': '500px', 'width': '100%'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_growth_rate_page(metric, country):
    """Growth Rate tab: standalone growth rate chart."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    stats_cards = make_deepdive_stats(country, metric, metric_label)
    return html.Div([
        html.Div(stats_cards, style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(170px, 1fr))',
                                     'gap': '16px', 'marginBottom': '20px'}),
        section_header('Growth Rate Analysis', f'{country} — Daily growth rate of {metric_label}', subtitle_class='animate-subtitle'),
        card([
            dcc.Graph(figure=plot_growth_rate(df, country, metric), style={'height': '500px', 'width': '100%'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_rankings(metric):
    """Rankings tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    top_df = top_countries(df, metric=metric, n=20)
    return html.Div([
        section_header('Rankings', f'Top 20 countries by {metric_label}'),
        card([
            dcc.Graph(
                figure=plot_bar_chart(top_df, x_col='country', y_col=metric, title=f'Top 20 — {metric_label}', color_col='continent'),
                style={'height': '550px'}, config=PLOTLY_CONFIG
            )
        ])
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


def insight_panel(process_text, conclusion_text):
    return html.Div([
        html.Div([
            html.Div('Analysis process', style={**TYPOGRAPHY['kpi_label'], 'marginBottom': '6px'}),
            html.Div(process_text, style={**TYPOGRAPHY['body_text'], 'lineHeight': '1.55'})
        ], style={'flex': '1'}),
        html.Div([
            html.Div('Conclusion', style={**TYPOGRAPHY['kpi_label'], 'marginBottom': '6px'}),
            html.Div(conclusion_text, style={**TYPOGRAPHY['body_text'], 'lineHeight': '1.55', 'fontWeight': '500'})
        ], style={'flex': '1'})
    ], style={
        'display': 'flex',
        'gap': '24px',
        'background': '#ffffff',
        'borderRadius': '12px',
        'boxShadow': '0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)',
        'padding': '18px 20px',
        'marginBottom': '16px',
        'flexWrap': 'wrap'
    })


def correlation_insight(x_metric, y_metric, color_col):
    latest = df.loc[df.groupby('country')['date'].idxmax()].copy()
    latest = add_correlation_groups(latest)
    required = [x_metric, y_metric]
    if color_col:
        required.append(color_col)
    plot_df = latest.dropna(subset=required)
    x_label = metric_label(x_metric)
    y_label = metric_label(y_metric)
    color_label = next((opt['label'] for opt in CORRELATION_COLOR_OPTIONS if opt['value'] == color_col), color_col)

    if len(plot_df) < 3:
        return insight_panel(
            f'The chart uses the latest available country record and compares {x_label} with {y_label}.',
            'There are not enough valid countries to produce a reliable correlation reading.'
        )

    corr = plot_df[[x_metric, y_metric]].corr().iloc[0, 1]
    abs_corr = abs(corr)
    if abs_corr >= 0.65:
        strength = 'strong'
    elif abs_corr >= 0.35:
        strength = 'moderate'
    elif abs_corr >= 0.15:
        strength = 'weak'
    else:
        strength = 'very weak'
    direction = 'positive' if corr > 0 else 'negative'

    process = (
        f'Each point is one country using its latest available record. The scatter compares {x_label} on the X-axis '
        f'against {y_label} on the Y-axis, grouped by {color_label}. Countries with missing values are excluded.'
    )
    conclusion = (
        f'The Pearson correlation is {corr:.2f}, indicating a {strength} {direction} relationship. '
        'This describes association only; it does not prove causation.'
    )
    return insight_panel(process, conclusion)


def build_correlation(metric):
    """Correlation tab."""
    compare = default_correlation_y(metric)
    return html.Div([
        section_header('Correlation Analysis', 'Explore relationships between metrics'),
        card([
            html.Div([
                html.Div([html.Span('X Metric', style=TYPOGRAPHY['control_label']), dcc.Dropdown(id='corr-x', options=[{'label': m['label'], 'value': m['id']} for m in CORRELATION_METRICS if m['id'] in df.columns], value=metric if metric in df.columns else 'new_cases_smoothed', clearable=False, style=DROPDOWN_STYLE)], style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
                html.Div([html.Span('Y Metric', style=TYPOGRAPHY['control_label']), dcc.Dropdown(id='corr-y', options=[{'label': m['label'], 'value': m['id']} for m in CORRELATION_METRICS if m['id'] in df.columns], value=compare, clearable=False, style=DROPDOWN_STYLE)], style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
                html.Div([html.Span('Color By', style=TYPOGRAPHY['control_label']), dcc.Dropdown(id='corr-color', options=CORRELATION_COLOR_OPTIONS, value='continent', clearable=False, style={'width': '220px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY})], style={'display': 'flex', 'flexDirection': 'column', 'gap': '4px'}),
            ], style={'display': 'flex', 'gap': '20px', 'alignItems': 'flex-end', 'flexWrap': 'wrap', 'marginBottom': '16px'}),
            html.Div(id='correlation-insight', children=correlation_insight(metric, compare, 'continent')),
            dcc.Graph(id='correlation-chart', figure=make_correlation_figure(metric, compare, 'continent'), style={'height': '560px'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_continent(metric):
    """Continent Analysis tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    latest = df.loc[df.groupby('country')['date'].idxmax()]
    cont_df = latest.groupby('continent')[metric].agg(['sum', 'mean', 'max', 'count']).reset_index()
    cont_df.columns = ['continent', 'total', 'average', 'maximum', 'count']
    cont_df = cont_df.sort_values('total', ascending=True)
    fig = plot_bar_chart(cont_df, x_col='continent', y_col='total',
                         title=f'{metric_label} by Continent', color_col='continent')
    return html.Div([
        section_header('Continent Comparison', f'{metric_label} across continents'),
        card([dcc.Graph(figure=fig, style={'height': '400px'}, config=PLOTLY_CONFIG)])
    ])


# ═══════════════════════════════════════════════════════════════════════
# Advanced Tab Builders
# ═══════════════════════════════════════════════════════════════════════

def empty_figure(message='No data available'):
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref='paper', yref='paper', showarrow=False, font={'size': 14, 'color': '#666'})
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
        title=title, template='plotly_white', hovermode='x unified', height=height,
        margin={'l': 60, 'r': 24, 't': 54, 'b': 46},
        legend={'orientation': 'h', 'yanchor': 'bottom', 'y': 1.02, 'xanchor': 'right', 'x': 1})
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
        main_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df[base_metric], mode='lines', name='Raw daily value' if not is_derived else 'Daily change', line={'color': 'rgba(120,120,120,0.35)', 'width': 1}))
    main_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['ma_7d'], mode='lines', name='7-day MA', line={'color': '#2563eb', 'width': 1.8}))
    main_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['ma_30d'], mode='lines', name='30-day MA', line={'color': '#dc2626', 'width': 1.8}))
    style_ma_figure(main_fig, f'Trend Overview: {value_label} — {country} ({range_label})', height=420)
    window_fig = go.Figure()
    for window, color in [(7, '#2563eb'), (14, '#16a34a'), (30, '#dc2626')]:
        window_fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df[f'ma_{window}d'], mode='lines', name=f'{window}-day MA', line={'color': color, 'width': 1.8}))
    style_ma_figure(window_fig, f'Window Comparison: {range_label}', height=340)
    diff_fig = go.Figure()
    diff_fig.add_trace(go.Bar(x=plot_df['date'], y=plot_df['ma_diff_7_30'], name='7-day minus 30-day', marker_color=np.where(plot_df['ma_diff_7_30'] >= 0, '#dc2626', '#2563eb')))
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
        stat_card('7-Day MA', f'{latest["ma_7d"]:,.0f}', 'short-term'),
        stat_card('30-Day MA', f'{latest["ma_30d"]:,.0f}', 'baseline'),
        stat_card('7 vs 30', f'{diff:,.0f}', trend_detail),
        stat_card('Peak 7-Day MA', f'{peak["ma_7d"]:,.0f}', str(peak['date'].date())),
        stat_card('Trend', trend_status, f'{days_since_peak} days since peak'),
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
    fig.add_trace(go.Scatter(x=anomaly_df['date'], y=anomaly_df['upper_bound'], mode='lines', name='Upper bound', line={'dash': 'dash', 'color': '#dc2626'}))
    fig.add_trace(go.Scatter(x=anomaly_df['date'], y=anomaly_df['lower_bound'], mode='lines', name='Lower bound', line={'dash': 'dash', 'color': '#dc2626'}))
    fig.add_trace(go.Scatter(x=anomalies['date'], y=anomalies[metric], mode='markers', name='Anomalies', marker={'size': 8, 'color': '#dc2626'}))
    fig.update_layout(title=f'{metric_label} Anomalies — {country}', template='plotly_white', margin={'l': 40, 'r': 20, 't': 50, 'b': 40}, legend={'orientation': 'h'})
    return fig


def make_fatality_outputs(country):
    fatality_df = fatality_trend(df, country)
    if fatality_df.empty:
        return empty_figure('No fatality data available'), []
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fatality_df['date'], y=fatality_df['cfr'], mode='lines', name='CFR', line={'color': '#dc2626'}))
    fig.add_trace(go.Scatter(x=fatality_df['date'], y=fatality_df['cfr_14d_ma'], mode='lines', name='14-day MA', line={'color': '#2563eb'}))
    fig.update_layout(title=f'Case Fatality Rate — {country}', yaxis_title='CFR (%)', template='plotly_white', margin={'l': 40, 'r': 20, 't': 50, 'b': 40}, legend={'orientation': 'h'})
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


def fatality_analysis_series(country):
    cols = ['date', 'total_cases', 'total_deaths']
    for col in ['new_cases_smoothed', 'new_deaths_smoothed']:
        if col in df.columns:
            cols.append(col)

    country_df = df[df['country'] == country][cols].copy()
    country_df = country_df.sort_values('date').dropna(subset=['total_cases', 'total_deaths'])
    if country_df.empty:
        return country_df

    country_df['cumulative_cfr'] = np.where(
        country_df['total_cases'] > 0,
        country_df['total_deaths'] / country_df['total_cases'] * 100,
        np.nan
    )
    daily_cases = country_df['new_cases_smoothed'].clip(lower=0) if 'new_cases_smoothed' in country_df.columns else country_df['total_cases'].diff().clip(lower=0)
    daily_deaths = country_df['new_deaths_smoothed'].clip(lower=0) if 'new_deaths_smoothed' in country_df.columns else country_df['total_deaths'].diff().clip(lower=0)

    cases_30d = daily_cases.shift(14).rolling(window=30, min_periods=7).sum()
    deaths_30d = daily_deaths.rolling(window=30, min_periods=7).sum()
    country_df['recent_cases_30d'] = cases_30d
    country_df['recent_deaths_30d'] = deaths_30d
    min_cases = max(1000, cases_30d.max(skipna=True) * 0.05)
    country_df['recent_fatality_ratio'] = np.where(cases_30d >= min_cases, deaths_30d / cases_30d * 100, np.nan)
    country_df['recent_fatality_90d'] = country_df['recent_fatality_ratio'].rolling(window=90, min_periods=14).mean()
    country_df['fatality_gap'] = country_df['recent_fatality_ratio'] - country_df['cumulative_cfr']
    country_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    return country_df


def latest_valid_fatality_row(fatality_df):
    valid = fatality_df.dropna(subset=['cumulative_cfr', 'recent_fatality_ratio', 'fatality_gap'])
    if not valid.empty:
        return valid.iloc[-1]
    return fatality_df.dropna(subset=['cumulative_cfr']).iloc[-1]


def make_fatality_outputs(country, compare_list=None):
    fatality_df = fatality_analysis_series(country)
    if fatality_df.empty:
        return empty_figure('No fatality data available'), []

    plot_df = fatality_df.dropna(subset=['cumulative_cfr'])
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
        row_heights=[0.7, 0.3],
        subplot_titles=('', '')
    )
    fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['cumulative_cfr'], mode='lines', name='Cumulative CFR', line={'color': '#6b7280', 'width': 2}), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['recent_fatality_ratio'], mode='lines', name='30-day recent ratio', line={'color': '#dc2626', 'width': 2}), row=1, col=1)
    fig.add_trace(go.Scatter(x=plot_df['date'], y=plot_df['recent_fatality_90d'], mode='lines', name='90-day smooth', line={'color': '#2563eb', 'width': 2}), row=1, col=1)

    compare_colors = ['#16a34a', '#d97706', '#7c3aed', '#0891b2']
    compare_countries = [c for c in (compare_list or []) if c and c != country][:4]
    for compare_country, color in zip(compare_countries, compare_colors):
        compare_df = fatality_analysis_series(compare_country).dropna(subset=['recent_fatality_90d'])
        if compare_df.empty:
            continue
        fig.add_trace(go.Scatter(
            x=compare_df['date'],
            y=compare_df['recent_fatality_90d'],
            mode='lines',
            name=f'{compare_country} 90-day',
            line={'color': color, 'width': 1.6, 'dash': 'dot'},
            opacity=0.85
        ), row=1, col=1)

    fig.add_trace(go.Bar(x=plot_df['date'], y=plot_df['fatality_gap'], name='Recent - cumulative', marker_color=np.where(plot_df['fatality_gap'].fillna(0) >= 0, '#dc2626', '#2563eb')), row=2, col=1)
    fig.add_hline(y=0, line_width=1, line_dash='dash', line_color='#777', row=2, col=1)
    fig.update_layout(
        title=f'Fatality Trend Analysis - {country}' + (f' vs {len(compare_countries)} compare countries' if compare_countries else ''),
        template='plotly_white',
        height=620,
        margin={'l': 60, 'r': 24, 't': 62, 'b': 98},
        title_font={'size': 16},
        legend={
            'orientation': 'h',
            'yanchor': 'top',
            'y': -0.16,
            'xanchor': 'center',
            'x': 0.5,
            'font': {'size': 11}
        },
        hovermode='x unified'
    )
    fig.update_yaxes(title_text='Fatality rate (%)', gridcolor='#e8e8e8', row=1, col=1)
    fig.update_yaxes(title_text='Gap (pp)', gridcolor='#e8e8e8', row=2, col=1)
    fig.update_xaxes(gridcolor='#e8e8e8')

    latest = latest_valid_fatality_row(fatality_df)
    peak_source = fatality_df.dropna(subset=['recent_fatality_ratio'])
    peak = peak_source.loc[peak_source['recent_fatality_ratio'].idxmax()] if not peak_source.empty else latest
    gap = latest.get('fatality_gap', np.nan)
    if pd.isna(gap):
        status = 'No recent signal'
        subtitle = 'insufficient recent cases'
    elif gap > 0.25:
        status = 'Above baseline'
        subtitle = f'{gap:+.2f} pp vs cumulative'
    elif gap < -0.25:
        status = 'Below baseline'
        subtitle = f'{gap:+.2f} pp vs cumulative'
    else:
        status = 'Near baseline'
        subtitle = f'{gap:+.2f} pp vs cumulative'

    stats_cards = [
        stat_card('Cumulative CFR', f'{latest["cumulative_cfr"]:.2f}%', 'all-time baseline'),
        stat_card('Recent Fatality', f'{latest["recent_fatality_ratio"]:.2f}%' if not pd.isna(latest["recent_fatality_ratio"]) else 'n/a', '30-day deaths / 14-day lagged cases'),
        stat_card('Fatality Gap', f'{gap:+.2f} pp' if not pd.isna(gap) else 'n/a', status),
        stat_card('Peak Recent Ratio', f'{peak["recent_fatality_ratio"]:.2f}%' if not pd.isna(peak["recent_fatality_ratio"]) else 'n/a', str(peak['date'].date())),
        stat_card('Total Deaths', f'{latest["total_deaths"]:,.0f}', subtitle),
    ]
    return fig, stats_cards


def make_lag_figure(country, x_metric, y_metric):
    lag_df = cross_lag_correlation(df, country, x_metric, y_metric, max_lag=60)
    if lag_df.empty:
        return empty_figure('No lead-lag data available')
    x_label = next((m['label'] for m in METRICS if m['id'] == x_metric), x_metric)
    y_label = next((m['label'] for m in METRICS if m['id'] == y_metric), y_metric)
    fig = px.bar(lag_df, x='lag_days', y='correlation', title=f'{x_label} vs {y_label} — {country}')
    fig.update_layout(template='plotly_white', xaxis_title='Lag days', yaxis_title='Correlation', margin={'l': 40, 'r': 20, 't': 50, 'b': 40})
    return fig


def lag_insight(country, x_metric, y_metric):
    lag_df = cross_lag_correlation(df, country, x_metric, y_metric, max_lag=60)
    x_label = next((m['label'] for m in METRICS if m['id'] == x_metric), x_metric)
    y_label = next((m['label'] for m in METRICS if m['id'] == y_metric), y_metric)
    if lag_df.empty:
        return insight_panel(
            f'The analysis shifts {x_label} and {y_label} across lag days to test whether one time series moves before the other.',
            'There is not enough valid time-series data to estimate a stable lead-lag relationship.'
        )

    best = lag_df.loc[lag_df['correlation'].abs().idxmax()]
    lag_days = int(best['lag_days'])
    corr = float(best['correlation'])
    if abs(corr) >= 0.65:
        strength = 'strong'
    elif abs(corr) >= 0.35:
        strength = 'moderate'
    elif abs(corr) >= 0.15:
        strength = 'weak'
    else:
        strength = 'very weak'

    if lag_days > 0:
        timing = f'{x_label} tends to lead {y_label} by about {lag_days} days'
    elif lag_days < 0:
        timing = f'{y_label} tends to lead {x_label} by about {abs(lag_days)} days'
    else:
        timing = f'{x_label} and {y_label} move most closely with no time lag'
    direction = 'same direction' if corr > 0 else 'opposite directions'

    process = (
        f'The method shifts the leading series from -60 to +60 days and computes the correlation at each lag. '
        f'The bar with the largest absolute correlation is used as the strongest timing signal for {country}.'
    )
    conclusion = (
        f'The strongest signal is at lag {lag_days} days with correlation {corr:.2f}. '
        f'This is a {strength} relationship: {timing}, moving in {direction}.'
    )
    return insight_panel(process, conclusion)


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
    fig = px.scatter(cluster_df, x='total_cases_per_million', y='total_deaths_per_million', color=cluster_df['cluster'].astype(str), hover_name='country', size='population', title='Country Clusters')
    fig.update_layout(template='plotly_white', xaxis_title='Total cases per million', yaxis_title='Total deaths per million', margin={'l': 40, 'r': 20, 't': 50, 'b': 40}, legend_title='Cluster')
    summary_cards = []
    for label, group in cluster_df.groupby('cluster'):
        summary_cards.append(
            html.Div([
                html.Div(f'Cluster {label}', style={'fontSize': '12px', 'fontWeight': '600', 'color': '#555', 'fontFamily': FONT_FAMILY}),
                html.Div(f'{len(group)} countries', style={'fontSize': '14px', 'fontWeight': '700', 'color': '#222', 'fontFamily': FONT_FAMILY}),
                html.Div(f'Cases: {group["total_cases_per_million"].mean():,.0f}', style={'fontSize': '11px', 'color': '#888', 'fontFamily': FONT_FAMILY}),
                html.Div(f'Deaths: {group["total_deaths_per_million"].mean():,.0f}', style={'fontSize': '11px', 'color': '#888', 'fontFamily': FONT_FAMILY}),
                html.Div(f'Vaccination: {group["people_fully_vaccinated_per_hundred"].mean():.1f}%', style={'fontSize': '11px', 'color': '#888', 'fontFamily': FONT_FAMILY}),
            ], style={'flex': '1', 'minWidth': '150px', 'background': '#f9f9f9', 'padding': '14px', 'borderRadius': '10px', 'border': 'none', 'boxShadow': '0 1px 2px rgba(0,0,0,0.04)'})
        )
    return fig, summary_cards


def build_ma_tab(metric, country):
    """Moving Average tab."""
    main_fig, recent_fig, diff_fig, stats_cards = make_moving_average_outputs(country, metric)
    return html.Div([
        section_header('Moving Average Analysis', f'{country} — Trend smoothing and momentum'),
        html.Div(id='ma-stats', children=stats_cards, style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap', 'marginBottom': '16px'}),
        card([
            html.Div([
                html.Span('View Range:', style={'fontSize': '12px', 'color': '#888', 'marginRight': '8px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='ma-range', options=MA_PERIOD_OPTIONS, value='all', clearable=False, style={'width': '260px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
                dcc.Checklist(id='ma-show-raw', options=[{'label': 'Show Raw', 'value': 'raw'}], value=['raw'], inputStyle={'marginRight': '6px'}, labelStyle={'fontSize': '12px', 'color': '#888', 'fontFamily': FONT_FAMILY, 'marginLeft': '16px'}),
            ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '16px'}),
            dcc.Graph(id='ma-main-chart', figure=main_fig, style={'height': '420px'}, config=PLOTLY_CONFIG)
        ], style_extra={'marginBottom': '16px'}),
        card([dcc.Graph(id='ma-recent-chart', figure=recent_fig, style={'height': '340px'}, config=PLOTLY_CONFIG)], style_extra={'marginBottom': '16px'}),
        card([dcc.Graph(id='ma-diff-chart', figure=diff_fig, style={'height': '300px'}, config=PLOTLY_CONFIG)])
    ])


def build_anomaly_tab(metric, country):
    """Anomaly Detection tab."""
    metric_label = next((m['label'] for m in METRICS if m['id'] == metric), metric)
    return html.Div([
        section_header('Anomaly Detection', f'{country} — Identifying outliers in {metric_label}'),
        card([
            html.Div([
                html.Span('Window:', style={'fontSize': '12px', 'color': '#888', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='anomaly-window', options=[{'label': f'{w} days', 'value': w} for w in [7, 14, 30]], value=14, clearable=False, style={'width': '120px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
                html.Span('Threshold:', style={'fontSize': '12px', 'color': '#888', 'marginLeft': '12px', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='anomaly-threshold', options=[{'label': f'{t}σ', 'value': t} for t in [1.5, 2.0, 2.5, 3.0]], value=2.0, clearable=False, style={'width': '100px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
            ], style={'marginBottom': '16px'}),
            dcc.Graph(id='anomaly-chart', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_fatality_tab(country):
    """Fatality Analysis tab."""
    return html.Div([
        section_header('Fatality Trend', f'{country} — Case Fatality Rate (CFR)'),
        card([
            dcc.Graph(id='fatality-chart', style={'height': '620px'}, config=PLOTLY_CONFIG)
        ], style_extra={'marginBottom': '16px'}),
        html.Div(id='fatality-stats', style={'display': 'grid', 'gridTemplateColumns': 'repeat(5, minmax(180px, 1fr))', 'gap': '16px'})
    ])


def build_lag_tab(country):
    """Lead-Lag Correlation tab."""
    return html.Div([
        section_header('Lead-Lag Analysis', f'{country} — Cross-correlation between metrics'),
        card([
            html.Div([
                html.Span('Leading:', style={'fontSize': '12px', 'color': '#888', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='lag-x', options=[{'label': m['label'], 'value': m['id']} for m in METRICS], value='new_cases_smoothed', clearable=False, style={'width': '200px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
                html.Span('Lagging:', style={'fontSize': '12px', 'color': '#888', 'marginLeft': '12px', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='lag-y', options=[{'label': m['label'], 'value': m['id']} for m in METRICS], value='new_deaths_smoothed', clearable=False, style={'width': '200px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
            ], style={'marginBottom': '16px'}),
            html.Div(id='lag-insight', children=lag_insight(country, 'new_cases_smoothed', 'new_deaths_smoothed')),
            dcc.Graph(id='lag-chart', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ])
    ])


def build_cluster_tab():
    """Clustering tab."""
    return html.Div([
        section_header('Country Clustering', 'Unsupervised learning: country segmentation'),
        card([
            html.Div([
                html.Span('Clusters:', style={'fontSize': '12px', 'color': '#888', 'marginRight': '6px', 'fontFamily': FONT_FAMILY}),
                dcc.Dropdown(id='cluster-n', options=[{'label': f'k={k}', 'value': k} for k in range(3, 8)], value=4, clearable=False, style={'width': '100px', 'fontSize': '13px', 'fontFamily': FONT_FAMILY, 'display': 'inline-block'}),
            ], style={'marginBottom': '16px'}),
            dcc.Graph(id='cluster-scatter', style={'height': '450px'}, config=PLOTLY_CONFIG)
        ], style_extra={'marginBottom': '16px'}),
        html.Div(id='cluster-summary', style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'})
    ])


# ═══════════════════════════════════════════════════════════════════════
# Interactive Callbacks (Global Trends, Advanced tabs, etc.)
# ═══════════════════════════════════════════════════════════════════════

# Global tab: map
@app.callback(Output('global-map', 'figure'), [Input('global-metric', 'value'), Input('global-slider', 'value')])
def update_global_map(metric, slider_val):
    return plot_choropleth_map(df, metric, MONTHLY_DATES[slider_val])


# Global tab: date label
@app.callback(Output('global-date-label', 'children'), Input('global-slider', 'value'))
def update_date_label(val):
    return f'Date: {MONTHLY_DATES[val]}'


# Global tab: stats
@app.callback(Output('global-stats', 'children'), [Input('global-metric', 'value'), Input('global-slider', 'value')])
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


# Global tab: trend chart
@app.callback(Output('global-trend-chart', 'figure'), [Input('global-metric', 'value'), Input('global-country', 'value'), Input('global-compare', 'value'), Input('global-slider', 'value')])
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


# Play interval
app.layout.children.append(dcc.Interval(id='play-interval', interval=400, n_intervals=0, disabled=True))

@app.callback(Output('play-interval', 'disabled'), Input('global-play', 'n_clicks'), State('play-interval', 'disabled'))
def toggle_play(n_clicks, disabled):
    if n_clicks == 0:
        return True
    return not disabled

@app.callback(Output('global-slider', 'value'), [Input('play-interval', 'n_intervals')], [State('global-slider', 'value')])
def advance_play(n_intervals, current):
    if current is None:
        return len(MONTHLY_DATES) - 1
    next_val = current + 1
    if next_val >= len(MONTHLY_DATES):
        return 0
    return next_val


# Correlation tab callback
@app.callback(
    [Output('correlation-chart', 'figure'), Output('correlation-insight', 'children')],
    [Input('corr-x', 'value'), Input('corr-y', 'value'), Input('corr-color', 'value')]
)
def update_correlation_chart(x_metric, y_metric, color_col):
    return make_correlation_figure(x_metric, y_metric, color_col), correlation_insight(x_metric, y_metric, color_col)


# Moving Average tab callback
@app.callback(
    [Output('ma-main-chart', 'figure'), Output('ma-recent-chart', 'figure'), Output('ma-diff-chart', 'figure'), Output('ma-stats', 'children')],
    [Input('global-metric', 'value'), Input('global-country', 'value'), Input('ma-range', 'value'), Input('ma-show-raw', 'value')]
)
def update_moving_average(metric, country, view_range, show_raw_values):
    show_raw = bool(show_raw_values and 'raw' in show_raw_values)
    main_fig, recent_fig, diff_fig, stats_cards = make_moving_average_outputs(country, metric, view_range=view_range, show_raw=show_raw)
    return main_fig, recent_fig, diff_fig, stats_cards


# Anomaly tab callback
@app.callback(Output('anomaly-chart', 'figure'), [Input('global-metric', 'value'), Input('global-country', 'value'), Input('anomaly-window', 'value'), Input('anomaly-threshold', 'value')])
def update_anomaly(metric, country, window, threshold):
    return make_anomaly_figure(country, metric, window=window, threshold=threshold)


# Fatality tab callback
@app.callback(
    [Output('fatality-chart', 'figure'), Output('fatality-stats', 'children')],
    [Input('global-country', 'value'),
     Input('global-compare', 'value')]
)
def update_fatality(country, compare_list):
    fig, stats_cards = make_fatality_outputs(country, compare_list)
    return fig, stats_cards


# Lead-Lag tab callback
@app.callback(
    [Output('lag-chart', 'figure'), Output('lag-insight', 'children')],
    [Input('global-country', 'value'), Input('lag-x', 'value'), Input('lag-y', 'value')]
)
def update_lag(country, x_metric, y_metric):
    return make_lag_figure(country, x_metric, y_metric), lag_insight(country, x_metric, y_metric)


# Clustering tab callback
@app.callback([Output('cluster-scatter', 'figure'), Output('cluster-summary', 'children')], [Input('cluster-n', 'value')])
def update_cluster(k):
    fig, summary_cards = make_cluster_outputs(k)
    return fig, html.Div(summary_cards, style={'display': 'flex', 'gap': '16px', 'flexWrap': 'wrap'})


# Overview tab: country filter + date range
@app.callback(Output('data-table', 'data'), [Input('overview-country-filter', 'value'), Input('overview-date-range', 'start_date'), Input('overview-date-range', 'end_date')])
def update_overview_table(country_filter, start_date, end_date):
    filtered = df.copy()
    if country_filter and country_filter != 'ALL':
        filtered = filtered[filtered['country'] == country_filter]
    if start_date:
        filtered = filtered[filtered['date'] >= pd.Timestamp(start_date)]
    if end_date:
        filtered = filtered[filtered['date'] <= pd.Timestamp(end_date)]
    return format_overview_table_records(filtered.head(100))


# ═══════════════════════════════════════════════════════════════════════
# Exit button
# ═══════════════════════════════════════════════════════════════════════
app.clientside_callback(
    """function(n_clicks) { if (n_clicks > 0) { window.close(); } return 'Exit'; }""",
    Output('exit-btn', 'children'),
    Input('exit-btn', 'n_clicks')
)


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print("Starting COVID-19 Data Explorer...")
    print(f"Open http://127.0.0.1:8051 in your browser")
    app.run(debug=False, host='127.0.0.1', port=8051)
