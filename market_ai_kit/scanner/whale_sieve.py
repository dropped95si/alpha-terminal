from typing import Dict
from enum import Enum
import yaml
import os

class WhaleVerdict(Enum):
    CONFIRM = "CONFIRM"
    WATCH = "WATCH"
    NEUTRAL = "NEUTRAL"
    DENY = "DENY"

class WhaleValidator:
    def __init__(self, config_path="config.yaml"):
        self.cfg = {}
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.cfg = yaml.safe_load(f).get('whale_sieve', {})
        self.weights = self.cfg.get('conviction_weights', {})
        self.sizes = self.cfg.get('block_thresholds', {})
        self.impact = self.cfg.get('impact', {})

    def validate_whale_flow(self, signal_data: Dict) -> Dict:
        # Fallback if config is missing or simple Z-score check
        vol_z = signal_data.get('vol_z', 0)
        
        # Default values (Prevents KeyError)
        verdict = WhaleVerdict.NEUTRAL
        boost = 0.0
        conviction = 5.0 # Neutral conviction

        # Logic
        if vol_z > 2.0:
            verdict = WhaleVerdict.CONFIRM
            boost = 0.15
            conviction = 8.0
        elif vol_z < 0.5:
            verdict = WhaleVerdict.DENY
            boost = -0.10
            conviction = 2.0
            
        return {
            'verdict': verdict.value, 
            'boost': boost,
            'conviction': conviction # <--- The missing key causing your crash
        }

def apply_whale_boost(base_prob, whale_result):
    return {'final_probability': max(0.0, min(0.98, base_prob + whale_result.get('boost', 0)))}