"""
🛡️ RISK ENGINE - QUARTER-KELLY SIZING
Enforces the 1:3 Reward/Risk 'Sober Rail'
"""

def calculate_position(account_equity, price, stop_loss, confidence):
    # 1. Enforce 1:3 Multiplier (The Sober Rail)
    risk_per_share = abs(price - stop_loss)
    target_3x = price + (risk_per_share * 3.0)

    # 2. Quarter-Kelly Calculation
    p = confidence / 100.0  # Probability (Win Rate)
    b = 3.0                 # Odds (Our R:R goal)
    
    # Kelly Formula: f* = (bp - q) / b
    kelly_f = (b * p - (1 - p)) / b
    
    # Apply the 1/4 Kelly multiplier to prevent 'Black Swan' ruin
    # Limit max risk to 2% of total equity per trade
    safe_f = max(min(kelly_f * 0.25, 0.02), 0.005) 
    
    total_risk_dollars = account_equity * safe_f
    shares = int(total_risk_dollars / risk_per_share) if risk_per_share > 0 else 0
    
    return {
        "shares": shares,
        "target_3x": round(target_3x, 2),
        "risk_percent": round(safe_f * 100, 2),
    }