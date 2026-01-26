"""market_ai_kit.scanner.level_engine

Convert the scanner card (range/pivots/fib/plan) into a small set of
"levels". Levels are NOT targets and NOT rules. They are simply *questions*:

- what's the probability we reach the next upside level?
- what's the probability we break down to the next downside level?

We keep it minimal for robustness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class Level:
    id: str
    price: float
    kind: str  # support/resistance/anchor


def levels_from_card(card: Dict[str, Any]) -> List[Level]:
    """Derive a compact level ladder.

    Priority:
    - range high/low (recent_range)
    - best pivot resistance/support
    - fib extremes

    Returns levels sorted by price.
    """
    price = float(card.get("price") or 0.0)

    lvls: List[Level] = []

    rng = card.get("range") or {}
    r_low = rng.get("low")
    r_high = rng.get("high")
    if r_low is not None:
        lvls.append(Level(id="range_low", price=float(r_low), kind="support"))
    if r_high is not None:
        lvls.append(Level(id="range_high", price=float(r_high), kind="resistance"))

    piv = card.get("pivots") or {}
    sups = piv.get("support") or []
    ress = piv.get("resistance") or []
    # choose nearest support below and nearest resistance above
    try:
        sups = [float(x) for x in sups]
        ress = [float(x) for x in ress]
        below = [x for x in sups if x < price]
        above = [x for x in ress if x > price]
        if below:
            lvls.append(Level(id="pivot_support", price=max(below), kind="support"))
        if above:
            lvls.append(Level(id="pivot_resistance", price=min(above), kind="resistance"))
    except Exception:
        pass

    fib = card.get("fib") or {}
    anc = fib.get("anchor") or {}
    try:
        a_low = float(anc.get("low")) if anc.get("low") is not None else None
        a_high = float(anc.get("high")) if anc.get("high") is not None else None
        if a_low is not None:
            lvls.append(Level(id="fib_anchor_low", price=a_low, kind="support"))
        if a_high is not None:
            lvls.append(Level(id="fib_anchor_high", price=a_high, kind="resistance"))
    except Exception:
        pass

    # de-dup by rounded price
    dedup: Dict[float, Level] = {}
    for l in lvls:
        key = round(float(l.price), 2)
        # keep first occurrence (priority order above)
        if key not in dedup:
            dedup[key] = l

    out = sorted(dedup.values(), key=lambda x: x.price)
    return out


def next_levels(levels: List[Level], price: float) -> Dict[str, Optional[Level]]:
    """Pick immediate next up and next down levels around current price."""
    up = [l for l in levels if l.price > price]
    dn = [l for l in levels if l.price < price]
    return {
        "next_up": min(up, key=lambda l: l.price) if up else None,
        "next_down": max(dn, key=lambda l: l.price) if dn else None,
    }
