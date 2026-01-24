from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd
import yfinance as yf

# New imports for V2 Connectors
import os
from supabase import create_client, Client

def fetch_ohlcv(ticker: str, years: int = 3, interval: str = "1d") -> Optional[pd.DataFrame]:
    period = f"{years}y"
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, group_by="column", progress=False)
    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    df = df.loc[:, ~pd.Index(df.columns).duplicated()].copy()
    df = df.rename(columns={
        "Open": "open", "High": "high", "Low": "low", "Close": "close", "Adj Close": "adj_close", "Volume": "volume"
    })
    df.index = pd.to_datetime(df.index)
    return df

def avg_dollar_volume(df: pd.DataFrame, days: int = 20) -> float:
    d = df.tail(days)
    if d.empty:
        return 0.0
    return float((d["close"] * d["volume"]).mean())

def last_price(df: pd.DataFrame) -> float:
    return float(df["close"].iloc[-1])

# --- V2 ADAPTIVE CONNECTORS ---

def get_sentiment(ticker: str) -> float:
    """
    📰 THE COMMON SENSE FILTER
    Returns a score from -1.0 (Panic) to 1.0 (Euphoria).
    If no news is found, returns 0.0 (Neutral).
    """
    # Logic placeholder for News/Social API integration
    # Currently used as a probability multiplier in main.py
    return 0.0 

def check_manual_alpha(ticker: str) -> bool:
    """
    🎯 THE 'YOU' SIGNAL
    Queries Supabase to see if you have manually flagged this ticker for Mom.
    """
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        supabase: Client = create_client(url, key)
        
        # Check the 'candidates' table for your manual flag
        res = supabase.table("candidates").select("is_manual_alpha").eq("ticker", ticker).execute()
        if res.data and len(res.data) > 0:
            return bool(res.data[0].get("is_manual_alpha", False))
    except Exception:
        return False
    return False
