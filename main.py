import yaml
from datetime import datetime, timezone
from market_ai_kit.scanner import data, indicators, learner, fib


def _analyze_ticker(ticker: str, cfg: dict, account_equity: float = 100000):
    # 1. Fetch 3-year history (Learning from the past)
    df = data.fetch_ohlcv(ticker, years=3)
    if df is None or len(df) < 200: return None
    df = indicators.add_indicators(df)

    # 2. Adaptive Probability (No Fixed Points)
    f_anchors = fib.auto_anchor(df)
    f_levels = fib.fib_levels(f_anchors['low'], f_anchors['high'])
    
    # Check what rule is currently winning for this stock
    prof = learner.build_indicator_profile(df, f_levels)
    best_rule = max(prof, key=lambda x: x['score'])
    base_prob = best_rule['score'] * 100 

    # 3. The Sentiment Multiplier (Probability Guardrail)
    sentiment = data.get_sentiment(ticker) # Returns -1 to 1
    # Panic (-0.5) drags 80% confidence down to 68%
    sentiment_weight = 1.0 + (sentiment * cfg['sentiment']['weight_impact'])

    # 4. Final Confidence Calculation
    confidence = base_prob * sentiment_weight
    
    # 5. Manual Alpha (The 'You' Signal)
    if data.check_manual_alpha(ticker): 
        confidence = max(confidence, 92.0)

    # 6. Risk Engine (Quarter-Kelly)
    price = df['close'].iloc[-1]
    stop = price - (df['atr_14'].iloc[-1] * cfg['rules']['atr_stop_buffer'])
    risk = risk_engine.calculate_position(account_equity, price, stop, confidence)

    return {
        "ticker": ticker,
        "confidence": round(confidence, 1),
        "shares": risk["shares"],
        "target": risk["target_3x"],
        "vol_z": round(df['vol_z'].iloc[-1], 2),
        "decision": "STRONG_BUY" if confidence >= 80 else "BUY" if confidence >= 65 else "WATCH"
    }