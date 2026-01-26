import json
import os

class ProbabilityEngine:
    def __init__(self, weights_path='config/learned_weights.json'):
        self.weights = {"BULL": {}, "BEAR": {}}
        if os.path.exists(weights_path):
            with open(weights_path, 'r') as f: self.weights = json.load(f)

    def calculate_score(self, signal_data: dict) -> dict:
        regime = signal_data.get('regime', 'BULL')
        active_weights = self.weights.get(regime, {})
        
        if not active_weights: return {'probability': 0.5, 'confidence': 'LOW'}

        score = 0.0
        total_weight = 0.0
        
        for feat, weight in active_weights.items():
            val = signal_data.get(feat, 0.5)
            score += val * weight
            total_weight += weight

        final_prob = score / total_weight if total_weight > 0 else 0.5
        return {'probability': round(final_prob, 3), 'regime_used': regime}