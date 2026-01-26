"""market_ai_kit.scanner.mode_defs

Three user-facing trading modes.

No hard rules.
- A "mode" only defines (a) the data resolution used to build the state
  and (b) the forward window (lookahead) used when estimating level-touch
  probabilities from historical paths.

The learner can still re-weight which sub-features matter inside each mode.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModeDef:
    name: str
    # yfinance-style interval strings (also accepted by our fetch_ohlcv adapter)
    interval: str
    # number of bars to look forward when estimating outcomes
    lookahead_bars: int
    # maximum history bars to keep for probability estimation
    max_history_bars: int


# Defaults match how you described trading:
# - Day: structure 15m + entry 3m. We estimate on 15m history (more stable)
#   and can later optionally fuse 3m features.
# - Swing: 4H/1D structure. We estimate on 1D history.
# - Long: weekly/monthly structure. We estimate on 1W history.
MODES: dict[str, ModeDef] = {
    "day": ModeDef(name="day", interval="15m", lookahead_bars=16, max_history_bars=2500),   # ~4 trading days of 15m bars
    "swing": ModeDef(name="swing", interval="1d", lookahead_bars=10, max_history_bars=4000), # ~10 days forward
    "long": ModeDef(name="long", interval="1wk", lookahead_bars=26, max_history_bars=6000),  # ~6 months forward
}


def list_modes() -> list[str]:
    return list(MODES.keys())
