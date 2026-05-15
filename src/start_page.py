from dash import html


def build_start_page():
    """Full-screen Apple-inspired entry page for the dashboard."""
    return html.Div(
        [
            html.Div(className='start-page-bg'),
            html.Div(className='start-page-vignette'),
            html.Nav(
                [
                    html.Div('COVID-19 Data Explorer', className='start-brand'),
                    html.Div(
                        [
                            html.Span('Global Trends'),
                            html.Span('Country Comparison'),
                            html.Button('Explore Data', id='start-nav-btn', n_clicks=0, className='start-nav-cta'),
                        ],
                        className='start-nav-links',
                    ),
                ],
                className='start-nav',
            ),
            html.Main(
                [
                    html.Div('Public health intelligence, made visual.', className='start-eyebrow'),
                    html.H1('COVID-19 Data Explorer', className='start-title'),
                    html.P(
                        'Explore global pandemic trends, country comparisons, vaccination progress, '
                        'policy signals, and public health patterns from one interactive dashboard.',
                        className='start-subtitle',
                    ),
                    html.Div(
                        [
                            html.Button('Explore Data', id='start-enter-btn', n_clicks=0, className='start-primary-btn'),
                            html.Span('Our World in Data dataset', className='start-source'),
                        ],
                        className='start-actions',
                    ),
                ],
                className='start-hero',
            ),
            html.Div(
                [
                    html.Div([html.Span('262'), html.Small('countries and regions')]),
                    html.Div([html.Span('2020-2026'), html.Small('daily timeline')]),
                    html.Div([html.Span('67'), html.Small('tracked indicators')]),
                ],
                className='start-metrics',
            ),
        ],
        className='start-page',
    )
