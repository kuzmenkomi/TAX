"""
TLH Priority Scorer - Transparent Scoring Breakdown
Calculates priority score with full visibility into components
"""

from typing import Dict, Any, Tuple
from decimal import Decimal
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScoringComponents:
    """Transparent breakdown of priority score"""
    tax_savings_score: float = 0.0      # Based on dollar amount
    liquidity_score: float = 0.0        # 0-100 from liquidity checker
    volatility_component: float = 0.0   # Risk adjustment
    wash_sale_penalty: float = 0.0      # Negative if near wash-sale
    fee_impact: float = 0.0             # Positive if fees are low
    urgency_factor: float = 0.0         # Time-based (prices dropping fast?)
    
    # Weights (can be customized per country/strategy)
    tax_weight: float = 0.40
    liquidity_weight: float = 0.35
    volatility_weight: float = 0.15
    wash_sale_weight: float = 0.05      # Penalty weight
    fee_weight: float = 0.05
    
    def calculate_total(self) -> float:
        """Calculate weighted total score (0-100)"""
        total = (
            self.tax_savings_score * self.tax_weight +
            self.liquidity_score * self.liquidity_weight +
            (self.volatility_component * 100) * self.volatility_weight +
            self.wash_sale_penalty * self.wash_sale_weight +
            self.fee_impact * self.fee_weight +
            self.urgency_factor * 0.10
        )
        return min(max(total, 0), 100)  # Clamp 0-100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to transparent dict"""
        total = self.calculate_total()
        return {
            "tax_savings_component": round(self.tax_savings_score * self.tax_weight, 2),
            "liquidity_component": round(self.liquidity_score * self.liquidity_weight, 2),
            "volatility_component": round(self.volatility_component * self.volatility_weight, 2),
            "wash_sale_penalty": round(self.wash_sale_penalty * self.wash_sale_weight, 2),
            "fee_impact": round(self.fee_impact * self.fee_weight, 2),
            "urgency_factor": round(self.urgency_factor * 0.10, 2),
            "total_score": round(total, 1),
            "breakdown": {
                "tax_savings_raw": round(self.tax_savings_score, 1),
                "liquidity_raw": round(self.liquidity_score, 1),
                "volatility_raw": round(self.volatility_component, 2),
                "wash_sale_penalty_raw": round(self.wash_sale_penalty, 1),
                "fee_impact_raw": round(self.fee_impact, 1),
            }
        }


