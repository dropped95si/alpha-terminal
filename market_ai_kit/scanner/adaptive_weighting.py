"""
Adaptive Weighting System
Credibility scoring for fake vs real breakouts
8-point credibility analysis
"""

from typing import Dict, List
from dataclasses import dataclass


@dataclass
class CredibilityFactors:
    """8-point credibility framework"""
    volume_reversal: float = 0.0      # Volume pattern
    price_structure: float = 0.0      # Technical structure
    multi_timeframe: float = 0.0      # Confluence across TF
    trend_strength: float = 0.0       # Direction conviction
    volatility_regime: float = 0.0    # Normal vs abnormal vol
    support_resistance: float = 0.0   # Level strength
    chart_pattern: float = 0.0        # Recognizable setup
    whale_validation: float = 0.0     # Institutional backing


class AdaptiveWeightingSystem:
    """
    Detects fake vs real breakouts
    Applies credibility multiplier to probability
    """
    
    def __init__(self):
        # Fake breakout characteristics
        self.fake_signals = {
            'high_volume_spike_low_range': 0.1,    # Big volume, small move
            'hollow_candles': 0.15,                # High wicks, no closes
            'rejection_at_resistance': 0.2,        # Bounce off level
            'gap_fill_only': 0.15,                 # Just fills gap, fails
            'single_timeframe': 0.25,              # Only D breakout, not 4H
            'no_whale_backing': 0.3,               # Volume from retail
        }
        
        # Real breakout characteristics
        self.real_signals = {
            'volume_acceleration': 0.95,           # Vol increases into breakout
            'clean_closes': 0.9,                   # Real closes above level
            'multi_timeframe_confluence': 0.95,    # D + 4H + 15M agree
            'continuation_follow_through': 0.92,  # Follow-through candle
            'whale_aligned': 0.98,                 # Institutional buying
            'above_daily_average': 0.93,           # Above avg daily range
        }
    
    def assess_credibility(self, signal_data: Dict) -> Dict:
        """
        Assess credibility of a signal using 8-point framework
        
        Input:
        {
            'ticker': 'NVDA',
            'entry': 135.50,
            'base_probability': 0.76,
            
            # Volume checks
            'volume_trend': 'increasing',  # last 5 days
            'volume_zscore': 2.5,
            'avg_volume': 50000000,
            'today_volume': 75000000,
            
            # Price structure
            'previous_high': 133.80,
            'resistance_level': 135.00,
            'broken_resistance': True,
            'closed_above_resistance': True,
            
            # Multi-timeframe
            'daily_signal': True,
            'h4_signal': True,
            'h1_signal': False,
            
            # Trend
            'trend_direction': 'up',
            'trend_strength': 'strong',  # ATR multiple from avg
            'atr_20': 2.50,
            'move_size': 3.20,  # Entry - previous low
            
            # Volatility
            'iv_rank': 0.65,           # Current vs 52-week
            'iv_trend': 'stable',
            
            # Support/Resistance
            'nearest_support': 130.00,
            'support_strength': 'strong',  # Touches from above
            
            # Chart pattern
            'chart_pattern': 'ascending_triangle',
            'pattern_complete': True,
            
            # Whale validation (from whale_sieve)
            'whale_conviction': 7.5,
            'whale_blocks_aligned': 2,
        }
        
        Returns:
        {
            'credibility': 0.92,
            'credibility_factors': {
                'volume_reversal': 0.95,
                'price_structure': 0.90,
                ...
            },
            'fake_breakout_probability': 0.08,
            'real_breakout_probability': 0.92,
            'multiplier': 0.92,  # Apply to final probability
            'risk_assessment': 'LOW',
            'recommendation': 'STRONG_BUY',
        }
        """
        
        factors = CredibilityFactors()
        
        # ===== FACTOR 1: VOLUME REVERSAL =====
        factors.volume_reversal = self._assess_volume(signal_data)
        
        # ===== FACTOR 2: PRICE STRUCTURE =====
        factors.price_structure = self._assess_price_structure(signal_data)
        
        # ===== FACTOR 3: MULTI-TIMEFRAME =====
        factors.multi_timeframe = self._assess_confluence(signal_data)
        
        # ===== FACTOR 4: TREND STRENGTH =====
        factors.trend_strength = self._assess_trend(signal_data)
        
        # ===== FACTOR 5: VOLATILITY REGIME =====
        factors.volatility_regime = self._assess_volatility(signal_data)
        
        # ===== FACTOR 6: SUPPORT/RESISTANCE =====
        factors.support_resistance = self._assess_levels(signal_data)
        
        # ===== FACTOR 7: CHART PATTERN =====
        factors.chart_pattern = self._assess_pattern(signal_data)
        
        # ===== FACTOR 8: WHALE VALIDATION =====
        factors.whale_validation = self._assess_whale(signal_data)
        
        # Calculate average credibility
        all_factors = [
            factors.volume_reversal,
            factors.price_structure,
            factors.multi_timeframe,
            factors.trend_strength,
            factors.volatility_regime,
            factors.support_resistance,
            factors.chart_pattern,
            factors.whale_validation,
        ]
        
        credibility = sum(all_factors) / len(all_factors)
        credibility = max(0.0, min(1.0, credibility))
        
        # Fake breakout probability
        fake_prob = 1.0 - credibility
        
        # Determine risk level
        risk = self._get_risk_level(credibility)
        
        # Recommendation
        rec = self._get_recommendation(credibility, signal_data.get('base_probability', 0.5))
        
        return {
            'credibility': round(credibility, 2),
            'credibility_factors': {
                'volume_reversal': round(factors.volume_reversal, 2),
                'price_structure': round(factors.price_structure, 2),
                'multi_timeframe': round(factors.multi_timeframe, 2),
                'trend_strength': round(factors.trend_strength, 2),
                'volatility_regime': round(factors.volatility_regime, 2),
                'support_resistance': round(factors.support_resistance, 2),
                'chart_pattern': round(factors.chart_pattern, 2),
                'whale_validation': round(factors.whale_validation, 2),
            },
            'fake_breakout_probability': round(fake_prob, 2),
            'real_breakout_probability': round(credibility, 2),
            'multiplier': round(credibility, 2),  # Apply to probability
            'risk_assessment': risk,
            'recommendation': rec,
        }
    
    def _assess_volume(self, data: Dict) -> float:
        """
        Volume Reversal: Volume increases into breakout?
        
        Good: Vol spike on breakout day, trend higher
        Bad: Vol spike before, then drops on breakout
        """
        trend = data.get('volume_trend', '').lower()
        zscore = data.get('volume_zscore', 0.0)
        
        # Must have volume spike
        if zscore < 2.0:
            return 0.40
        
        # Better if volume increasing
        if trend == 'increasing':
            return 0.95
        elif trend == 'stable':
            return 0.75
        else:
            return 0.45
    
    def _assess_price_structure(self, data: Dict) -> float:
        """
        Price Structure: Clean break of resistance?
        
        Good: Closes above resistance level
        Bad: Wicks above then closes below
        """
        
        broken = data.get('broken_resistance', False)
        closed_above = data.get('closed_above_resistance', False)
        
        if not broken:
            return 0.30
        
        if closed_above:
            return 0.92  # Clean break
        else:
            return 0.55  # Wick rejection
    
    def _assess_confluence(self, data: Dict) -> float:
        """
        Multi-Timeframe Confluence
        
        Good: Daily + 4H + 15M all bullish
        Bad: Only daily signal
        """
        
        daily = data.get('daily_signal', False)
        h4 = data.get('h4_signal', False)
        h1 = data.get('h1_signal', False)
        
        count = sum([daily, h4, h1])
        
        if count >= 2:
            return 0.95  # Multi-timeframe
        elif count == 1:
            return 0.60  # Single timeframe
        else:
            return 0.30
    
    def _assess_trend(self, data: Dict) -> float:
        """
        Trend Strength
        
        Good: Move size > 1 ATR average
        Bad: Small move, could reverse
        """
        
        direction = data.get('trend_direction', '').lower()
        strength = data.get('trend_strength', '').lower()
        
        if direction != 'up':
            return 0.30
        
        # Check move size
        move = data.get('move_size', 0.0)
        atr = data.get('atr_20', 1.0)
        
        if move >= atr * 1.5:
            return 0.92  # Strong move
        elif move >= atr:
            return 0.75  # Normal move
        else:
            return 0.50  # Weak move
    
    def _assess_volatility(self, data: Dict) -> float:
        """
        Volatility Regime
        
        Good: Normal volatility (not extremely high)
        Bad: Extreme vol = squeeze risk
        """
        
        iv_rank = data.get('iv_rank', 0.5)
        trend = data.get('iv_trend', 'stable').lower()
        
        # IV rank 0.3-0.7 is normal
        if iv_rank < 0.3:
            return 0.70  # Too low vol
        elif iv_rank > 0.8:
            return 0.50  # Too high vol
        else:
            return 0.85  # Normal
        
        # Stable is better than increasing
        if trend == 'stable':
            return 0.90
        elif trend == 'increasing':
            return 0.70
        else:
            return 0.60
    
    def _assess_levels(self, data: Dict) -> float:
        """
        Support/Resistance Strength
        
        Good: Strong support below entry
        Bad: No support
        """
        
        entry = data.get('entry', 100)
        support = data.get('nearest_support', 0)
        strength = data.get('support_strength', '').lower()
        
        # Distance from support
        distance = abs(entry - support) / entry
        
        if distance > 0.10:  # >10% away
            return 0.50  # Risky stop location
        elif distance > 0.05:
            return 0.75  # Adequate space
        else:
            return 0.85  # Close support
        
        # Strength of support
        if strength == 'strong':
            return 0.90
        else:
            return 0.70
    
    def _assess_pattern(self, data: Dict) -> float:
        """
        Chart Pattern Recognition
        
        Good: Recognizable breakout pattern
        Bad: No clear pattern
        """
        
        pattern = data.get('chart_pattern', 'none').lower()
        complete = data.get('pattern_complete', False)
        
        if not complete:
            return 0.50  # Incomplete pattern = risky
        
        # Some patterns more reliable
        good_patterns = [
            'ascending_triangle',
            'cup_and_handle',
            'flag',
            'pennant',
            'inverse_head_and_shoulders',
        ]
        
        if pattern in good_patterns:
            return 0.92
        elif pattern != 'none':
            return 0.75
        else:
            return 0.55
    
    def _assess_whale(self, data: Dict) -> float:
        """
        Whale Validation
        
        Good: High conviction whale blocks
        Bad: No institutional backing
        """
        
        conviction = data.get('whale_conviction', 0.0)
        blocks = data.get('whale_blocks_aligned', 0)
        
        if conviction >= 7 and blocks >= 2:
            return 0.98  # Real whale buying
        elif conviction >= 5 and blocks >= 1:
            return 0.80  # Institutional present
        elif conviction >= 3:
            return 0.65  # Some activity
        else:
            return 0.45  # No whale validation
    
    def _get_risk_level(self, credibility: float) -> str:
        """Map credibility to risk level"""
        if credibility >= 0.90:
            return 'VERY_LOW'
        elif credibility >= 0.80:
            return 'LOW'
        elif credibility >= 0.70:
            return 'MEDIUM'
        elif credibility >= 0.60:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
    
    def _get_recommendation(self, credibility: float, probability: float) -> str:
        """Get trading recommendation"""
        combined = credibility * probability
        
        if combined >= 0.85:
            return 'STRONG_BUY'
        elif combined >= 0.75:
            return 'BUY'
        elif combined >= 0.65:
            return 'MODERATE_BUY'
        elif combined >= 0.55:
            return 'WEAK_BUY'
        else:
            return 'AVOID'


