"""
Whale Flow Validator - Bible Rules
Detects institutional dark pool activity and whale block accumulation
"""

from typing import Dict, List, Optional
from enum import Enum


class WhaleVerdict(Enum):
    CONFIRM = "CONFIRM"      # +20% probability boost
    WATCH = "WATCH"          # +5% probability boost
    NEUTRAL = "NEUTRAL"      # 0% change
    DENY = "DENY"            # -15% probability cut


class WhaleValidator:
    """
    Bible Rules for whale flow validation
    
    Rule 1: Volume Spike Check
      - Z-score > 2.0 = statistically significant volume
    
    Rule 2: Whale Alignment
      - Blocks within ±2% of signal entry price
    
    Rule 3: Conviction Intensity
      - Score 0-10 based on block size and frequency
    
    Final Verdict:
    - CONFIRM: High conviction + aligned blocks = whales buying
    - WATCH: Present activity + neutral positioning
    - DENY: Blocks on sell side = institutional selling
    """
    
    def __init__(self):
        self.block_size_thresholds = {
            'mega_whale': 500000,      # >$500k per block
            'large_whale': 100000,     # >$100k per block
            'medium_whale': 50000,     # >$50k per block
            'small_whale': 10000,      # >$10k per block
        }
        
        self.conviction_weights = {
            'mega_whale': 3.0,
            'large_whale': 2.0,
            'medium_whale': 1.0,
            'small_whale': 0.3,
        }
    
    def validate_whale_flow(self, signal_data: Dict) -> Dict:
        """
        Validate whale flow for a signal
        
        Input:
        {
            'ticker': 'NVDA',
            'entry': 135.50,
            'target': 142.00,
            'volume_zscore': 2.5,              # Volume z-score
            'whale_buy_blocks': [
                {'price': 135.20, 'size': 200000},
                {'price': 135.80, 'size': 150000},
            ],
            'whale_sell_blocks': [
                {'price': 142.00, 'size': 100000},
            ],
            'volume_trend': 'increasing',      # Last 5 days
        }
        
        Returns:
        {
            'verdict': 'CONFIRM',
            'conviction': 8.2,  # 0-10 scale
            'credibility': 0.95,
            'buy_blocks': 2,
            'sell_blocks': 1,
            'alignment': 'PERFECT',
            'boost': 0.20  # +20% probability
        }
        """
        
        # ===== RULE 1: VOLUME SPIKE CHECK =====
        volume_valid = self._check_volume_spike(signal_data)
        
        if not volume_valid:
            return {
                'verdict': 'DENY',
                'conviction': 0.0,
                'credibility': 0.0,
                'boost': -0.15,
                'reason': 'No significant volume spike (Z < 2.0)',
            }
        
        # ===== RULE 2: WHALE ALIGNMENT =====
        buy_blocks = signal_data.get('whale_buy_blocks', [])
        sell_blocks = signal_data.get('whale_sell_blocks', [])
        entry = signal_data.get('entry', 100)
        
        aligned_buys = self._check_alignment(buy_blocks, entry)
        aligned_sells = self._check_alignment(sell_blocks, entry)
        
        alignment_score = self._score_alignment(
            aligned_buys, 
            aligned_sells, 
            entry
        )
        
        # ===== RULE 3: CONVICTION INTENSITY =====
        conviction = self._calc_conviction(aligned_buys, aligned_sells)
        
        # ===== DETERMINE VERDICT =====
        verdict, boost = self._determine_verdict(
            alignment_score,
            conviction,
            aligned_buys,
            aligned_sells
        )
        
        # ===== CREDIBILITY SCORE =====
        credibility = self._calc_credibility(
            conviction,
            len(aligned_buys),
            len(aligned_sells)
        )
        
        return {
            'verdict': verdict.value,
            'conviction': round(conviction, 1),
            'credibility': round(credibility, 2),
            'alignment_score': round(alignment_score, 2),
            'buy_blocks': len(aligned_buys),
            'sell_blocks': len(aligned_sells),
            'alignment': self._get_alignment_label(alignment_score),
            'boost': round(boost, 2),
            'analysis': {
                'volume_spike': volume_valid,
                'largest_buy_block': self._get_largest_block(aligned_buys),
                'total_buy_volume': sum(b['size'] for b in aligned_buys),
                'total_sell_volume': sum(b['size'] for b in aligned_sells),
            }
        }
    
    def _check_volume_spike(self, data: Dict) -> bool:
        """
        Rule 1: Volume Spike Check
        Z-score > 2.0 = statistically significant
        """
        zscore = data.get('volume_zscore', 0.0)
        
        # Z > 2.0 is 95th percentile
        return zscore > 2.0
    
    def _check_alignment(self, blocks: List[Dict], entry: float) -> List[Dict]:
        """
        Rule 2: Whale Alignment
        Blocks within ±2% of entry price
        """
        tolerance = entry * 0.02  # ±2%
        
        aligned = [
            block for block in blocks
            if abs(block.get('price', 0) - entry) <= tolerance
        ]
        
        return sorted(aligned, key=lambda x: x.get('size', 0), reverse=True)
    
    def _score_alignment(
        self,
        buy_blocks: List[Dict],
        sell_blocks: List[Dict],
        entry: float
    ) -> float:
        """
        Score alignment: ratio of aligned buys to sells
        
        Score 1.0 = All buys, no sells (PERFECT)
        Score 0.5 = Equal buys and sells (NEUTRAL)
        Score 0.0 = All sells, no buys (TERRIBLE)
        """
        buy_vol = sum(b['size'] for b in buy_blocks)
        sell_vol = sum(b['size'] for b in sell_blocks)
        total_vol = buy_vol + sell_vol
        
        if total_vol == 0:
            return 0.5  # Neutral if no blocks
        
        # Ratio of buy volume
        buy_ratio = buy_vol / total_vol
        
        # Perfect = all buys (1.0), terrible = all sells (0.0)
        return buy_ratio
    
    def _calc_conviction(
        self,
        buy_blocks: List[Dict],
        sell_blocks: List[Dict]
    ) -> float:
        """
        Rule 3: Conviction Intensity
        0-10 scale based on block size and count
        
        Mega whale (>$500k):  3.0 per block
        Large whale (>$100k): 2.0 per block
        Medium (>$50k):       1.0 per block
        Small (>$10k):        0.3 per block
        """
        conviction = 0.0
        
        # Score buys (positive)
        for block in buy_blocks:
            size = block.get('size', 0)
            weight = self._get_block_weight(size)
            conviction += weight
        
        # Penalize sells (negative)
        for block in sell_blocks:
            size = block.get('size', 0)
            weight = self._get_block_weight(size)
            conviction -= weight * 0.5  # Less penalty for sells
        
        # Cap at 0-10
        conviction = max(0.0, min(10.0, conviction))
        
        return conviction
    
    def _get_block_weight(self, size: float) -> float:
        """Get conviction weight for block size"""
        if size >= self.block_size_thresholds['mega_whale']:
            return self.conviction_weights['mega_whale']
        elif size >= self.block_size_thresholds['large_whale']:
            return self.conviction_weights['large_whale']
        elif size >= self.block_size_thresholds['medium_whale']:
            return self.conviction_weights['medium_whale']
        else:
            return self.conviction_weights['small_whale']
    
    def _determine_verdict(
        self,
        alignment_score: float,
        conviction: float,
        buy_blocks: List[Dict],
        sell_blocks: List[Dict]
    ) -> tuple:
        """
        Determine final verdict and boost
        
        CONFIRM: Whales buying strongly
          - Alignment 0.70+ AND Conviction 6+
          - Boost: +20% probability
        
        WATCH: Whales present
          - Alignment 0.50+ AND Conviction 3+
          - Boost: +5% probability
        
        NEUTRAL: Indifferent
          - Otherwise
          - Boost: 0%
        
        DENY: Whales selling
          - Sell blocks > buy blocks
          - Boost: -15% probability
        """
        
        # Check if whales are selling
        if len(sell_blocks) > len(buy_blocks):
            return (WhaleVerdict.DENY, -0.15)
        
        # Check conviction
        if alignment_score >= 0.70 and conviction >= 6.0:
            return (WhaleVerdict.CONFIRM, 0.20)
        
        if alignment_score >= 0.50 and conviction >= 3.0:
            return (WhaleVerdict.WATCH, 0.05)
        
        return (WhaleVerdict.NEUTRAL, 0.0)
    
    def _calc_credibility(self, conviction: float, buy_count: int, sell_count: int) -> float:
        """
        Credibility: how reliable is the whale signal?
        
        True whale blocks (>$100k): 95% credibility
        False breakouts (retail): 40% credibility
        """
        
        if conviction >= 6.0 and buy_count >= 2:
            return 0.95  # Real whale activity
        elif conviction >= 3.0 and buy_count >= 1:
            return 0.75  # Institutional presence
        elif buy_count > 0:
            return 0.60  # Some activity
        else:
            return 0.40  # Unclear/retail
    
    def _get_alignment_label(self, score: float) -> str:
        """Get human-readable alignment label"""
        if score >= 0.85:
            return 'PERFECT'
        elif score >= 0.70:
            return 'STRONG'
        elif score >= 0.50:
            return 'BALANCED'
        elif score >= 0.30:
            return 'MIXED'
        else:
            return 'WEAK'
    
    def _get_largest_block(self, blocks: List[Dict]) -> Optional[int]:
        """Get largest block size"""
        if not blocks:
            return None
        return max(b.get('size', 0) for b in blocks)


