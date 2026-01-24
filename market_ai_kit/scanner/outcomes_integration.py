import json
import os
from datetime import datetime

STATS_FILE = "output/learned_rule_stats.json" 

def get_learned_confidence(rule_name: str, base_confidence: float) -> float:
    """Boosts or Penalizes confidence based on Real Data."""
    if not os.path.exists(STATS_FILE):
        return base_confidence

    try:
        with open(STATS_FILE, 'r') as f:
            stats = json.load(f)
        
        if rule_name in stats:
            rule_data = stats[rule_name]
            win_rate = rule_data.get('win_rate', 0.5)
            if win_rate > 0.60: return min(100, base_confidence + 15)
            elif win_rate < 0.40: return max(0, base_confidence - 20)
    except Exception:
        pass
    return base_confidence

def record_signal_for_tracking(signal_data: dict):
    """Saves signal to pending list for outcomes.py."""
    log_entry = {
        "ticker": signal_data['ticker'],
        "date": datetime.now().strftime("%Y-%m-%d"),
        "entry": signal_data['entry'],
        "patterns": list(signal_data.get('patterns', {}).keys())
    }
    with open("output/pending_signals.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")