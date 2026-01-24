from __future__ import annotations

import argparse
from datetime import datetime, timezone
from typing import Dict, List

import yaml

from .data import fetch_ohlcv, avg_dollar_volume, last_price
from .fib import auto_anchor, fib_levels
from .indicators import add_indicators
from .learner import build_indicator_profile
from .structure import pivot_levels, recent_range
from .universe import build_universe
from .utils import write_json
from .scorer import relative_strength
from .auto_tune import tune_thresholds
from .report import write_report


def _industry_rank(cfg: Dict) -> List[Dict]:
    etfs = cfg["universe"]["core_etfs"]
    items = []
    for t in etfs:
        df = fetch_ohlcv(t, years=int(cfg["scan"]["history_years"]), interval=cfg["scan"]["interval"])
        if df is None or len(df) < 200:
            continue
        d = add_indicators(df).dropna()
        last = d.iloc[-1]
        score = 0.0
        score += 1.0 if last["close"] > last["sma_50"] else 0.0
        score += 1.0 if last["close"] > last["sma_200"] else 0.0
        score += float(d["close"].iloc[-1] / d["close"].iloc[-60] - 1.0)
        items.append({"ticker": t, "score": score})
    items.sort(key=lambda x: x["score"], reverse=True)
    return items


def _entry_plan(df_ind: "pd.DataFrame", pivots: Dict, rng: Dict[str, float], best_rules: List[Dict], cfg: Dict) -> Dict:
    import pandas as pd
    d = df_ind
    last = d.iloc[-1]
    atr = float(last.get("atr_14", 0.0) or 0.0)

    # Decide style based on best rule name
    style = "value"
    if best_rules:
        name = best_rules[0].get("rule", "")
        if "BREAKOUT" in name or "MA_CROSS" in name:
            style = "breakout"

    if style == "breakout":
        trigger = float(rng["range_high"])
        stop = float(max(rng["range_low"], trigger - 2.5 * atr)) if atr > 0 else float(rng["range_low"])
        t1 = float(trigger + cfg["rules"]["target_r_multiple_1"] * atr) if atr > 0 else float(trigger * 1.08)
        t2 = float(trigger + cfg["rules"]["target_r_multiple_2"] * atr) if atr > 0 else float(trigger * 1.20)
        return {
            "entry": {
                "type": "breakout_confirmation",
                "trigger": round(trigger, 2),
                "why": ["Best learned rule suggests breakout/confirmation works for this ticker"]
            },
            "exit_if_wrong": {
                "stop": round(stop, 2),
                "why": ["Break below structure / ATR-based risk"]
            },
            "targets": [
                {"price": round(t1, 2), "why": "First step target (ATR multiple)"},
                {"price": round(t2, 2), "why": "Second step target (ATR multiple)"}
            ]
        }

    # value style (FV-based)
    fv = float(last.get("fv_vwap_20", last["close"]))
    fv_low = float(last.get("fv_low", fv))
    fv_high = float(last.get("fv_high", fv))

    zone_low = float(max(rng["range_low"], fv_low))
    zone_high = float(min(rng["range_high"], fv_high))
    stop = float(max(rng["range_low"], zone_low - 1.5 * atr)) if atr > 0 else float(rng["range_low"])
    t1 = float(zone_high + cfg["rules"]["target_r_multiple_1"] * atr) if atr > 0 else float(rng["range_high"])
    t2 = float(zone_high + cfg["rules"]["target_r_multiple_2"] * atr) if atr > 0 else float(rng["range_high"] * 1.15)

    return {
        "entry": {
            "type": "value_zone",
            "zone": {"low": round(zone_low, 2), "high": round(zone_high, 2)},
            "why": ["Best learned rule suggests value/mean-reversion entries work for this ticker"]
        },
        "exit_if_wrong": {
            "stop": round(stop, 2),
            "why": ["Break below value zone / ATR buffer"]
        },
        "targets": [
            {"price": round(t1, 2), "why": "First step target (ATR multiple)"},
            {"price": round(t2, 2), "why": "Second step target (ATR multiple)"}
        ]
    }

