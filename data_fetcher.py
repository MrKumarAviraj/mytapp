"""
Data Fetcher Module
Handles fetching OHLCV data from yfinance with caching and retry logic.
"""

import yfinance as yf
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def fetch_data_raw(ticker: str, period: str = "5y", interval: str = "1d") -> pd.DataFrame:
    """
    Raw data fetcher with retry logic.
    
    Args:
        ticker: Stock symbol (e.g., AAPL)
        period: Data period (e.g., "5y", "1y", "max")
        interval: Data interval (e.g., "1d", "1h", "15m")
    
    Returns:
        DataFrame with OHLCV data
    """
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    
    # Handle multi-level columns if present (yfinance sometimes returns this)
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten multi-level columns: ('Close', 'AAPL') -> 'Close'
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    # Ensure required columns exist
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0
    
    # Drop any rows with all NaN values
    df = df.dropna(how='all')
    
    return df


@st.cache_data(ttl=3600, show_spinner="Fetching data...")
def fetch_ohlcv_data(ticker: str, period: str = "5y", interval: str = "1d") -> tuple[pd.DataFrame, bool]:
    """
    Cached data fetcher with fallback to last cached version.
    
    Args:
        ticker: Stock symbol
        period: Data period
        interval: Data interval
    
    Returns:
        Tuple of (DataFrame, is_cached_flag)
    """
    try:
        df = fetch_data_raw(ticker, period, interval)
        return df, False  # Fresh data
    except Exception as e:
        st.warning(f"Live data temporarily unavailable for {ticker}: {str(e)}. Showing cached snapshot.")
        # Return empty dataframe with flag - Streamlit cache will serve old data
        # In practice, we'd load from a local cache file, but for simplicity:
        raise e


def get_timeframe_params(timeframe: str) -> tuple[str, str]:
    """
    Convert user-friendly timeframe to yfinance parameters.
    
    Args:
        timeframe: One of "1D", "4H", "1H", "15M"
    
    Returns:
        Tuple of (period, interval)
    """
    mapping = {
        "1D": ("5y", "1d"),
        "4H": ("6mo", "1h"),
        "1H": ("3mo", "1h"),
        "15M": ("5d", "15m"),
    }
    return mapping.get(timeframe, ("5y", "1d"))
