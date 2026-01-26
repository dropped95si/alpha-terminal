"""market_ai_kit.scanner.probability_v22

v2.2 Probability Engine: level-to-level odds board.

- No hard rules.
- Uses historical OHLCV + current state features.
- Produces probabilities for Day / Swing / Long modes.

This is deliberately modular:
- level_engine decides *which* levels to evaluate (questions)
- level_probability estimates barrier-touch probabilities from history
- feature_engine computes soft evidence features (for attribution + regime)

The first implementation uses robust historical path counting.
As your outcomes table fills, we can add an online learner that updates
weights and similarity filtering. Nothing in this file forces thresholds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import pandas as pd

from .data import fetch_ohlcv
from .feature_engine import FeatureEngine
from .level_engine import levels_from_card, next_levels
from .level_probability import estimate_level_odds, expected_moves
from .mode_defs import MODES


def _prefix_for_interval(interval: str) -> str:
    return interval.replace(" ", "").replace("/", "_") + "_"


def _infer_regime(features: Dict[str, float], *, prefix: str) -> Dict[str, Any]:
    """Soft regime inference.

    No hard thresholds: we compute smooth scores and pick the max.
    """
    # Pull a few robust features
    comp = float(features.get(prefix + "compression", 0.5))
    eff = float(features.get(prefix + "trend_eff", 0.5))
    rv = float(features.get(prefix + "rv_ratio", 0.5))

    # Smooth scores (bounded 0..1)
    trend_score = 0.55 * eff + 0.25 * rv + 0.20 * (1.0 - comp)
    chop_score = 0.55 * comp + 0.25 * (1.0 - eff) + 0.20 * (1.0 - rv)
    trans_score = 1.0 - abs(trend_score - chop_score)

    scores = {
        "trend": float(trend_score),
        "chop": float(chop_score),
        "transition": float(trans_score),
    }
    regime = max(scores, key=scores.get)
    conf = float(scores[regime])
    return {"type": regime, "confidence": round(conf, 3), "scores": {k: round(v, 3) for k, v in scores.items()}}


@dataclass
class ModeResult:
    mode: str
    interval: str
    lookahead_bars: int
    n_samples: int
    next_up: Optional[Dict[str, Any]]
    next_down: Optional[Dict[str, Any]]
    probs: Dict[str, float]
    moves: Dict[str, float]
    regime: Dict[str, Any]
    confidence: float
    features: Dict[str, float]


class ProbabilityEngineV22:
    def __init__(self):
        self.fe = FeatureEngine()

    def score_card(self, card: Dict[str, Any], *, history_years_default: int = 3) -> Dict[str, Any]:
        """Return v2.2 odds board for Day/Swing/Long.

        This is a pure math/statistics function.
        """
        ticker = card.get("ticker")
        price = float(card.get("price") or 0.0)
        levels = levels_from_card(card)
        nxt = next_levels(levels, price)

        out: Dict[str, Any] = {
            "ticker": ticker,
            "as_of": card.get("as_of"),
            "price": price,
            "levels": [l.__dict__ for l in levels],
            "next": {
                "up": nxt["next_up"].__dict__ if nxt["next_up"] else None,
                "down": nxt["next_down"].__dict__ if nxt["next_down"] else None,
            },
            "modes": {},
        }

        if not ticker or price <= 0 or (nxt["next_up"] is None and nxt["next_down"] is None):
            return out

        for mode_name, m in MODES.items():
            interval = m.interval
            # yfinance intraday limits: if asking for intraday, keep years small
            years = history_years_default
            if interval in ("1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h"):
                years = 1  # fetch_ohlcv should internally cap anyway

            df = fetch_ohlcv(ticker, years=years, interval=interval)
            if df is None or len(df) < 80:
                continue

            # features at this resolution
            prefix = _prefix_for_interval(interval)
            snap = self.fe.compute(df, prefix=prefix)
            regime = _infer_regime(snap.features, prefix=prefix)

            # Determine immediate next barriers
            up = float(nxt["next_up"].price) if nxt["next_up"] else None
            dn = float(nxt["next_down"].price) if nxt["next_down"] else None

            # If only one side exists, fabricate the other using symmetric move from history
            # (still no rules; it's derived from history distribution)
            move_stats = expected_moves(df, lookahead=m.lookahead_bars)
            p50_up = float(move_stats.get("p50_up_pct", 0.0))
            p50_dn = float(move_stats.get("p50_down_pct", 0.0))

            if up is None:
                up = price * (1.0 + max(0.01, p50_up))
            if dn is None:
                dn = price * (1.0 - max(0.01, p50_dn))

            odds = estimate_level_odds(df, up=up, dn=dn, lookahead=m.lookahead_bars)

            # Confidence: sample size + regime confidence + stability (1 - both)
            # All continuous.
            n_conf = min(1.0, odds.n / 800.0)
            stability = max(0.0, 1.0 - odds.p_both)
            confidence = round(0.45 * n_conf + 0.35 * float(regime["confidence"]) + 0.20 * stability, 3)

            out["modes"][mode_name] = {
                "interval": interval,
                "lookahead_bars": m.lookahead_bars,
                "n_samples": odds.n,
                "regime": regime,
                "next_up": {"id": nxt["next_up"].id if nxt["next_up"] else "derived", "price": round(float(up), 2)},
                "next_down": {"id": nxt["next_down"].id if nxt["next_down"] else "derived", "price": round(float(dn), 2)},
                "probs": {
                    "p_up": round(odds.p_up, 3),
                    "p_down": round(odds.p_down, 3),
                    "p_chop": round(odds.p_chop, 3),
                    "p_both": round(odds.p_both, 3),
                },
                "moves": {k: round(float(v), 4) for k, v in move_stats.items()},
                "confidence": confidence,
                # store features (soft evidence) for transparency / later learning
                "features": {k: round(float(v), 6) for k, v in snap.features.items()},
            }

        return out