def run(cfg_path: str) -> None:
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    years = int(cfg["scan"]["history_years"])
    interval = cfg["scan"]["interval"]
    min_price = float(cfg["scan"]["min_price"])
    min_dollar_vol = float(cfg["scan"]["min_avg_dollar_volume"])
    max_cards = int(cfg["scan"]["max_cards_total"])

    uni = build_universe(cfg)
    tickers = uni["scan_list"]

    # --- Auto-tune thresholds based on current scan universe ---
    preview = []
    for t in tickers:
        df0 = fetch_ohlcv(t, years=years, interval=interval)
        if df0 is None or len(df0) < 220:
            continue
        p0 = last_price(df0)
        if p0 < min_price:
            continue
        adv0 = avg_dollar_volume(df0, days=20)
        if adv0 < min_dollar_vol:
            continue
        d0 = add_indicators(df0).dropna()
        if d0.empty:
            continue
        rng0 = recent_range(df0, lookback=int(cfg["rules"]["ready_breakout_lookback_days"]))
        volz0 = float(d0["vol_z"].iloc[-1]) if "vol_z" in d0.columns else 0.0
        atr0 = float(d0["atr_14"].iloc[-1]) if "atr_14" in d0.columns else 0.0
        preview.append({"ticker": t, "price": float(p0), "vol_z": float(volz0), "atr": float(atr0),
                        "range_high": float(rng0["range_high"]), "range_low": float(rng0["range_low"])})
    thr = tune_thresholds(preview, cfg)


    # benchmark for relative strength
    spy = fetch_ohlcv("SPY", years=years, interval=interval)
    if spy is None or len(spy) < 200:
        raise RuntimeError("Failed to download SPY benchmark from Yahoo")

    industries = _industry_rank(cfg)

    early: List[Dict] = []
    ready: List[Dict] = []
    watch: List[Dict] = []
    profiles: List[Dict] = []

    now = datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

    for t in tickers:
        df = fetch_ohlcv(t, years=years, interval=interval)
        if df is None or len(df) < 220:
            continue

        price = last_price(df)
        if price < min_price:
            continue

        adv = avg_dollar_volume(df, days=20)
        if adv < min_dollar_vol:
            continue

        d = add_indicators(df).dropna()
        if d.empty:
            continue

        rng = recent_range(df, lookback=int(cfg["rules"]["ready_breakout_lookback_days"]))
        pivots = pivot_levels(df)

        # fib
        anc = auto_anchor(df, lookback=120)
        fibs = fib_levels(anc["low"], anc["high"])

        # learning
        prof = build_indicator_profile(d, fibs)
        top_rules = prof.get("top_rules", [])
        profiles.append({"ticker": t, "as_of": now, **prof})

        # emerging score
        rs = relative_strength(df, spy, lookback_days=int(cfg["rules"]["early_rs_lookback_days"]))
        vol_z = float(d["vol_z"].iloc[-1]) if "vol_z" in d.columns else 0.0

        # FV (Fair Value) zone
        trigger = float(rng["range_high"])
        near_pct = float(thr.near_breakout_pct)

        fv = float(d["fv_vwap_20"].iloc[-1]) if "fv_vwap_20" in d.columns else float(price)
        fv_low = float(d["fv_low"].iloc[-1]) if "fv_low" in d.columns else float(price)
        fv_high = float(d["fv_high"].iloc[-1]) if "fv_high" in d.columns else float(price)

        # READY = breakout confirmed + volume confirm + not too extended vs FV
        is_breakout = price >= trigger
        not_too_extended = price <= (fv_high + float(thr.fv_max_extension_atr) * float(d['atr_14'].iloc[-1]))
        is_ready = is_breakout and not_too_extended and (vol_z >= float(thr.vol_z_min))

        # EARLY = RS improving OR near breakout, but not ready yet
        is_near = price >= trigger * near_pct
        is_early = ((rs >= float(cfg["rules"]["early_rs_min"])) or is_near) and not is_ready
        plan = _entry_plan(d, pivots, rng, top_rules, cfg)

        card = {
            "ticker": t,
            "price": round(price, 2),
            "avg_dollar_volume": int(adv),
            "rs_60d_vs_spy": round(rs, 4),
            "vol_z": round(vol_z, 2),
            "fv": {"vwap_20": round(fv, 2), "low": round(fv_low, 2), "high": round(fv_high, 2)},
            "range": {"low": round(rng["range_low"], 2), "high": round(rng["range_high"], 2)},
            "pivots": pivots,
            "fib": {"anchor": anc, "levels": {k: round(v, 2) for k, v in fibs.items()}},
            "plan": plan,
            "learned_top_rules": top_rules[:3],
            "labels": [],
            "as_of": now,
        }

        if t in uni["china_watchlist"]:
            card["labels"].append("CHINA_HIGH_HEADLINE_RISK")

        if is_ready:
            card["labels"].append("READY_CONFIRMED")
            ready.append(card)
        elif is_early:
            card["labels"].append(cfg["mom_safe"]["early_label"])
            early.append(card)
        else:
            card["labels"].append("WATCH")
            watch.append(card)

    # Sort ready/early by RS then vol_z
    ready.sort(key=lambda x: (x["rs_60d_vs_spy"], x["vol_z"]), reverse=True)
    early.sort(key=lambda x: (x["rs_60d_vs_spy"], x["vol_z"]), reverse=True)

    ready = ready[:max_cards]
    early = early[:max_cards]

    auto_meta = {"vol_z_min": thr.vol_z_min, "near_breakout_pct": thr.near_breakout_pct, "fv_max_extension_atr": thr.fv_max_extension_atr, "ready_confirm_closes": thr.ready_confirm_closes}

    industries_json = {"as_of": now, "auto_thresholds": auto_meta, "rankings": industries}
    write_json(industries_json, "output/industries.json")
    early_json = {"as_of": now, "auto_thresholds": auto_meta, "cards": early}
    write_json(early_json, "output/early.json")
    ready_json = {"as_of": now, "auto_thresholds": auto_meta, "cards": ready}
    write_json(ready_json, "output/ready.json")
    watch_json = {"as_of": now, "auto_thresholds": auto_meta, "cards": watch[:max_cards]}
    write_json(watch_json, "output/watch.json")
    profiles_json = {"as_of": now, "auto_thresholds": auto_meta, "profiles": profiles}
    write_json(profiles_json, "output/ticker_indicator_profiles.json")

    write_report("output", industries_json, early_json, ready_json)

    # --- Build full payload for Supabase ingestion (scan_runs + signals) ---
    def _to_signal(card: Dict) -> Dict:
        # labels is an array; Supabase schema expects a single label string
        label = "WATCH"
        if card.get("labels"):
            label = card["labels"][0]

        # plan is already a dict with entry/exit_if_wrong/targets
        plan = card.get("plan", {}) or {}

        entry = plan.get("entry", {}) or {}
        stop = plan.get("exit_if_wrong", {}) or {}
        targets = plan.get("targets", []) or []

        # Normalize to your Supabase schema fields
        return {
            "ticker": card.get("ticker"),
            "label": label,
            "plan_type": entry.get("type", "unknown"),
            "entry": entry,
            "stop": stop,
            "targets": targets,
            "rs_vs_spy": card.get("rs_60d_vs_spy"),
            "vol_z": card.get("vol_z"),
            "fv": card.get("fv"),
            "pivots": card.get("pivots"),
            "fib": card.get("fib"),
            "learned_top_rules": card.get("learned_top_rules"),
        }

    all_cards: List[Dict] = []
    all_cards.extend(ready)
    all_cards.extend(early)
    all_cards.extend(watch[:max_cards])

    full_payload = {
        "as_of": now,
        "source": "yahoo",
        "interval": interval,
        "history_years": years,
        "auto_thresholds": auto_meta,
        "signals": [_to_signal(c) for c in all_cards],
    }

    write_json(full_payload, "output/full_scan_payload.json")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()

