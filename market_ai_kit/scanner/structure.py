from __future__ import annotations

from typing import Dict, List

import pandas as pd


def pivot_levels(df: pd.DataFrame, window: int = 5) -> Dict[str, List[float]]:
    highs = df["high"]
    lows = df["low"]

    pivots_high = highs[(highs.shift(window) < highs) & (highs.shift(-window) < highs)]
    pivots_low = lows[(lows.shift(window) > lows) & (lows.shift(-window) > lows)]

    return {
        "resistance": [float(x) for x in pivots_high.tail(5).values],
        "support": [float(x) for x in pivots_low.tail(5).values],
    }


def recent_range(df: pd.DataFrame, lookback: int = 60) -> Dict[str, float]:
    d = df.tail(lookback)
    return {
        "range_low": float(d["low"].min()),
        "range_high": float(d["high"].max()),
    }
