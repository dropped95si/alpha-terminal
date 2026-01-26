"""
Alpha Terminal v2.2 Audit CLI
Uses EnhancedV22Engine to analyze single tickers with full probability breakdown
"""

from __future__ import annotations

import argparse
import json
from typing import Dict, Any

from market_ai_kit.scanner.data import fetch_ohlcv
from market_ai_kit.scanner.indicators import add_indicators
from market_ai_kit.scanner.v22_enhanced_wrapper import EnhancedV22Engine


def _fmt_pct(x: float | None) -> str:
    """Format float as percentage"""
    if x is None:
        return "NA"
    if isinstance(x, float):
        return f"{x*100:.1f}%"
    return str(x)


def audit_one(ticker: str, years: int = 10, interval: str = "1d") -> Dict[str, Any]:
    """
    Analyze one ticker through full v2.2 pipeline
    
    Returns dict with:
    - regime, p_up, confidence (math layer)
    - whale_verdict, whale_boost (institutional layer)
    - credibility, recommendation (credibility layer)
    - drivers (what drove the signal)
    - raw (full payload for debugging)
    """
    
    # 1. Fetch data
    df = fetch_ohlcv(ticker, years=years, interval=interval)
    if df is None or df.empty:
        return {"ticker": ticker, "error": "no data"}

    # 2. Add indicators
    df = add_indicators(df).dropna()
    if df.empty:
        return {"ticker": ticker, "error": "no indicators"}

    # 3. Get latest card
    latest = df.iloc[-1].to_dict()
    latest["ticker"] = ticker

    # 4. Run through enhanced engine
    engine = EnhancedV22Engine()
    odds = engine.score_with_enhancements(latest, config={})

    # 5. Extract values (with fallbacks for different structures)
    swing = odds.get("swing", {}) or {}
    probs = swing.get("probs", {}) or {}
    
    regime = swing.get("regime") or odds.get("regime") or "UNKNOWN"
    confidence = swing.get("confidence") or odds.get("confidence")
    p_up = probs.get("p_up") or swing.get("p_up") or odds.get("probability")

    whale = odds.get("whale", {}) or {}
    cred = odds.get("credibility", {}) or {}

    return {
        "ticker": ticker,
        # Math layer
        "regime": regime,
        "p_up": p_up,
        "confidence": confidence,
        # Whale layer
        "whale_verdict": whale.get("verdict"),
        "whale_boost": whale.get("boost"),
        "whale_conviction": whale.get("conviction"),
        # Credibility layer
        "credibility": cred.get("credibility_score") or cred.get("credibility") or cred.get("score"),
        "risk_level": cred.get("risk_assessment"),
        "recommendation": cred.get("recommendation"),
        # Drivers
        "drivers": swing.get("drivers") or swing.get("features") or [],
        # Full payload for debugging
        "raw": odds,
    }


def print_signal(r: Dict[str, Any]) -> None:
    """Pretty-print an audit result"""
    
    if r.get("error"):
        print(f"⚠️  {r['ticker']}: {r['error']}")
        return

    ticker = r['ticker']
    rec = r.get('recommendation', 'UNKNOWN')
    
    print(f"\n🔎 {ticker} [{rec}]")
    print(f"   ⚙️  Regime: {r.get('regime', 'N/A')}")
    print(f"   🎯 Probability: {_fmt_pct(r.get('p_up'))} | Confidence: {_fmt_pct(r.get('confidence'))}")
    
    whale_v = r.get('whale_verdict', 'N/A')
    whale_boost = r.get('whale_boost')
    if whale_boost is not None:
        print(f"   🐋 Whale: {whale_v} (boost: {_fmt_pct(whale_boost)})")
    else:
        print(f"   🐋 Whale: {whale_v}")
    
    cred = r.get('credibility')
    risk = r.get('risk_level', 'N/A')
    if cred is not None:
        print(f"   ✅ Credibility: {_fmt_pct(cred)} | Risk: {risk}")
    else:
        print(f"   ✅ Risk: {risk}")
    
    # Drivers
    drivers = r.get('drivers') or []
    if drivers:
        if isinstance(drivers, list):
            driver_str = ", ".join([str(d) for d in drivers[:3]])
        else:
            driver_str = str(drivers)
        print(f"   🧠 Drivers: {driver_str}")


def main():
    ap = argparse.ArgumentParser(
        description="Alpha Terminal v2.2 Audit CLI - Deep analysis of signals using EnhancedV22Engine"
    )
    ap.add_argument(
        "--tickers",
        nargs="+",
        default=["NVDA", "TSLA", "AMD", "AAPL", "MSFT"],
        help="Tickers to audit"
    )
    ap.add_argument(
        "--years",
        type=int,
        default=10,
        help="Years of historical data to load"
    )
    ap.add_argument(
        "--interval",
        type=str,
        default="1d",
        help="Bar interval (1d, 1h, etc)"
    )
    ap.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON (one object per line)"
    )
    args = ap.parse_args()

    print("=" * 70)
    print("🧠 ALPHA TERMINAL V2.2 AUDIT CLI")
    print("=" * 70)
    print(f"\nScanning: {', '.join(args.tickers)}")
    print(f"History: {args.years}y | Interval: {args.interval}")
    print("-" * 70)

    for t in args.tickers:
        r = audit_one(t, years=args.years, interval=args.interval)

        if args.json:
            print(json.dumps(r, indent=2, default=str))
        else:
            print_signal(r)

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
