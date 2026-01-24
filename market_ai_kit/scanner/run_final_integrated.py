"""
🚀 ALPHA TERMINAL - MODERN SCANNER (INTEGRATED)
Stack: TA-Lib Patterns + Multi-Timeframe + Timeout Logic + Outcomes DB
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from typing import Dict, List
import yaml
import pandas as pd

# Core Modules
from .data import fetch_ohlcv, last_price
from .indicators import add_indicators
from .learner import build_indicator_profile
from .universe import build_universe
from .utils import write_json

# MODERN IMPORTS
try:
    from . import patterns_talib
    from . import multi_timeframe
    from . import timeout
    from . import outcomes_integration
    MODERN_STACK = True
except ImportError:
    print("⚠️ Modern Stack libraries missing. Falling back.")
    MODERN_STACK = False

def _to_signal(card: Dict) -> Dict:
    return {
        "ticker": card.get("ticker"),
        "date": card.get("as_of"),
        "price": card.get("price"),
        "signal": card.get("signal"),
        "signal_type": card.get("signal_type", "UNKNOWN"),
        "confidence": card.get("confidence", 0),
        "decision": card.get("decision", "WATCH"),
        "patterns": card.get("patterns_detected", {}),
        "macro_trends": card.get("macro_trends", {}),
        "exit_plan": card.get("exit_plan", {}),
        "learned_top_rules": card.get("learned_top_rules", []),
    }

def _scan_ticker(ticker: str, cfg: Dict) -> Dict:
    interval = cfg["scan"].get("interval", "1d")
    history_years = int(cfg["scan"].get("history_years", 2))
    
    df = fetch_ohlcv(ticker, years=history_years, interval=interval)
    if df is None or len(df) < 200: return {}

    df = add_indicators(df)
    
    # MODERN LOGIC
    patterns = patterns_talib.detect_patterns(df) if MODERN_STACK else {}
    macro_trends = multi_timeframe.evaluate_timeframes(df) if MODERN_STACK else {}
    prof = build_indicator_profile(df, cfg)
    
    if prof.get('signal'): 
        base_confidence = prof.get('confidence', 50)
        if MODERN_STACK:
            for p_name in patterns:
                base_confidence = outcomes_integration.get_learned_confidence(p_name, base_confidence)
            prof['exit_plan'] = timeout.get_timeout_rules(prof.get('signal_type', 'SWING'))
            outcomes_integration.record_signal_for_tracking({
                "ticker": ticker, "entry": last_price(df), "patterns": patterns
            })
        
        prof['confidence'] = base_confidence
        prof['patterns_detected'] = patterns
        prof['macro_trends'] = macro_trends
        prof['ticker'] = ticker
        prof['price'] = last_price(df)
        prof['as_of'] = datetime.now(timezone.utc).isoformat()
        
        if prof['confidence'] >= 80: prof['decision'] = "STRONG_BUY"
        elif prof['confidence'] >= 60: prof['decision'] = "BUY"
        else: prof['decision'] = "WATCH"

    return prof

def run_scan(config_path: str = "config.yaml"):
    with open(config_path) as f: cfg = yaml.safe_load(f)
    tickers = build_universe(cfg)
    ready = []

    print(f"🚀 STARTING MODERN SCAN: {len(tickers)} tickers")
    for t in tickers:
        try:
            res = _scan_ticker(t, cfg)
            if res and res.get('signal'):
                ready.append(res)
                print(f"   ✅ {t}: {list(res.get('patterns_detected', {}).keys())} | Conf: {res['confidence']}%")
        except Exception: pass

    full_payload = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "source": "yahoo",
        "signals": [_to_signal(c) for c in ready]
    }
    
    write_json(full_payload, "output/full_scan_payload.json")
    write_json([_to_signal(c) for c in ready], "output/ready.json")
    print(f"\n✅ SCAN COMPLETE. Found {len(ready)} signals.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()
    run_scan(args.config)