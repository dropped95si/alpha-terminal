from typing import Dict
from enum import Enum

class WhaleVerdict(Enum):
    CONFIRM = "CONFIRM"
    WATCH = "WATCH"
    DENY = "DENY"
    NEUTRAL = "NEUTRAL"

class WhaleValidator:
    def validate_whale_flow(self, signal_data: Dict) -> Dict:
        # Simple Logic: High Vol Z-Score + Price Action check
        vol_z = signal_data.get('vol_z', 0)
        
        if vol_z > 2.0:
            return {'verdict': 'CONFIRM', 'boost': 0.15}
        elif vol_z < 0.5:
            return {'verdict': 'DENY', 'boost': -0.10}
        
        return {'verdict': 'NEUTRAL', 'boost': 0.0}

def apply_whale_boost(base_prob, whale_result):
    return {'final_probability': max(0.0, min(0.98, base_prob + whale_result.get('boost', 0)))}