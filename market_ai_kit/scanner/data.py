from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker: str, years: int = 3, interval: str = "1d") -> Optional[pd.DataFrame]:
    period = f"{years}y"
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=False, group_by="column", progress=False)
    if df is None or df.empty:
        return None

    # Fix yfinance edge-cases (MultiIndex columns or duplicate column names)
    if isinstance(df.columns, pd.MultiIndex):
        # keep first level names like Open/High/Low/Close/Adj Close/Volume
        df.columns = df.columns.get_level_values(0)
    # drop duplicate columns if any
    df = df.loc[:, ~pd.Index(df.columns).duplicated()].copy()
    # standardize columns
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
