from dash import html


def build_start_page(loading=False, status_text=None, disable_enter=False, error_text=None):
    """Full-screen Apple-inspired entry page for the dashboard."""
    if error_text:
        status_class = 'start-status start-status-error'
    elif loading:
        status_class = 'start-status start-status-loading'
    else:
        status_class = 'start-status start-status-ready'
    status_message = error_text or status_text or ('Loading COVID-19 dataset...' if loading else 'Ready')
    button_class = 'start-primary-btn start-primary-btn-disabled' if disable_enter else 'start-primary-btn'
    nav_button_class = 'start-nav-cta start-nav-cta-disabled' if disable_enter else 'start-nav-cta'
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
                            html.Button('Explore Data', id='start-nav-btn', n_clicks=0,
                                        className=nav_button_class, disabled=disable_enter),
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
                            html.Span(className='start-status-dot'),
                            html.Span(status_message, id='startup-status-text'),
                        ],
                        className=status_class,
                    ),
                    html.Div(
                        [
                            html.Button('Explore Data', id='start-enter-btn', n_clicks=0,
                                        className=button_class, disabled=disable_enter),
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
