"""market_ai_kit.scanner.feature_engine

Soft-feature generator.

- No hard rules / thresholds.
- Produces continuous, mostly normalized features in [0, 1] or clipped z-scores.
- Works with only OHLCV, but can accept optional enrichments.

This module is intentionally light and robust. Anything we compute here becomes
*evidence*, never a rule.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def _safe_div(a: float, b: float, eps: float = 1e-9) -> float:
    return float(a) / float(b + eps)


def _clip01(x: float) -> float:
    return float(max(0.0, min(1.0, x)))


@dataclass
class FeatureSnapshot:
    features: Dict[str, float]
    meta: Dict[str, Any]


class FeatureEngine:
    """Compute soft features from an OHLCV dataframe.

    Expected columns: open, high, low, close, volume.
    Index: datetime-like.
    """

    def compute(self, df: pd.DataFrame, *, prefix: str = "") -> FeatureSnapshot:
        if df is None or len(df) < 50:
            return FeatureSnapshot(features={}, meta={"reason": "insufficient_history"})

        d = df.copy()
        # Standardize column names
        d.columns = [c.lower() for c in d.columns]

        close = d["close"].astype(float)
        high = d["high"].astype(float)
        low = d["low"].astype(float)
        vol = d["volume"].astype(float)

        # Returns
        r1 = close.pct_change().fillna(0.0)

        # Realized volatility proxy (rolling)
        vol20 = r1.rolling(20).std().fillna(method="bfill")
        vol60 = r1.rolling(60).std().fillna(method="bfill")

        # Volume z-score (rolling)
        vmean = vol.rolling(20).mean()
        vstd = vol.rolling(20).std()
        vol_z = ((vol - vmean) / (vstd + 1e-9)).clip(-3, 3)

        # Trend efficiency ratio (Kaufman-like) over 10 bars
        change = (close - close.shift(10)).abs()
        noise = (close.diff().abs().rolling(10).sum())
        trend_eff = (change / (noise + 1e-9)).clip(0, 1)

        # Range compression: current true range vs rolling median
        tr = (high - low).abs()
        tr_med = tr.rolling(50).median()
        compression = (1.0 - (tr / (tr_med + 1e-9))).clip(0, 1)

        # Position inside recent range
        look = 50
        rh = high.rolling(look).max()
        rl = low.rolling(look).min()
        range_pos = ((close - rl) / (rh - rl + 1e-9)).clip(0, 1)

        # "Acceptance" proxy: time spent near last close (low dispersion)
        # Lower rolling std of close -> more acceptance/balance
        accept = (1.0 - (close.pct_change().rolling(20).std() / (close.pct_change().rolling(60).std() + 1e-9))).clip(0, 1)

        # "Rejection" proxy: wickiness (long wicks relative to body)
        body = (close - d["open"].astype(float)).abs()
        wick = (high - low) - body
        wickiness = (wick / (tr + 1e-9)).clip(0, 1)

        last = len(d) - 1
        feats: Dict[str, float] = {
            "range_pos": float(range_pos.iat[last]),
            "compression": float(compression.iat[last]),
            "trend_eff": float(trend_eff.iat[last]),
            "vol_z": float(vol_z.iat[last]),
            "rv_20": float(vol20.iat[last]),
            "rv_60": float(vol60.iat[last]),
            "acceptance": float(accept.iat[last]),
            "wickiness": float(wickiness.iat[last]),
        }

        # Normalize some into [0,1] where helpful
        feats["vol_z_norm"] = _clip01((feats["vol_z"] + 3.0) / 6.0)
        feats["rv_ratio"] = _clip01(_safe_div(feats["rv_20"], feats["rv_60"]) / 2.0)

        # Prefix for multi-resolution stacking (e.g., "15m_", "1d_")
        if prefix:
            feats = {f"{prefix}{k}": v for k, v in feats.items()}

        meta = {
            "rows": int(len(d)),
            "last_close": float(close.iat[last]),
        }
        return FeatureSnapshot(features=feats, meta=meta)


def merge_feature_snapshots(*snaps: FeatureSnapshot) -> FeatureSnapshot:
    feats: Dict[str, float] = {}
    meta: Dict[str, Any] = {}
    for s in snaps:
        feats.update(s.features)
        meta.update({f"{k}": v for k, v in (s.meta or {}).items() if k not in meta})
    return FeatureSnapshot(features=feats, meta=meta)
