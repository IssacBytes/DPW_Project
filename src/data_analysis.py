"""
Data Analysis Module
Performs statistical analysis, trend analysis, and comparisons.
Provides function interfaces for GUI to interact with.
"""

import pandas as pd
import numpy as np


def descriptive_stats(df: pd.DataFrame, column: str) -> dict:
    """
    Calculate descriptive statistics for a specific column.
    
    Args:
        df: Input DataFrame
        column: Column name to analyze
        
    Returns:
        Dictionary with statistical measures
    """
    data = df[column].dropna()
    stats = {
        'column': column,
        'count': int(len(data)),
        'mean': float(data.mean()),
        'median': float(data.median()),
        'std': float(data.std()),
        'min': float(data.min()),
        'max': float(data.max()),
        'q1': float(data.quantile(0.25)),
        'q3': float(data.quantile(0.75)),
        'sum': float(data.sum()),
    }
    return stats


def global_trend(df: pd.DataFrame, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
    """
    Calculate global daily trend for a given metric.
    Aggregates all countries by date.
    
    Args:
        df: Input DataFrame
        metric: Column name to aggregate (e.g., 'new_cases_smoothed', 'new_deaths_smoothed')
        
    Returns:
        DataFrame with date and global total for the metric
    """
    global_df = df.groupby('date')[metric].sum().reset_index()
    global_df = global_df.sort_values('date')
    return global_df


def country_trend(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
    """
    Get trend data for a specific country.
    
    Args:
        df: Input DataFrame
        country: Country name
        metric: Column name for the metric to analyze
        
    Returns:
        DataFrame with date and metric values for the country
    """
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date')
    return country_df


def compare_countries(df: pd.DataFrame, countries: list, metric: str = 'total_cases_per_million') -> pd.DataFrame:
    """
    Compare multiple countries on a given metric over time.
    
    Args:
        df: Input DataFrame
        countries: List of country names
        metric: Column name to compare
        
    Returns:
        DataFrame with date, country, and metric columns
    """
    compare_df = df[df['country'].isin(countries)][['date', 'country', metric]].copy()
    compare_df = compare_df.sort_values(['country', 'date'])
    return compare_df


def top_countries(df: pd.DataFrame, metric: str = 'total_cases', n: int = 10, date: str = None) -> pd.DataFrame:
    """
    Get top N countries for a given metric.
    
    Args:
        df: Input DataFrame
        metric: Column name to rank by
        n: Number of top countries to return
        date: Specific date to analyze (if None, uses latest available date)
        
    Returns:
        DataFrame with top countries and their metric values
    """
    if date is None:
        # Use the latest date for each country
        latest_df = df.loc[df.groupby('country')['date'].idxmax()]
    else:
        latest_df = df[df['date'] == date].copy()
    
    top_df = latest_df.dropna(subset=[metric]).nlargest(n, metric)
    return top_df[['country', metric, 'continent', 'population']]


def growth_rate_analysis(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
    """
    Calculate daily growth rate for a country.
    
    Args:
        df: Input DataFrame
        country: Country name
        metric: Column name for the metric
        
    Returns:
        DataFrame with date, metric value, and daily growth rate (%)
    """
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.sort_values('date')
    
    # Calculate daily growth rate
    country_df['growth_rate'] = country_df[metric].pct_change() * 100
    country_df['daily_change'] = country_df[metric].diff()
    
    return country_df


def cumulative_analysis(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """
    Analyze cumulative cases and deaths for a country.
    
    Args:
        df: Input DataFrame
        country: Country name
        
    Returns:
        DataFrame with cumulative metrics
    """
    country_df = df[df['country'] == country][
        ['date', 'total_cases', 'total_deaths', 'new_cases_smoothed', 'new_deaths_smoothed']
    ].copy()
    country_df = country_df.sort_values('date')
    
    # Calculate death rate
    country_df['death_rate'] = (country_df['total_deaths'] / country_df['total_cases'] * 100)
    
    return country_df


def continent_comparison(df: pd.DataFrame, metric: str = 'new_cases_smoothed') -> pd.DataFrame:
    """
    Aggregate data by continent over time.
    
    Args:
        df: Input DataFrame
        metric: Column name to aggregate
        
    Returns:
        DataFrame with date, continent, and aggregated metric
    """
    continent_df = df.groupby(['date', 'continent'])[metric].sum().reset_index()
    continent_df = continent_df.sort_values(['continent', 'date'])
    return continent_df


def correlation_analysis(df: pd.DataFrame, columns: list = None) -> pd.DataFrame:
    """
    Calculate correlation matrix between selected numeric columns.
    
    Args:
        df: Input DataFrame
        columns: List of columns to include (if None, uses all numeric)
        
    Returns:
        Correlation matrix DataFrame
    """
    if columns is None:
        # Select key numeric columns for correlation
        columns = [
            'new_cases_smoothed', 'new_deaths_smoothed', 
            'total_cases_per_million', 'total_deaths_per_million',
            'people_fully_vaccinated_per_hundred', 'stringency_index',
            'population_density', 'median_age', 'gdp_per_capita',
            'diabetes_prevalence', 'life_expectancy'
        ]
    
    available_cols = [c for c in columns if c in df.columns]
    corr_df = df[available_cols].dropna().corr()
    return corr_df


def vaccination_impact(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """
    Analyze the impact of vaccination on new cases for a country.
    
    Args:
        df: Input DataFrame
        country: Country name
        
    Returns:
        DataFrame with vaccination and case data aligned
    """
    country_df = df[df['country'] == country][
        ['date', 'new_cases_smoothed', 'new_deaths_smoothed',
         'people_fully_vaccinated_per_hundred', 'total_vaccinations_per_hundred']
    ].copy()
    country_df = country_df.sort_values('date')
    return country_df


def get_peak_dates(df: pd.DataFrame, country: str, metric: str = 'new_cases_smoothed', n_peaks: int = 3) -> list:
    """
    Find the dates with the highest values for a given metric.
    
    Args:
        df: Input DataFrame
        country: Country name
        metric: Column name
        n_peaks: Number of peaks to return
        
    Returns:
        List of (date, value) tuples for peak dates
    """
    country_df = df[df['country'] == country][['date', metric]].copy()
    country_df = country_df.dropna()
    peaks = country_df.nlargest(n_peaks, metric)
    return list(zip(peaks['date'].dt.strftime('%Y-%m-%d'), peaks[metric]))
