"""
Data Loader Module
Loads and parses the COVID-19 CSV dataset into pandas DataFrame.
Provides function interfaces for GUI to interact with.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(filepath: str) -> pd.DataFrame:
    """
    Load COVID-19 CSV dataset into a pandas DataFrame.
    
    Args:
        filepath: Path to the CSV file
        
    Returns:
        DataFrame containing the loaded data
    """
    df = pd.read_csv(filepath, low_memory=False)
    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])
    return df


def get_columns_info(df: pd.DataFrame) -> list:
    """
    Get information about all columns in the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of dicts with column info: name, dtype, non-null count, null count
    """
    info = []
    for col in df.columns:
        info.append({
            'name': col,
            'dtype': str(df[col].dtype),
            'non_null': int(df[col].notna().sum()),
            'null_count': int(df[col].isna().sum()),
            'sample_values': df[col].dropna().unique()[:3].tolist()
        })
    return info


def select_columns(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Select specific columns from the DataFrame.
    
    Args:
        df: Input DataFrame
        columns: List of column names to select
        
    Returns:
        DataFrame with only the selected columns
    """
    available_cols = [c for c in columns if c in df.columns]
    return df[available_cols]


def get_countries(df: pd.DataFrame) -> list:
    """
    Get sorted list of unique countries.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Sorted list of country names
    """
    return sorted(df['country'].dropna().unique().tolist())


def get_continents(df: pd.DataFrame) -> list:
    """
    Get sorted list of unique continents.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Sorted list of continent names
    """
    return sorted(df['continent'].dropna().unique().tolist())


def get_date_range(df: pd.DataFrame) -> tuple:
    """
    Get the date range of the dataset.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Tuple of (min_date, max_date) as datetime objects
    """
    return (df['date'].min(), df['date'].max())


def get_numeric_columns(df: pd.DataFrame) -> list:
    """
    Get list of numeric columns suitable for analysis.
    
    Args:
        df: Input DataFrame
        
    Returns:
        List of numeric column names
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    # Remove ID-like columns
    exclude = ['code']
    return [c for c in numeric_cols if c not in exclude]


def get_data_preview(df: pd.DataFrame, n_rows: int = 10) -> pd.DataFrame:
    """
    Get a preview of the first n rows.
    
    Args:
        df: Input DataFrame
        n_rows: Number of rows to preview
        
    Returns:
        DataFrame with first n rows
    """
    return df.head(n_rows)


def get_basic_stats(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get basic statistical summary of numeric columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with descriptive statistics
    """
    numeric_df = df.select_dtypes(include=[np.number])
    return numeric_df.describe()
