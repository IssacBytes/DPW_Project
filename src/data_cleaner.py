"""
Data Cleaner Module
Handles data cleaning: missing values, duplicates, inconsistencies.
Provides function interfaces for GUI to interact with.
"""

import pandas as pd
import numpy as np


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform automatic data cleaning on the COVID-19 dataset.
    
    Steps:
    1. Remove duplicate rows
    2. Sort by country and date
    3. Convert date column
    4. Forward-fill country-level constant columns
    
    Args:
        df: Raw DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Remove duplicates
    df = df.drop_duplicates()
    
    # Sort by country and date
    df = df.sort_values(['country', 'date']).reset_index(drop=True)
    
    # Ensure date is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    return df


def handle_missing_values(df: pd.DataFrame, strategy: str = 'ffill') -> pd.DataFrame:
    """
    Handle missing values in the dataset.
    
    Args:
        df: Input DataFrame
        strategy: 'ffill' (forward fill), 'bfill' (backward fill), 
                  'drop' (drop rows with missing), 'zero' (fill with 0),
                  or 'interpolate' (linear interpolation)
        
    Returns:
        DataFrame with handled missing values
    """
    df = df.copy()
    
    # Columns that should NOT be filled (categorical/identifier columns)
    non_fill_cols = ['country', 'code', 'continent']
    
    # Separate numeric and non-numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    fill_cols = [c for c in numeric_cols if c not in non_fill_cols]
    
    if strategy == 'ffill':
        # Forward fill within each country group
        for col in fill_cols:
            df[col] = df.groupby('country')[col].transform(lambda x: x.ffill())
        # Then backward fill any remaining NaNs at the start
        for col in fill_cols:
            df[col] = df.groupby('country')[col].transform(lambda x: x.bfill())
    
    elif strategy == 'bfill':
        for col in fill_cols:
            df[col] = df.groupby('country')[col].transform(lambda x: x.bfill())
        for col in fill_cols:
            df[col] = df.groupby('country')[col].transform(lambda x: x.ffill())
    
    elif strategy == 'drop':
        df = df.dropna(subset=fill_cols)
    
    elif strategy == 'zero':
        df[fill_cols] = df[fill_cols].fillna(0)
    
    elif strategy == 'interpolate':
        for col in fill_cols:
            df[col] = df.groupby('country')[col].transform(
                lambda x: x.interpolate(method='linear', limit_direction='both')
            )
    
    return df


def filter_by_date(df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Filter data by date range.
    
    Args:
        df: Input DataFrame
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Filtered DataFrame
    """
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    return df[mask].copy()


def filter_by_country(df: pd.DataFrame, countries: list) -> pd.DataFrame:
    """
    Filter data to include only specified countries.
    
    Args:
        df: Input DataFrame
        countries: List of country names to include
        
    Returns:
        Filtered DataFrame
    """
    return df[df['country'].isin(countries)].copy()


def filter_by_continent(df: pd.DataFrame, continents: list) -> pd.DataFrame:
    """
    Filter data to include only specified continents.
    
    Args:
        df: Input DataFrame
        continents: List of continent names to include
        
    Returns:
        Filtered DataFrame
    """
    return df[df['continent'].isin(continents)].copy()


def remove_outliers(df: pd.DataFrame, column: str, method: str = 'iqr', threshold: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers from a specific column.
    
    Args:
        df: Input DataFrame
        column: Column name to check for outliers
        method: 'iqr' (Interquartile Range) or 'zscore'
        threshold: IQR multiplier or Z-score threshold
        
    Returns:
        DataFrame with outliers removed
    """
    df = df.copy()
    
    if method == 'iqr':
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - threshold * IQR
        upper = Q3 + threshold * IQR
        df = df[(df[column] >= lower) & (df[column] <= upper)]
    
    elif method == 'zscore':
        z_scores = np.abs((df[column] - df[column].mean()) / df[column].std())
        df = df[z_scores < threshold]
    
    return df


def get_cleaning_summary(df_original: pd.DataFrame, df_cleaned: pd.DataFrame) -> dict:
    """
    Get a summary of what was cleaned.
    
    Args:
        df_original: Original DataFrame before cleaning
        df_cleaned: Cleaned DataFrame after cleaning
        
    Returns:
        Dictionary with cleaning statistics
    """
    summary = {
        'original_rows': len(df_original),
        'cleaned_rows': len(df_cleaned),
        'rows_removed': len(df_original) - len(df_cleaned),
        'original_columns': len(df_original.columns),
        'cleaned_columns': len(df_cleaned.columns),
        'missing_before': int(df_original.isna().sum().sum()),
        'missing_after': int(df_cleaned.isna().sum().sum()),
        'duplicates_removed': int(df_original.duplicated().sum()),
    }
    return summary
