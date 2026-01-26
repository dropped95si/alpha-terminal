"""market_ai_kit.scanner.level_probability

Pure statistical level-reach estimation.

No hard rules.
We estimate level-touch odds from historical paths using simple, robust
barrier-touch counting.

This works even without explicit "trade outcomes" tables:
- we use OHLCV to label whether a path would have touched an upper / lower
  barrier within a lookahead window.

If both barriers touch in the same window, we mark it as "both" (uncertain).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class LevelOdds:
    p_up: float
    p_down: float
    p_chop: float
    p_both: float
    n: int


def _touches_in_window(df: pd.DataFrame, start_idx: int, lookahead: int, up: float, dn: float) -> Tuple[bool, bool]:
    """Return (touched_up, touched_down) within window [start_idx+1, start_idx+lookahead]."""
    w = df.iloc[start_idx + 1 : start_idx + 1 + lookahead]
    if w.empty:
        return False, False
    hi = float(w["high"].max())
    lo = float(w["low"].min())
    return hi >= up, lo <= dn


def estimate_level_odds(df: pd.DataFrame, *, up: float, dn: float, lookahead: int, stride: int = 3) -> LevelOdds:
    """Estimate barrier-touch probabilities from historical OHLCV.

    Parameters
    ----------
    df : pd.DataFrame
        Must have columns open/high/low/close/volume.
    up, dn : float
        Barrier prices.
    lookahead : int
        Number of future bars to evaluate.
    stride : int
        Step size through history (trade-off between speed and sample size).
    """
    if df is None or len(df) < (lookahead + 50):
        return LevelOdds(p_up=0.0, p_down=0.0, p_chop=1.0, p_both=0.0, n=0)

    d = df.copy()
    d.columns = [c.lower() for c in d.columns]

    up_hits = 0
    dn_hits = 0
    both = 0
    neither = 0

    # sample through history
    last_start = len(d) - lookahead - 2
    for i in range(0, last_start, max(1, int(stride))):
        tu, td = _touches_in_window(d, i, lookahead, up, dn)
        if tu and td:
            both += 1
        elif tu:
            up_hits += 1
        elif td:
            dn_hits += 1
        else:
            neither += 1

    n = up_hits + dn_hits + both + neither
    if n == 0:
        return LevelOdds(p_up=0.0, p_down=0.0, p_chop=1.0, p_both=0.0, n=0)

    p_up = up_hits / n
    p_down = dn_hits / n
    p_both = both / n
    p_chop = neither / n

    return LevelOdds(p_up=float(p_up), p_down=float(p_down), p_chop=float(p_chop), p_both=float(p_both), n=int(n))


def expected_moves(df: pd.DataFrame, *, lookahead: int, stride: int = 3) -> Dict[str, float]:
    """Return robust expected move sizes over lookahead.

    Computes distribution of max-up and max-down moves (as % of start close).
    """
    if df is None or len(df) < (lookahead + 50):
        return {"e_up_pct": 0.0, "e_down_pct": 0.0, "p50_up_pct": 0.0, "p50_down_pct": 0.0}

    d = df.copy()
    d.columns = [c.lower() for c in d.columns]

    ups = []
    dns = []
    last_start = len(d) - lookahead - 2
    for i in range(0, last_start, max(1, int(stride))):
        start = float(d["close"].iloc[i])
        w = d.iloc[i + 1 : i + 1 + lookahead]
        if w.empty or start <= 0:
            continue
        up = (float(w["high"].max()) / start) - 1.0
        dn = 1.0 - (float(w["low"].min()) / start)
        ups.append(up)
        dns.append(dn)

    if not ups or not dns:
        return {"e_up_pct": 0.0, "e_down_pct": 0.0, "p50_up_pct": 0.0, "p50_down_pct": 0.0}

    ups = np.array(ups)
    dns = np.array(dns)

    return {
        "e_up_pct": float(np.mean(ups)),
        "e_down_pct": float(np.mean(dns)),
        "p50_up_pct": float(np.median(ups)),
        "p50_down_pct": float(np.median(dns)),
    }
