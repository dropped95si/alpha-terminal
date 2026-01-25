from __future__ import annotations

"""Dynamic weight updater (learn-forward). Optional.

Run this after outcomes are recorded to update output/weights.json.
It is intentionally decoupled from the scan run, so the scanner stays fast and deterministic.

Env required (server-side):
  SUPABASE_URL
  SUPABASE_SERVICE_ROLE_KEY

You may need to adjust table/column names to match your Supabase schema.
"""

import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .probability_engine import load_weights, save_weights, _clamp


def _get_supabase():
    try:
        from supabase import create_client  # type: ignore
    except Exception as e:
        raise RuntimeError("Missing python package 'supabase'. Install it if you want weight updates via python.") from e

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)


def fetch_recent_outcomes(limit: int = 800) -> List[Dict[str, Any]]:
    sb = _get_supabase()
    # TODO: adjust table name + columns to your schema
    res = sb.table("outcomes").select("*").order("created_at", desc=True).limit(limit).execute()
    return res.data or []


def update_weights(weights: Dict[str, float], outcomes: List[Dict[str, Any]]) -> Dict[str, float]:
    if not outcomes:
        return weights

    # Guardrails (anti-overfit)
    step = 0.05
    cap = 0.20
    decay = 0.995
    min_samples = 30

    # Baseline win rate
    wins = 0
    for o in outcomes:
        wins += 1 if bool(o.get("is_win") or (o.get("result") == "win")) else 0
    base_win = wins / max(1, len(outcomes))

    # Aggregate factor mentions from stored 'why' (or store factor_breakdown later for precision)
    factor_wins: Dict[str, int] = {}
    factor_total: Dict[str, int] = {}

    for o in outcomes:
        is_win = bool(o.get("is_win") or (o.get("result") == "win"))
        why = o.get("why") or []
        if isinstance(why, str):
            why = [why]
        fired = []
        for line in why:
            if isinstance(line, str) and ":" in line:
                fired.append(line.split(":")[0].strip())
        for f in set(fired):
            factor_total[f] = factor_total.get(f, 0) + 1
            if is_win:
                factor_wins[f] = factor_wins.get(f, 0) + 1

    # Decay existing weights
    for k in list(weights.keys()):
        if k.startswith("factor."):
            weights[k] *= decay

    for f, tot in factor_total.items():
        if tot < min_samples:
            continue
        wr = factor_wins.get(f, 0) / tot
        delta = (wr - base_win) * step * 10.0
        delta = _clamp(delta, -cap, cap)
        key = f"factor.{f}"
        weights[key] = float(_clamp(weights.get(key, 1.0) + delta, 0.2, 3.0))

    return weights


def main():
    w = load_weights()
    outcomes = fetch_recent_outcomes()
    w2 = update_weights(w, outcomes)
    save_weights(w2)
    print("✅ Weights updated", datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    main()
