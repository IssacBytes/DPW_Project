"""
Advanced Analysis Module
Extended analytical functions for COVID-19 data.
Used by app_extended.py for the 5 advanced tabs.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


def moving_average(df, country, metric, windows=[7, 14, 30]):
    """
    Compute moving averages for a given country and metric.
    Returns DataFrame with raw values + MA columns.
    """
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date').dropna(subset=[metric])
    
    for w in windows:
        country_df[f'ma_{w}d'] = country_df[metric].rolling(window=w, min_periods=1).mean()
    
    return country_df


def anomaly_detection(df, country, metric, threshold=2.0, window=14):
    """
    Detect anomalies using rolling mean ± threshold * rolling std.
    Returns DataFrame with is_anomaly flag.
    """
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date').dropna(subset=[metric])
    
    country_df['rolling_mean'] = country_df[metric].rolling(window=window, min_periods=1).mean()
    country_df['rolling_std'] = country_df[metric].rolling(window=window, min_periods=1).std().fillna(0)
    country_df['upper_bound'] = country_df['rolling_mean'] + threshold * country_df['rolling_std']
    country_df['lower_bound'] = country_df['rolling_mean'] - threshold * country_df['rolling_std']
    country_df['is_anomaly'] = (
        (country_df[metric] > country_df['upper_bound']) |
        (country_df[metric] < country_df['lower_bound'])
    )
    
    return country_df


def fatality_trend(df, country):
    """
    Compute case fatality rate (CFR) trend for a country.
    Returns DataFrame with total_cases, total_deaths, cfr, cfr_14d_ma.
    """
    country_df = df[df['country'] == country][['date', 'total_cases', 'total_deaths']].copy()
    country_df = country_df.sort_values('date').dropna(subset=['total_cases', 'total_deaths'])
    
    country_df['cfr'] = (country_df['total_deaths'] / country_df['total_cases'] * 100).fillna(0)
    country_df['cfr_14d_ma'] = country_df['cfr'].rolling(window=14, min_periods=1).mean()
    
    return country_df


def cross_lag_correlation(df, country, metric_x, metric_y, max_lag=21):
    """
    Compute cross-correlation between two metrics at various lags.
    Returns DataFrame with lag_days and correlation.
    """
    country_df = df[df['country'] == country][['date', metric_x, metric_y]].copy()
    country_df = country_df.sort_values('date').dropna(subset=[metric_x, metric_y])
    
    x_vals = country_df[metric_x].values
    y_vals = country_df[metric_y].values
    
    results = []
    for lag in range(-max_lag, max_lag + 1):
        if lag < 0:
            x_shifted = x_vals[-lag:]
            y_shifted = y_vals[:lag]
        elif lag > 0:
            x_shifted = x_vals[:-lag]
            y_shifted = y_vals[lag:]
        else:
            x_shifted = x_vals
            y_shifted = y_vals
        
        if len(x_shifted) > 10:
            corr = np.corrcoef(x_shifted, y_shifted)[0, 1]
            results.append({'lag_days': lag, 'correlation': corr if not np.isnan(corr) else 0})
    
    return pd.DataFrame(results)


def simple_clustering(df, n_clusters=5):
    """
    Cluster countries based on latest per-capita metrics.
    Returns DataFrame with cluster labels.
    """
    latest = df.loc[df.groupby('country')['date'].idxmax()].copy()
    
    features = [
        'total_cases_per_million', 'total_deaths_per_million',
        'people_fully_vaccinated_per_hundred', 'population'
    ]
    
    # Filter to countries with all features
    clust_df = latest.dropna(subset=features).copy()
    
    # Scale features
    scaler = StandardScaler()
    scaled = scaler.fit_transform(clust_df[features].fillna(0))
    
    # Cluster
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    clust_df['cluster'] = kmeans.fit_predict(scaled)
    
    return clust_df


def country_summary_report(df, country):
    """
    Generate a summary report for a country.
    Returns dict with key statistics.
    """
    country_df = df[df['country'] == country].sort_values('date')
    
    report = {}
    
    # Latest values
    latest = country_df.iloc[-1] if len(country_df) > 0 else None
    if latest is not None:
        report['total_cases'] = latest.get('total_cases', 0) or 0
        report['total_deaths'] = latest.get('total_deaths', 0) or 0
        report['total_vaccinated'] = latest.get('people_fully_vaccinated_per_hundred', 0) or 0
    
    # CFR
    if report.get('total_cases', 0) > 0:
        report['cfr_percent'] = (report['total_deaths'] / report['total_cases']) * 100
    else:
        report['cfr_percent'] = 0
    
    # Peak values
    if 'new_cases_smoothed' in country_df.columns:
        peak_idx = country_df['new_cases_smoothed'].idxmax()
        report['peak_new_cases'] = {
            'value': country_df.loc[peak_idx, 'new_cases_smoothed'],
            'date': str(country_df.loc[peak_idx, 'date'].date())
        }
    
    if 'new_deaths_smoothed' in country_df.columns:
        peak_idx = country_df['new_deaths_smoothed'].idxmax()
        report['peak_new_deaths'] = {
            'value': country_df.loc[peak_idx, 'new_deaths_smoothed'],
            'date': str(country_df.loc[peak_idx, 'date'].date())
        }
    
    # Recent trend (last 30 days)
    if len(country_df) >= 30 and 'new_cases_smoothed' in country_df.columns:
        recent = country_df.tail(30)
        first_val = recent['new_cases_smoothed'].iloc[0]
        last_val = recent['new_cases_smoothed'].iloc[-1]
        if first_val > 0:
            report['recent_trend'] = {
                'change_pct': ((last_val - first_val) / first_val) * 100,
                'first_date': str(recent['date'].iloc[0].date()),
                'last_date': str(recent['date'].iloc[-1].date())
            }
    
    return report


def multi_metric_summary(df, country, metrics):
    """
    Generate summary for multiple metrics for a country.
    Returns dict of metric -> {mean, max, min, latest}.
    """
    country_df = df[df['country'] == country].sort_values('date')
    
    summary = {}
    for m in metrics:
        if m in country_df.columns:
            series = country_df[m].dropna()
            if len(series) > 0:
                summary[m] = {
                    'mean': series.mean(),
                    'max': series.max(),
                    'min': series.min(),
                    'latest': series.iloc[-1],
                    'std': series.std()
                }
    
    return summary