def apply_whale_boost(base_probability: float, whale_verdict_result: Dict) -> Dict:
    """
    Apply whale verdict boost/cut to base probability
    
    Input:
      base_probability: 0.76 (from 16-factor engine)
      whale_verdict_result: {verdict: 'CONFIRM', boost: 0.20, ...}
    
    Returns:
      {
        'final_probability': 0.89,
        'whale_boost_applied': 0.20,
        'confidence': 'HIGH'
      }
    """
    boost = whale_verdict_result.get('boost', 0.0)
    conviction = whale_verdict_result.get('conviction', 0.0)
    
    # Apply boost to base probability
    # But cap the final result at 0.98
    final_prob = base_probability + boost
    final_prob = max(0.0, min(0.98, final_prob))
    
    # Confidence increases with conviction
    if conviction >= 7:
        confidence = 'HIGH'
    elif conviction >= 4:
        confidence = 'MEDIUM'
    else:
        confidence = 'LOW'
    
    return {
        'base_probability': round(base_probability, 3),
        'final_probability': round(final_prob, 3),
        'whale_boost_applied': round(boost, 3),
        'whale_conviction': round(conviction, 1),
        'whale_verdict': whale_verdict_result.get('verdict'),
        'confidence': confidence,
    }


# Example usage
if __name__ == '__main__':
    validator = WhaleValidator()
    
    signal = {
        'ticker': 'NVDA',
        'entry': 135.50,
        'target': 142.00,
        'volume_zscore': 2.5,  # Significant volume spike
        'whale_buy_blocks': [
            {'price': 135.20, 'size': 200000},   # $200k block
            {'price': 135.80, 'size': 150000},   # $150k block
        ],
        'whale_sell_blocks': [
            {'price': 142.00, 'size': 100000},   # $100k block at target
        ],
    }
    
    result = validator.validate_whale_flow(signal)
    print(f"Whale Verdict: {result['verdict']}")
    print(f"Conviction: {result['conviction']}/10")
    print(f"Alignment: {result['alignment']}")
    print(f"Credibility: {result['credibility']:.0%}")
    
    # Apply to base probability
    final = apply_whale_boost(0.76, result)
    print(f"\nBase Probability: {final['base_probability']:.1%}")
    print(f"Whale Boost: +{final['whale_boost_applied']:.1%}")
    print(f"Final Probability: {final['final_probability']:.1%}")
