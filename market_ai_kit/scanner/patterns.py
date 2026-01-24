import talib
import pandas as pd

def detect_patterns(df: pd.DataFrame) -> dict:
    """
    Scans for all TA-Lib candlestick patterns.
    Returns dict of {pattern_name: {score, sentiment}}
    """
    if len(df) < 100: return {}
    
    op, hi, lo, cl = df['open'].values, df['high'].values, df['low'].values, df['close'].values
    found_patterns = {}

    # Get all pattern functions from TA-Lib abstract API
    # Requires 'pip install ta-lib' or 'pip install talib-binary'
    pattern_names = talib.get_function_groups()['Pattern Recognition']
    
    for name in pattern_names:
        fn = getattr(talib, name)
        result = fn(op, hi, lo, cl)
        
        # Check only the last candle (-1)
        last_val = result[-1]
        if last_val != 0:
            sentiment = "BULL" if last_val > 0 else "BEAR"
            # TA-Lib returns 100/-100. We map to readable dict.
            found_patterns[name] = {
                "sentiment": sentiment,
                "score": int(last_val),
                "type": "CANDLESTICK"
            }

    return found_patterns