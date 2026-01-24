from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


def _forward_return(df: pd.DataFrame, horizon: int) -> pd.Series:
    return df["close"].shift(-horizon) / df["close"] - 1.0


def rule_ma_cross(df: pd.DataFrame) -> pd.Series:
    return (df["ema_20"] > df["ema_50"]) & (df["ema_20"].shift(1) <= df["ema_50"].shift(1))


def rule_breakout(df: pd.DataFrame, lookback: int = 60) -> pd.Series:
    hh = df["high"].rolling(lookback).max().shift(1)
    return (df["close"] > hh) & (df["vol_z"] > 1.0)


def rule_fib_bounce(df: pd.DataFrame, fib_level: float, tol: float = 0.01) -> pd.Series:
    # Signal when low touches within tolerance of fib level and close recovers above fib level
    touched = (df["low"] <= fib_level * (1 + tol)) & (df["low"] >= fib_level * (1 - tol))
    recover = df["close"] > fib_level
    return touched & recover


RULES = {
    "MA_CROSS_EMA20_50": rule_ma_cross,
    "BREAKOUT_VOL": rule_breakout,
}


def score_rule(df: pd.DataFrame, signal: pd.Series, horizon: int = 60) -> Optional[Dict]:
    sig = signal.fillna(False)
    if int(sig.sum()) < 5:
        return None
    fwd = _forward_return(df, horizon)
    r = fwd[sig].dropna()
    if len(r) < 5:
        return None
    win_rate = float((r > 0).mean())
    avg_return = float(r.mean())
    return {
        "signals": int(sig.sum()),
        "samples": int(len(r)),
        "win_rate": win_rate,
        "avg_return": avg_return,
        "expectancy": avg_return,
    }


def build_indicator_profile(df: pd.DataFrame, fibs: Dict[str, float]) -> Dict:
    scores: List[Dict] = []

    for name, fn in RULES.items():
        sig = fn(df)
        s60 = score_rule(df, sig, horizon=60)
        s90 = score_rule(df, sig, horizon=90)
        if s60 or s90:
            scores.append({
                "rule": name,
                "h60": s60,
                "h90": s90,
                "score": float((s60 or {}).get("expectancy", 0.0) * 0.6 + (s90 or {}).get("expectancy", 0.0) * 0.4),
            })

    # Fib bounce rules
    for k, lvl in fibs.items():
        sig = rule_fib_bounce(df, lvl)
        s60 = score_rule(df, sig, horizon=60)
        if s60:
            scores.append({
                "rule": f"FIB_BOUNCE_{k}",
                "h60": s60,
                "h90": None,
                "score": float(s60.get("expectancy", 0.0)),
            })

    scores.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    top = scores[:5]
    return {
        "top_rules": top,
        "rules_tested": len(scores),
    }
