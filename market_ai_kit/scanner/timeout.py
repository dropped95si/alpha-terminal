def get_timeout_rules(signal_type: str) -> dict:
    """Returns exit logic based on time."""
    if signal_type in ["PULLBACK", "MEAN_REVERSION"]:
        return {"days": 45, "action": "CLOSE", "reason": "Momentum stalled"}
    elif signal_type in ["BREAKOUT", "MOMENTUM"]:
        return {"days": 15, "action": "CLOSE", "reason": "Failed to launch"}
    return {"days": 60, "action": "CLOSE", "reason": "Standard Strategy Timeout"}