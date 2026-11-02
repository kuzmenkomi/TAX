"""
TLH Engine - Core Orchestration Layer
Orchestrates scorer, executor, event listener, and storage
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RecommendationStatus(str, Enum):
    """Status of a TLH recommendation"""
    NEW = "new"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class TLHRecommendation:
    """Complete TLH recommendation with scoring and execution status"""
    asset: str
    loss_amount: Decimal
    tax_rate: float
    position_id: str  # Reference to original position
    
    # Scoring details
    priority_score: float
    priority_breakdown: Dict
    explanation: str
    
    # Execution tracking
    status: RecommendationStatus = RecommendationStatus.NEW
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    
    # Execution attempt
    execution_strategy: Optional[str] = None  # "immediate", "limit_price", "scheduled"
    execution_attempts: int = 0
    last_execution_error: Optional[str] = None
    last_execution_time: Optional[datetime] = None
    
    # Execution result
    order_id: Optional[str] = None
    quantity_executed: Optional[Decimal] = None
    average_price_executed: Optional[Decimal] = None
    fees_paid: Optional[Decimal] = None
    
    # Metadata
    notes: str = ""
    wash_sale_risk: bool = False
    wash_sale_days_remaining: int = 0
    
    def is_expired(self) -> bool:
        """Check if recommendation has expired"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'asset': self.asset,
            'loss_amount': float(self.loss_amount),
            'tax_rate': self.tax_rate,
            'position_id': self.position_id,
            'priority_score': self.priority_score,
            'priority_breakdown': self.priority_breakdown,
            'explanation': self.explanation,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'execution_strategy': self.execution_strategy,
            'execution_attempts': self.execution_attempts,
            'order_id': self.order_id,
            'quantity_executed': float(self.quantity_executed) if self.quantity_executed else None,
            'fees_paid': float(self.fees_paid) if self.fees_paid else None,
            'wash_sale_risk': self.wash_sale_risk,
            'wash_sale_days_remaining': self.wash_sale_days_remaining,
        }


@dataclass
class ExecutionPlan:
    """Plan for executing multiple TLH opportunities"""
    recommendations: List[TLHRecommendation]
    execution_order: List[str]  # position_ids in preferred execution order
    estimated_tax_savings: Decimal = Decimal("0")
    estimated_fees: Decimal = Decimal("0")
    estimated_capital_needed: Decimal = Decimal("0")
    
    def total_tax_savings(self) -> Decimal:
        """Calculate total tax savings"""
        return sum(r.loss_amount * Decimal(str(r.tax_rate / 100)) 
                  for r in self.recommendations)


