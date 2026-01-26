import os
import requests
import yaml
from datetime import datetime, timezone
from market_ai_kit.scanner import data, risk_engine
from market_ai_kit.scanner.feature_engine import FeatureEngine
from market_ai_kit.scanner.probability_engine import ProbabilityEngine
from market_ai_kit.scanner.whale_sieve import WhaleValidator, apply_whale_boost
from market_ai_kit.scanner.adaptive_weighting import AdaptiveWeightingSystem, apply_credibility_multiplier

def analyze_ticker(ticker, cfg):
    # 1. Fetch & Feature Gen
    df = data.fetch_ohlcv(ticker)
    if df is None: return None
    
    feat_engine = FeatureEngine()
    df = feat_engine.transform(df)
    if df.empty: return None
    
    latest = df.iloc[-1].to_dict()
    latest['ticker'] = ticker
    
    # 2. Statistical Base Prob (V2.20 Logic)
    prob_engine = ProbabilityEngine()
    base_result = prob_engine.calculate_score(latest)
    
    # 3. Whale & Credibility Modifiers
    whale = WhaleValidator().validate_whale_flow(latest)
    whale_boosted = apply_whale_boost(base_result['probability'], whale)
    
    cred = AdaptiveWeightingSystem().assess_credibility(latest)
    final = apply_credibility_multiplier(whale_boosted['final_probability'], cred)

    # 4. Risk Engine
    risk = risk_engine.calculate_position(
        account_size=100000, 
        entry=latest['close'], 
        stop=latest['close'] * 0.95, 
        confidence=final['final_probability'] * 100
    )

    return {
        "ticker": ticker,
        "probability": final['final_probability'],
        "regime": base_result.get('regime_used'),
        "whale_verdict": whale['verdict'],
        "recommendation": cred['recommendation'],
        "shares": risk['shares'],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def main():
    print("--- 🚀 ALPHA TERMINAL V2.20 ---")
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f: cfg = yaml.safe_load(f)
    else: cfg = {}

    watchlist = ["NVDA", "TSLA", "AMD", "AAPL", "MSFT"]
    
    for ticker in watchlist:
        try:
            res = analyze_ticker(ticker, cfg)
            if res:
                print(f"✅ {ticker}: {res['probability']:.1%} [{res['whale_verdict']}]")
        except Exception as e:
            print(f"⚠️ {ticker}: {e}")

if __name__ == "__main__":
    main()