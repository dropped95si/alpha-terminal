
from typing import Any, Dict
from .probability_v22 import ProbabilityEngineV22
from .whale_sieve import WhaleValidator, apply_whale_boost
from .adaptive_weighting import AdaptiveWeightingSystem, apply_credibility_multiplier


class EnhancedV22Engine:
    """Wraps ProbabilityEngineV22 with whale + credibility post-processing"""
    
    def __init__(self):
        self.v22 = ProbabilityEngineV22()
        self.whale_validator = WhaleValidator()
        self.credibility_system = AdaptiveWeightingSystem()
    
    def score_with_enhancements(
        self,
        card: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Score card through full pipeline:
        1. Get v22 probability (level-based odds)
        2. Apply whale validation
        3. Apply credibility check
        4. Return enhanced result
        """
        
        # Step 1: Get v22 odds for all modes
        v22_result = self.v22.score(card, config)
        
        # Use swing mode as base (most reliable for 5-20 bars)
        swing = v22_result.get("swing", {})
        base_prob = swing.get("probs", {}).get("p_up", 0.5)
        
        # Step 2: Whale validation (NEW)
        whale_result = self.whale_validator.validate_whale_flow(card)
        whale_boosted = apply_whale_boost(base_prob, whale_result)
        prob_after_whale = whale_boosted['final_probability']
        
        # Step 3: Credibility check (NEW)
        credibility_result = self.credibility_system.assess_credibility(card)
        final_result = apply_credibility_multiplier(
            prob_after_whale,
            credibility_result
        )
        
        # Build enhanced output
        enhanced_probs = swing.get("probs", {})
        enhanced_probs["p_up"] = final_result['final_probability']
        
        return {
            **v22_result,
            "swing": {
                **swing,
                "probs": enhanced_probs,
                "whale_verdict": whale_result.get("verdict"),
                "whale_conviction": whale_result.get("conviction", 0.0),
                "credibility_score": credibility_result.get("credibility", 0.0),
                "recommendation": credibility_result.get("recommendation"),
                "risk_assessment": credibility_result.get("risk_assessment"),
            },
            "probability": final_result['final_probability'],
            "whale_verdict": whale_result.get("verdict"),
            "credibility_score": credibility_result.get("credibility", 0.0),
        }
PYEOF
```