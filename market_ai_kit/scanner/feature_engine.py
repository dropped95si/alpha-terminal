import pandas as pd
import pandas_ta as ta
import numpy as np
import yaml
import os

class FeatureEngine:
    def __init__(self, config_path="config.yaml"):
        self.cfg = {'features': [], 'learning': {'regime_window': 200}}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.cfg = yaml.safe_load(f)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or len(df) < 200: return df
        
        # Normalize Volatility (Z-Score)
        rolling_mean = df['volume'].rolling(20).mean()
        rolling_std = df['volume'].rolling(20).std()
        df['vol_z'] = (df['volume'] - rolling_mean) / (rolling_std + 1e-6)

        # Normalize Momentum (RSI)
        df['rsi'] = df.ta.rsi(length=14) / 100.0

        # Market Regime (Bull vs Bear)
        df['regime_ma'] = df.ta.sma(length=200)
        df['regime'] = np.where(df['close'] > df['regime_ma'], 'BULL', 'BEAR')

        return df.dropna()