class TLHEngine:
    """
    Core orchestration engine for Tax-Loss Harvesting
    
    Flow:
    1. Scan portfolio for harvestable losses (triggered by: scheduler, price event, manual)
    2. Score each opportunity (transparent 6-component scoring)
    3. Create recommendations (with explanation + execution strategy)
    4. Execute (dry-run first, then real)
    5. Track execution (audit trail + status updates)
    """
    
    def __init__(
        self,
        scorer=None,  # TLHScorer
        executor=None,  # TLHExecutor
        event_listener=None,  # TLHEventListener
        event_reactor=None,  # TLHEventReactor
        db_service=None,  # Database service
    ):
        self.scorer = scorer
        self.executor = executor
        self.event_listener = event_listener
        self.event_reactor = event_reactor
        self.db = db_service
        
        # In-memory state
        self.recommendations: Dict[str, TLHRecommendation] = {}
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        self.execution_history: List[Dict] = []
        
        # Settings
        self.auto_execute_min_score = 90  # Auto-execute if score >= 90
        self.allow_auto_execution = True
        
        logger.info("✅ TLH Engine initialized")
    
    def scan_portfolio(self, positions: List[Dict]) -> List[TLHRecommendation]:
        """
        Scan portfolio for tax-loss harvesting opportunities
        
        Args:
            positions: List of current positions with {
                'id': position_id,
                'asset': symbol,
                'quantity': qty,
                'average_cost': cost_basis,
                'current_price': current_price,
                'purchase_date': datetime,
                'exchanges': [list of exchange ids]
            }
        
        Returns:
            List of TLHRecommendation sorted by priority_score desc
        """
        logger.info(f"📊 Scanning {len(positions)} positions for TLH opportunities...")
        
        recommendations = []
        
        for position in positions:
            asset = position['asset']
            avg_cost = Decimal(str(position['average_cost']))
            current_price = Decimal(str(position['current_price']))
            quantity = Decimal(str(position['quantity']))
            
            # Check if in loss
            loss_per_unit = avg_cost - current_price
            if loss_per_unit <= 0:
                continue  # No loss
            
            loss_amount = loss_per_unit * quantity
            
            # Check wash-sale
            wash_sale_days = self._check_wash_sale(asset, position['purchase_date'])
            if wash_sale_days and wash_sale_days > 0:
                logger.warning(f"  ⚠️ {asset}: wash-sale risk for {wash_sale_days} more days")
                continue
            
            # Calculate liquidity (simplified - assume 100 for major assets)
            liquidity_score = self._calculate_liquidity(asset, quantity)
            
            # Calculate volatility (simplified - fetch from market data)
            volatility = self._get_volatility(asset)
            
            # Estimate fees
            estimated_fees = loss_amount * Decimal("0.001")  # 0.1% exchange fee
            
            # Calculate tax rate (simplified - use default)
            tax_rate = self._get_tax_rate(asset)
            
            # SCORE THE OPPORTUNITY
            score, breakdown = self.scorer.score_opportunity(
                loss_amount=loss_amount,
                tax_rate=tax_rate,
                liquidity_score=liquidity_score,
                volatility=volatility,
                estimated_fees=estimated_fees,
                wash_sale_days_remaining=wash_sale_days or 0,
                price_momentum=self._get_price_momentum(asset)
            )
            
            # Get explanation
            explanation = self.scorer.get_score_explanation(breakdown)
            
            # Create recommendation
            rec = TLHRecommendation(
                asset=asset,
                loss_amount=loss_amount,
                tax_rate=tax_rate,
                position_id=position['id'],
                priority_score=score,
                priority_breakdown=breakdown,
                explanation=explanation,
                expires_at=datetime.now() + timedelta(days=7),  # Recommendations expire after 7 days
                wash_sale_risk=False,
                wash_sale_days_remaining=wash_sale_days or 0,
            )
            
            recommendations.append(rec)
            self.recommendations[rec.position_id] = rec
            
            logger.info(f"  ✨ {asset}: Score {score:.1f} - {explanation[:50]}")
        
        # Sort by priority score
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        logger.info(f"✅ Found {len(recommendations)} harvestable opportunities")
        return recommendations
    
    def create_execution_plan(
        self,
        recommendation_ids: List[str],
        strategy: str = "immediate"
    ) -> ExecutionPlan:
        """
        Create plan to execute recommendations
        
        Args:
            recommendation_ids: List of position_ids to execute
            strategy: "immediate", "limit_price", "scheduled"
        
        Returns:
            ExecutionPlan with execution order and estimates
        """
        logger.info(f"📋 Creating execution plan for {len(recommendation_ids)} recommendations...")
        
        recs = [self.recommendations[id] for id in recommendation_ids if id in self.recommendations]
        
        # Sort by score (highest first)
        recs.sort(key=lambda r: r.priority_score, reverse=True)
        
        plan = ExecutionPlan(
            recommendations=recs,
            execution_order=[r.position_id for r in recs],
        )
        
        # Calculate estimates
        plan.estimated_tax_savings = sum(
            r.loss_amount * Decimal(str(r.tax_rate / 100))
            for r in recs
        )
        plan.estimated_fees = sum(
            r.loss_amount * Decimal("0.001")
            for r in recs
        )
        plan.estimated_capital_needed = sum(r.loss_amount for r in recs)
        
        self.execution_plans[datetime.now().isoformat()] = plan
        
        logger.info(f"✅ Plan created: {len(recs)} recs, $${plan.estimated_tax_savings:.2f} tax savings")
        return plan
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        dry_run: bool = True,
        strategy: str = "immediate"
    ) -> Dict:
        """
        Execute an execution plan
        
        Args:
            plan: ExecutionPlan from create_execution_plan()
            dry_run: If True, simulate without real orders
            strategy: Execution strategy
        
        Returns:
            Execution summary with results
        """
        logger.info(f"🚀 Executing plan: {len(plan.recommendations)} recommendations, dry_run={dry_run}...")
        
        results = {
            'successful': [],
            'failed': [],
            'total_tax_savings': Decimal("0"),
            'total_fees': Decimal("0"),
        }
        
        for rec in plan.recommendations:
            try:
                # Dry run first
                if dry_run:
                    dry_result = self.executor.dry_run(
                        asset=rec.asset,
                        quantity=rec.loss_amount / Decimal("100"),  # Rough estimate
                        current_price=Decimal("100")
                    )
                    
                    if not dry_result.successful:
                        logger.warning(f"  ⚠️ {rec.asset}: Dry run failed - {dry_result.error}")
                        rec.status = RecommendationStatus.FAILED
                        rec.last_execution_error = dry_result.error
                        results['failed'].append(rec.to_dict())
                        continue
                    
                    logger.info(f"  ✓ {rec.asset}: Dry run successful")
                    rec.execution_attempts += 1
                    rec.status = RecommendationStatus.APPROVED
                    
                    # Don't actually execute in dry-run mode
                    results['successful'].append(rec.to_dict())
                else:
                    # Real execution
                    exec_result = self.executor.execute_order(
                        asset=rec.asset,
                        quantity=rec.loss_amount / Decimal("100"),
                        strategy=strategy
                    )
                    
                    if exec_result.successful:
                        rec.status = RecommendationStatus.EXECUTED
                        rec.order_id = exec_result.order_id
                        rec.quantity_executed = exec_result.quantity_executed
                        rec.average_price_executed = exec_result.average_price
                        rec.fees_paid = exec_result.fees_paid
                        rec.execution_attempts += 1
                        rec.last_execution_time = datetime.now()
                        
                        results['successful'].append(rec.to_dict())
                        results['total_fees'] += exec_result.fees_paid
                        
                        logger.info(f"  ✅ {rec.asset}: Executed - {exec_result.quantity_executed} @ {exec_result.average_price}")
                    else:
                        rec.status = RecommendationStatus.FAILED
                        rec.last_execution_error = exec_result.error
                        rec.execution_attempts += 1
                        results['failed'].append(rec.to_dict())
                        logger.error(f"  ❌ {rec.asset}: Execution failed - {exec_result.error}")
            
            except Exception as e:
                logger.error(f"  ❌ {rec.asset}: Exception - {str(e)}")
                rec.status = RecommendationStatus.FAILED
                rec.last_execution_error = str(e)
                results['failed'].append(rec.to_dict())
        
        results['total_tax_savings'] = float(plan.estimated_tax_savings)
        
        logger.info(f"✅ Plan execution complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        
        return results
    
    # Helper methods
    
    def _check_wash_sale(self, asset: str, purchase_date: datetime) -> int:
        """Check wash-sale periods - return days remaining or 0"""
        # Simplified: check if sold same asset in last 30 days
        # In real implementation, query trade history
        return 0
    
    def _calculate_liquidity(self, asset: str, quantity: Decimal) -> float:
        """Calculate liquidity score 0-100"""
        # Major assets: 100, minor: 50
        major_assets = {'BTC', 'ETH', 'USDC', 'USDT'}
        return 100.0 if asset in major_assets else 50.0
    
    def _get_volatility(self, asset: str) -> float:
        """Get 30-day volatility percentage"""
        # Simplified - in real: fetch from market data service
        return 15.0
    
    def _get_tax_rate(self, asset: str) -> float:
        """Get applicable tax rate"""
        # Simplified - in real: calculate based on country/jurisdiction
        return 24.0
    
    def _get_price_momentum(self, asset: str) -> float:
        """Get price momentum (-ve = falling, +ve = rising)"""
        # Simplified - in real: calculate from price history
        return 0.0
    
    # API Methods
    
    def get_recommendations(self, status: Optional[RecommendationStatus] = None) -> List[Dict]:
        """Get all recommendations, optionally filtered by status"""
        recs = list(self.recommendations.values())
        if status:
            recs = [r for r in recs if r.status == status]
        return [r.to_dict() for r in recs]
    
    def get_recommendation(self, position_id: str) -> Optional[Dict]:
        """Get specific recommendation"""
        rec = self.recommendations.get(position_id)
        return rec.to_dict() if rec else None
    
    def approve_recommendation(self, position_id: str):
        """User approves a recommendation"""
        if position_id in self.recommendations:
            self.recommendations[position_id].status = RecommendationStatus.APPROVED
            logger.info(f"✅ Recommendation approved: {position_id}")
    
    def cancel_recommendation(self, position_id: str):
        """User cancels a recommendation"""
        if position_id in self.recommendations:
            self.recommendations[position_id].status = RecommendationStatus.CANCELLED
            logger.info(f"❌ Recommendation cancelled: {position_id}")
    
    def get_execution_history(self, limit: int = 100) -> List[Dict]:
        """Get execution history"""
        return self.execution_history[-limit:]


# Example usage
if __name__ == "__main__":
    from tlh_scorer import TLHScorer
    from tlh_executor import TLHExecutor
    
    # Initialize components
    engine = TLHEngine(
        scorer=TLHScorer(),
        executor=TLHExecutor()
    )
    
    # Simulate portfolio scan
    sample_positions = [
        {
            'id': 'pos_btc_001',
            'asset': 'BTC',
            'quantity': Decimal('1.5'),
            'average_cost': Decimal('35000'),
            'current_price': Decimal('30000'),
            'purchase_date': datetime.now() - timedelta(days=180),
            'exchanges': ['binance']
        },
        {
            'id': 'pos_eth_001',
            'asset': 'ETH',
            'quantity': Decimal('10'),
            'average_cost': Decimal('2500'),
            'current_price': Decimal('2000'),
            'purchase_date': datetime.now() - timedelta(days=90),
            'exchanges': ['kraken']
        }
    ]
    
    print("\n🔍 Scanning portfolio...\n")
    recommendations = engine.scan_portfolio(sample_positions)
    
    print("\n📋 Creating execution plan...\n")
    if recommendations:
        plan = engine.create_execution_plan([r.position_id for r in recommendations[:1]])
        print(f"Plan: {len(plan.recommendations)} recommendations")
        print(f"Estimated tax savings: ${plan.estimated_tax_savings:.2f}")
    
    print("\n✅ TLH Engine demo complete")