def apply_credibility_multiplier(
    base_probability: float,
    credibility_result: Dict
) -> Dict:
    """
    Apply credibility multiplier to final probability
    """
    
    multiplier = credibility_result.get('multiplier', 0.5)
    final_prob = base_probability * multiplier
    final_prob = max(0.0, min(0.98, final_prob))
    
    return {
        'base_probability': round(base_probability, 3),
        'credibility': round(credibility_result.get('credibility', 0.5), 3),
        'final_probability': round(final_prob, 3),
        'risk_assessment': credibility_result.get('risk_assessment'),
        'recommendation': credibility_result.get('recommendation'),
    }


# Example
if __name__ == '__main__':
    system = AdaptiveWeightingSystem()
    
    signal = {
        'ticker': 'NVDA',
        'entry': 135.50,
        'base_probability': 0.76,
        'volume_trend': 'increasing',
        'volume_zscore': 2.5,
        'previous_high': 133.80,
        'resistance_level': 135.00,
        'broken_resistance': True,
        'closed_above_resistance': True,
        'daily_signal': True,
        'h4_signal': True,
        'h1_signal': False,
        'trend_direction': 'up',
        'atr_20': 2.50,
        'move_size': 3.20,
        'iv_rank': 0.65,
        'iv_trend': 'stable',
        'nearest_support': 130.00,
        'chart_pattern': 'ascending_triangle',
        'pattern_complete': True,
        'whale_conviction': 7.5,
        'whale_blocks_aligned': 2,
    }
    
    result = system.assess_credibility(signal)
    print(f"Credibility: {result['credibility']:.0%}")
    print(f"Fake Breakout Risk: {result['fake_breakout_probability']:.0%}")
    print(f"Risk Level: {result['risk_assessment']}")
    print(f"Recommendation: {result['recommendation']}")
    
    # Apply multiplier
    final = apply_credibility_multiplier(0.76, result)
    print(f"\nBase Prob: {final['base_probability']:.1%}")
    print(f"Multiplier: {final['credibility']:.1%}")
    print(f"Final Prob: {final['final_probability']:.1%}")
