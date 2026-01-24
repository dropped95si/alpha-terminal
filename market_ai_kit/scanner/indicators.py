from __future__ import annotations

import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, SMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange, BollingerBands


def _ensure_series(x):
    # yfinance can sometimes return single-column DataFrames (shape: [n,1])
    # which breaks indicator libs expecting 1D Series.
    try:
        import pandas as pd
        if isinstance(x, pd.DataFrame):
            return x.iloc[:, 0]
    except Exception:
        pass
    return x



def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # drop duplicate columns / flatten if needed
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d = d.loc[:, ~pd.Index(d.columns).duplicated()].copy()

    # Coerce core columns to 1D Series
    for col in ["open","high","low","close","volume"]:
        if col in d.columns:
            d[col] = _ensure_series(d[col])

    # MA / EMA
    for n in [10, 20, 50, 200]:
        d[f"sma_{n}"] = SMAIndicator(d["close"], window=n).sma_indicator()
    for n in [10, 20, 50]:
        d[f"ema_{n}"] = EMAIndicator(d["close"], window=n).ema_indicator()

    # RSI
    d["rsi_14"] = RSIIndicator(d["close"], window=14).rsi()

    # MACD
    macd = MACD(d["close"], window_slow=26, window_fast=12, window_sign=9)
    d["macd"] = macd.macd()
    d["macd_signal"] = macd.macd_signal()
    d["macd_hist"] = macd.macd_diff()

    # ATR
    atr = AverageTrueRange(d["high"], d["low"], d["close"], window=14)
    d["atr_14"] = atr.average_true_range()


    # --- Fair Value (FV) proxy: VWAP(20) +/- ATR ---
    tp = (d["high"] + d["low"] + d["close"]) / 3.0
    vwap20 = (tp * d["volume"]).rolling(20).sum() / d["volume"].rolling(20).sum()
    d["fv_vwap_20"] = vwap20
    d["fv_low"] = d["fv_vwap_20"] - 1.0 * d["atr_14"]
    d["fv_high"] = d["fv_vwap_20"] + 1.0 * d["atr_14"]
    # Bollinger
    bb = BollingerBands(d["close"], window=20, window_dev=2)
    d["bb_mid"] = bb.bollinger_mavg()
    d["bb_high"] = bb.bollinger_hband()
    d["bb_low"] = bb.bollinger_lband()
    d["bb_width"] = (d["bb_high"] - d["bb_low"]) / d["bb_mid"]

    # Volume z-score
    mu = d["volume"].rolling(20).mean()
    sd = d["volume"].rolling(20).std().replace(0, np.nan)
    d["vol_z"] = (d["volume"] - mu) / sd

    return d
