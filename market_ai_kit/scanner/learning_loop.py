import pandas as pd
import numpy as np
import json
import os
from scipy.stats import spearmanr

class DynamicLearner:
    def __init__(self, weights_path='config/learned_weights.json'):
        self.weights_path = weights_path
        self.weights = {"BULL": {}, "BEAR": {}}
        # Load existing if available
        if os.path.exists(weights_path):
            with open(weights_path, 'r') as f: self.weights = json.load(f)

    def train(self, history_df: pd.DataFrame):
        for regime in ['BULL', 'BEAR']:
            subset = history_df[history_df['regime'] == regime]
            if len(subset) < 30: continue 

            features = [c for c in ['vol_z', 'rsi'] if c in subset.columns]
            new_weights = {}
            total_score = 0.0

            for feat in features:
                # Spearman Rank Correlation (Anti-Overfit)
                ic, _ = spearmanr(subset[feat], subset['profit'])
                score = max(0.0, ic) # Only positive predictive power
                new_weights[feat] = score
                total_score += score

            if total_score > 0:
                for k in new_weights: new_weights[k] /= total_score
                self.weights[regime] = new_weights

        self._save_weights()

    def _save_weights(self):
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        with open(self.weights_path, 'w') as f: json.dump(self.weights, f, indent=2)