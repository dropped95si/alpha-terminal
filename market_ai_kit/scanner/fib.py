from __future__ import annotations

from typing import Dict

import pandas as pd

FIBS = [0.382, 0.5, 0.618, 0.786]


def fib_levels(low: float, high: float) -> Dict[str, float]:
    out = {}
    for f in FIBS:
        out[str(f)] = float(high - (high - low) * f)
    return out


def auto_anchor(df: pd.DataFrame, lookback: int = 120) -> Dict[str, float]:
    d = df.tail(lookback)
    low = float(d['low'].min())
    high = float(d['high'].max())
    return {'low': low, 'high': high}
