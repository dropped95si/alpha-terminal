import pandas as pd

def evaluate_timeframes(df: pd.DataFrame) -> dict:
    """
    Resamples daily data to analyze trends across multiple horizons.
    Returns dict of trend directions.
    """
    summary = {}
    if len(df) < 20: return {"status": "INSUFFICIENT_DATA"}
    
    current_price = df['close'].iloc[-1]

    # 1. Short Term (Daily)
    sma_20 = df['close'].rolling(20).mean().iloc[-1]
    summary['trend_20d'] = "UP" if current_price > sma_20 else "DOWN"

    # 2. Medium Term (Weekly Resample) ~ 6 Months context
    df_weekly = df.resample('W').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'})
    if len(df_weekly) > 26:
        sma_weekly_26 = df_weekly['close'].rolling(26).mean().iloc[-1]
        summary['trend_6m'] = "UP" if df_weekly['close'].iloc[-1] > sma_weekly_26 else "DOWN"
    else:
        summary['trend_6m'] = "NEUTRAL"

    # 3. Long Term (Monthly Resample) ~ 12 Months context
    df_monthly = df.resample('ME').agg({'open':'first', 'high':'max', 'low':'min', 'close':'last'})
    if len(df_monthly) > 12:
        sma_monthly_12 = df_monthly['close'].rolling(12).mean().iloc[-1]
        summary['trend_12m'] = "UP" if df_monthly['close'].iloc[-1] > sma_monthly_12 else "DOWN"
    else:
        summary['trend_12m'] = "NEUTRAL"

    # Alignment Score (0 to 1)
    up_votes = sum(1 for k, v in summary.items() if v == "UP")
    summary['alignment_score'] = round(up_votes / 3, 2)

    return summary