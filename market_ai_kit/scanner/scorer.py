from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def relative_strength(df: pd.DataFrame, benchmark: pd.DataFrame, lookback_days: int = 60) -> float:
    a = df["close"].tail(lookback_days)
    b = benchmark["close"].tail(lookback_days)
    if len(a) < lookback_days or len(b) < lookback_days:
        return 0.0
    ra = float(a.iloc[-1] / a.iloc[0] - 1.0)
    rb = float(b.iloc[-1] / b.iloc[0] - 1.0)
    return ra - rb


def mom_score(df: pd.DataFrame) -> float:
    last = df.iloc[-1]
    score = 0.0
    if not pd.isna(last.get("sma_50")) and last["close"] > last.get("sma_50", 0):
        score += 1.0
    if not pd.isna(last.get("sma_200")) and last["close"] > last.get("sma_200", 0):
        score += 1.0
    # short-term return boost
    if len(df) >= 60:
        score += float(df["close"].iloc[-1] / df["close"].iloc[-60] - 1.0)
    return score