class TLHScorer:
    """
    Transparent priority scoring for tax-loss opportunities
    """
    
    # Tax benefit scoring (0-100)
    TAX_BENEFIT_SCALING_FACTOR = 500  # $500 loss = 10 points
    MIN_TAX_BENEFIT_FOR_POINTS = Decimal("100")
    
    # Liquidity penalties
    LIQUIDITY_THRESHOLD_HIGH = 80
    LIQUIDITY_THRESHOLD_MEDIUM = 50
    LIQUIDITY_THRESHOLD_LOW = 30
    
    # Wash-sale penalties
    WASH_SALE_CLOSE_THRESHOLD = 10  # days
    WASH_SALE_PENALTY_MAX = -20  # max -20 points
    
    # Fee impact
    FEE_THRESHOLD_ACCEPTABLE = 0.15  # 15% of benefit
    
    # Volatility impact (riskier = higher priority to execute now)
    VOLATILITY_THRESHOLD_HIGH = 25  # %
    VOLATILITY_THRESHOLD_MEDIUM = 10  # %
    
    # Urgency (price dropping fast = more urgent)
    PRICE_MOMENTUM_THRESHOLD = 5  # % drop in 7 days
    
    @classmethod
    def score_opportunity(
        cls,
        loss_amount: Decimal,
        tax_rate: float,
        liquidity_score: float,
        volatility: float,
        estimated_fees: Decimal,
        wash_sale_days_remaining: int = 0,
        price_momentum: float = 0.0,  # % drop in last 7 days
        strategy_weights: Dict[str, float] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Score opportunity with full transparency
        
        Returns:
            (total_score, breakdown_dict)
        """
        components = ScoringComponents()
        
        # Optional custom weights
        if strategy_weights:
            for key, value in strategy_weights.items():
                if hasattr(components, key):
                    setattr(components, key, value)
        
        # 1️⃣ TAX SAVINGS COMPONENT (0-100)
        # Higher loss = higher score
        tax_benefit = loss_amount * Decimal(str(tax_rate / 100))
        
        if tax_benefit > cls.MIN_TAX_BENEFIT_FOR_POINTS:
            # Scale logarithmically to avoid extreme outliers
            tax_score = min(
                (float(tax_benefit) / cls.TAX_BENEFIT_SCALING_FACTOR) * 100,
                100
            )
        else:
            tax_score = 0
        
        components.tax_savings_score = tax_score
        logger.debug(f"[TLH Scorer] Tax benefit ${tax_benefit:.2f} → score {tax_score:.1f}")
        
        # 2️⃣ LIQUIDITY COMPONENT (0-100)
        # Higher liquidity = higher score (can actually execute)
        components.liquidity_score = liquidity_score
        logger.debug(f"[TLH Scorer] Liquidity {liquidity_score} → component {liquidity_score * components.liquidity_weight:.1f}")
        
        # 3️⃣ VOLATILITY COMPONENT (0-1, later scaled)
        # Higher volatility = execute now (price could recover)
        if volatility > cls.VOLATILITY_THRESHOLD_HIGH:
            vol_component = 1.0  # Max urgency
        elif volatility > cls.VOLATILITY_THRESHOLD_MEDIUM:
            vol_component = 0.7
        else:
            vol_component = 0.3
        
        components.volatility_component = vol_component
        logger.debug(f"[TLH Scorer] Volatility {volatility:.1f}% → component {vol_component}")
        
        # 4️⃣ WASH-SALE PENALTY
        # Penalize if close to wash-sale period
        if wash_sale_days_remaining > 0:
            if wash_sale_days_remaining <= cls.WASH_SALE_CLOSE_THRESHOLD:
                # Linear penalty: 0 days left = -20, 10 days left = -2
                penalty = (cls.WASH_SALE_PENALTY_MAX / cls.WASH_SALE_CLOSE_THRESHOLD) * wash_sale_days_remaining
                components.wash_sale_penalty = penalty
                logger.debug(f"[TLH Scorer] Wash-sale penalty: {wash_sale_days_remaining} days → {penalty:.1f} points")
        
        # 5️⃣ FEE IMPACT
        # Reward if fees are low relative to benefit
        if tax_benefit > 0:
            fee_ratio = float(estimated_fees) / float(tax_benefit)
            
            if fee_ratio < cls.FEE_THRESHOLD_ACCEPTABLE:
                # Good fee ratio - add bonus points (capped at +10)
                fee_bonus = min((1 - fee_ratio) * 20, 10)
                components.fee_impact = fee_bonus
            else:
                # High fees - penalty
                fee_penalty = min((fee_ratio - cls.FEE_THRESHOLD_ACCEPTABLE) * 20, -10)
                components.fee_impact = fee_penalty
            
            logger.debug(f"[TLH Scorer] Fee ratio {fee_ratio:.2f} → impact {components.fee_impact:.1f}")
        
        # 6️⃣ URGENCY FACTOR
        # Price dropping fast = more urgent
        if price_momentum < -cls.PRICE_MOMENTUM_THRESHOLD:
            # Losing value fast - execute now!
            urgency = min(abs(price_momentum) * 2, 30)  # Max 30 points
            components.urgency_factor = urgency
            logger.debug(f"[TLH Scorer] Price momentum {price_momentum:.1f}% → urgency {urgency:.1f}")
        
        # Calculate total
        total_score = components.calculate_total()
        breakdown = components.to_dict()
        
        logger.info(f"[TLH Scorer] Final score: {total_score:.1f}/100")
        
        return total_score, breakdown
    
    @classmethod
    def get_score_explanation(cls, breakdown: Dict[str, Any]) -> str:
        """Generate human-readable explanation of score"""
        score = breakdown.get('total_score', 0)
        
        if score >= 90:
            reason = "🔥 Excellent opportunity - execute immediately"
        elif score >= 75:
            reason = "✅ Good opportunity - consider executing"
        elif score >= 50:
            reason = "⚠️ Moderate opportunity - wait for confirmation"
        elif score >= 30:
            reason = "❌ Poor opportunity - fees may exceed benefits"
        else:
            reason = "❌ Skip - not worth executing"
        
        explanation = f"""
{reason}

Score Breakdown:
  Tax Savings:     +{breakdown.get('tax_savings_component', 0):.1f} points
  Liquidity:       +{breakdown.get('liquidity_component', 0):.1f} points
  Volatility:      +{breakdown.get('volatility_component', 0):.1f} points
  Wash-Sale:       {breakdown.get('wash_sale_penalty', 0):.1f} points
  Fee Impact:      {breakdown.get('fee_impact', 0):.1f} points
  Urgency:         +{breakdown.get('urgency_factor', 0):.1f} points
  ─────────────────────────────
  TOTAL:           {breakdown.get('total_score', 0):.1f}/100
"""
        return explanation.strip()


# Example usage
if __name__ == "__main__":
    from decimal import Decimal
    
    # Excellent opportunity
    score, breakdown = TLHScorer.score_opportunity(
        loss_amount=Decimal("5000"),
        tax_rate=24.0,
        liquidity_score=100,
        volatility=15,
        estimated_fees=Decimal("50"),
        wash_sale_days_remaining=0,
        price_momentum=-3.0
    )
    
    print(f"Score: {score:.1f}/100")
    print(f"Breakdown: {breakdown}")
    print(f"\nExplanation:\n{TLHScorer.get_score_explanation(breakdown)}")
    
    # Poor opportunity (high fees, illiquid)
    score2, breakdown2 = TLHScorer.score_opportunity(
        loss_amount=Decimal("200"),
        tax_rate=24.0,
        liquidity_score=25,  # Illiquid
        volatility=5,
        estimated_fees=Decimal("80"),  # 40% of benefit!
        wash_sale_days_remaining=5,
        price_momentum=0.0
    )
    
    print(f"\n\nPoor opportunity:")
    print(f"Score: {score2:.1f}/100")
    print(f"\nExplanation:\n{TLHScorer.get_score_explanation(breakdown2)}")
