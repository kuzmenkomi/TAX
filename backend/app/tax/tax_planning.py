"""
Tax Planning Simulator - "What-If" Scenario Analysis

Calculates tax impact of hypothetical transactions:
- What if I sold these positions now vs in 3 months?
- What if I harvest losses strategically?
- What's my long-term capital gains rate vs short-term?
- How much in taxes if I convert staking rewards to USD?

Helps users make tax-optimal decisions before executing trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import pandas as pd


@dataclass
class TaxPosition:
    """A held position for tax planning."""
    
    asset: str
    quantity: Decimal
    cost_basis: Decimal  # Cost per unit
    current_price: Decimal
    acquisition_date: datetime
    
    @property
    def total_cost(self) -> Decimal:
        """Total value paid for this position."""
        return self.cost_basis * self.quantity
    
    @property
    def current_value(self) -> Decimal:
        """Current market value."""
        return self.current_price * self.quantity
    
    @property
    def unrealized_gain(self) -> Decimal:
        """Unrealized profit/loss."""
        return self.current_value - self.total_cost
    
    @property
    def gain_percentage(self) -> Decimal:
        """Gain as percentage of cost basis."""
        if self.total_cost == 0:
            return Decimal("0")
        return (self.unrealized_gain / self.total_cost) * 100
    
    @property
    def holding_period_days(self) -> int:
        """Days held (for short-term vs long-term determination)."""
        return (datetime.now() - self.acquisition_date).days
    
    @property
    def is_long_term(self) -> bool:
        """True if held >365 days (long-term capital gains treatment in most countries)."""
        return self.holding_period_days > 365
    
    def days_until_long_term(self) -> int:
        """Days until long-term status achieved."""
        if self.is_long_term:
            return 0
        long_term_date = self.acquisition_date + timedelta(days=365)
        return (long_term_date - datetime.now()).days


class TaxScenario:
    """Tax impact of a hypothetical transaction."""
    
    def __init__(
        self,
        name: str,
        description: str,
        position: TaxPosition,
        quantity_to_sell: Decimal,
        sale_price: Optional[Decimal] = None,
    ):
        """Create a tax scenario (hypothetical sale).
        
        Args:
            name: Scenario name (e.g., "Sell Now", "Wait 3 Months")
            description: Description of the scenario
            position: The position being analyzed
            quantity_to_sell: Quantity to hypothetically sell
            sale_price: Sale price (if None, uses current price)
        """
        self.name = name
        self.description = description
        self.position = position
        self.quantity_to_sell = quantity_to_sell
        self.sale_price = sale_price or position.current_price
    
    @property
    def proceeds(self) -> Decimal:
        """Gross proceeds from sale."""
        return self.quantity_to_sell * self.sale_price
    
    @property
    def cost_basis(self) -> Decimal:
        """Cost basis for sold quantity."""
        return self.quantity_to_sell * self.position.cost_basis
    
    @property
    def capital_gain(self) -> Decimal:
        """Realized capital gain/loss."""
        return self.proceeds - self.cost_basis
    
    @property
    def is_long_term(self) -> bool:
        """True if this sale qualifies as long-term capital gain."""
        return self.position.is_long_term
    
    @property
    def tax_rate(self) -> Decimal:
        """Tax rate applicable to this scenario."""
        if self.is_long_term:
            return Decimal("0.15")  # Long-term capital gains rate (15% in USA)
        else:
            return Decimal("0.35")  # Short-term rate (up to 35% in USA)
    
    @property
    def estimated_tax(self) -> Decimal:
        """Estimated tax on capital gain."""
        if self.capital_gain <= 0:
            return Decimal("0")  # No tax on losses
        return self.capital_gain * self.tax_rate
    
    @property
    def after_tax_proceeds(self) -> Decimal:
        """Proceeds after taxes."""
        return self.proceeds - self.estimated_tax
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "name": self.name,
            "description": self.description,
            "position": self.position.asset,
            "quantity_sold": float(self.quantity_to_sell),
            "sale_price": float(self.sale_price),
            "proceeds": float(self.proceeds),
            "cost_basis": float(self.cost_basis),
            "capital_gain": float(self.capital_gain),
            "holding_period": "long-term" if self.is_long_term else "short-term",
            "days_held": self.position.holding_period_days,
            "tax_rate": f"{float(self.tax_rate)*100:.0f}%",
            "estimated_tax": float(self.estimated_tax),
            "after_tax_proceeds": float(self.after_tax_proceeds),
        }


class TaxPlanningSimulator:
    """Simulates tax impact of different trading/holding scenarios."""
    
    @staticmethod
    def scenario_sell_now(position: TaxPosition) -> TaxScenario:
        """Scenario: Sell entire position at current price."""
        return TaxScenario(
            name="Sell Now",
            description=f"Sell all {position.quantity} {position.asset} at current price",
            position=position,
            quantity_to_sell=position.quantity,
            sale_price=position.current_price,
        )
    
    @staticmethod
    def scenario_wait_for_long_term(position: TaxPosition) -> TaxScenario:
        """Scenario: Hold for long-term capital gains treatment (>365 days)."""
        if position.is_long_term:
            return TaxScenario(
                name="Already Long-Term",
                description=f"Position already held {position.holding_period_days} days",
                position=position,
                quantity_to_sell=position.quantity,
            )
        else:
            days_left = position.days_until_long_term()
            return TaxScenario(
                name=f"Wait {days_left} Days (Long-Term)",
                description=f"Hold for {days_left} more days to qualify for long-term treatment",
                position=position,
                quantity_to_sell=position.quantity,
            )
    
    @staticmethod
    def scenario_partial_harvest_losses(
        position: TaxPosition,
        percentage: float = 0.5
    ) -> TaxScenario:
        """Scenario: Harvest losses with partial position sale."""
        quantity_to_sell = position.quantity * Decimal(str(percentage))
        return TaxScenario(
            name=f"Harvest {percentage*100:.0f}% Losses",
            description=f"Sell {percentage*100:.0f}% to realize losses for tax offset",
            position=position,
            quantity_to_sell=quantity_to_sell,
            sale_price=position.current_price,
        )
    
    @staticmethod
    def scenario_price_targets(
        position: TaxPosition,
        price_targets: list[Decimal],
    ) -> list[TaxScenario]:
        """Scenarios: Tax impact at different price points.
        
        Useful for: "If BTC hits $50k, how much in taxes?"
        """
        scenarios = []
        for target_price in price_targets:
            percent_change = ((target_price - position.current_price) / position.current_price * 100)
            
            scenario = TaxScenario(
                name=f"At ${target_price:,.2f} ({percent_change:+.1f}%)",
                description=f"Tax impact if {position.asset} price moves to ${target_price:,.2f}",
                position=position,
                quantity_to_sell=position.quantity,
                sale_price=target_price,
            )
            scenarios.append(scenario)
        
        return scenarios
    
    @staticmethod
    def compare_scenarios(scenarios: list[TaxScenario]) -> dict:
        """Compare tax impact across multiple scenarios.
        
        Returns:
            Comparison with tax savings opportunities identified
        """
        if not scenarios:
            return {"error": "No scenarios provided"}
        
        scenarios_data = [s.to_dict() for s in scenarios]
        
        # Find best/worst scenarios
        best_scenario = min(scenarios, key=lambda x: x.estimated_tax)
        worst_scenario = max(scenarios, key=lambda x: x.estimated_tax)
        
        total_tax_range = worst_scenario.estimated_tax - best_scenario.estimated_tax
        
        return {
            "scenarios": scenarios_data,
            "comparison": {
                "best_scenario": best_scenario.name,
                "best_estimated_tax": float(best_scenario.estimated_tax),
                "worst_scenario": worst_scenario.name,
                "worst_estimated_tax": float(worst_scenario.estimated_tax),
                "tax_savings_opportunity": float(total_tax_range),
                "recommendation": _generate_recommendation(scenarios),
            }
        }


def _generate_recommendation(scenarios: list[TaxScenario]) -> str:
    """Generate tax optimization recommendation."""
    # Find scenarios with losses
    loss_scenarios = [s for s in scenarios if s.capital_gain < 0]
    long_term_scenarios = [s for s in scenarios if s.is_long_term]
    
    if loss_scenarios:
        return (
            "🔴 Loss Harvesting Opportunity: "
            f"Realize losses from {loss_scenarios[0].position.asset} to offset gains"
        )
    
    if long_term_scenarios and not all(s.is_long_term for s in scenarios):
        days_to_wait = min(s.position.days_until_long_term() for s in scenarios if not s.is_long_term)
        if days_to_wait <= 30:
            return (
                "⏳ Timing Opportunity: "
                f"Wait {days_to_wait} days for long-term capital gains treatment (save ~15-20%)"
            )
    
    return "✅ Tax position is already optimized"


# ==================== ADVANCED SCENARIOS ====================

class IncomeOptimizationScenario:
    """Tax impact of different income recognition strategies."""
    
    @staticmethod
    def compare_income_sources(
        staking_income: Decimal,
        airdrop_income: Decimal,
        lending_income: Decimal,
        ordinary_tax_rate: Decimal = Decimal("0.35"),
    ) -> dict:
        """Compare tax impact of different income types.
        
        In most countries:
        - Staking rewards: Ordinary income (35%)
        - Airdrops: Ordinary income (35%)
        - Lending interest: Ordinary income (35%)
        
        But strategies like converting to staking could affect timing.
        """
        
        total_income = staking_income + airdrop_income + lending_income
        total_tax = total_income * ordinary_tax_rate
        
        breakdown = {
            "staking": {
                "amount": float(staking_income),
                "tax": float(staking_income * ordinary_tax_rate),
                "strategy": "Compounding postpones realization until sales"
            },
            "airdrops": {
                "amount": float(airdrop_income),
                "tax": float(airdrop_income * ordinary_tax_rate),
                "strategy": "Hold long-term to convert gains to long-term capital gains"
            },
            "lending": {
                "amount": float(lending_income),
                "tax": float(lending_income * ordinary_tax_rate),
                "strategy": "Track by platform; some jurisdictions offer deductions"
            }
        }
        
        return {
            "total_income": float(total_income),
            "total_estimated_tax": float(total_tax),
            "tax_rate": f"{float(ordinary_tax_rate)*100:.0f}%",
            "breakdown": breakdown,
            "optimization_tips": [
                "🎯 Hold airdrops for 365+ days to convert to long-term capital gains",
                "📊 Reinvest staking rewards to defer tax realization",
                "🔄 Consider deducting platform/custody fees",
            ]
        }


# ==================== API INTEGRATION ====================
"""
Add to your FastAPI app:

from app.tax.tax_planning import (
    TaxPlanningSimulator,
    TaxPosition,
    IncomeOptimizationScenario
)
from datetime import datetime
from decimal import Decimal

@app.post("/tax-planning/scenarios/{position_id}")
def analyze_tax_scenarios(
    position_id: int,
    price_targets: list[float] = None,
    include_loss_harvest: bool = True,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Analyze tax impact of different selling/holding scenarios for a position.'''
    
    # Get position from database
    position_data = db.query(Transaction).filter(
        Transaction.id == position_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not position_data:
        raise HTTPException(status_code=404)
    
    # Create TaxPosition object
    position = TaxPosition(
        asset=position_data.asset,
        quantity=Decimal(str(position_data.quantity)),
        cost_basis=Decimal(str(position_data.price)),
        current_price=Decimal(str(position_data.current_price)),
        acquisition_date=position_data.timestamp
    )
    
    # Generate scenarios
    scenarios = [
        TaxPlanningSimulator.scenario_sell_now(position),
        TaxPlanningSimulator.scenario_wait_for_long_term(position),
    ]
    
    if include_loss_harvest and position.unrealized_gain < 0:
        scenarios.append(
            TaxPlanningSimulator.scenario_partial_harvest_losses(position, 0.5)
        )
    
    if price_targets:
        scenarios.extend(
            TaxPlanningSimulator.scenario_price_targets(
                position,
                [Decimal(str(p)) for p in price_targets]
            )
        )
    
    # Compare all scenarios
    comparison = TaxPlanningSimulator.compare_scenarios(scenarios)
    
    return {
        "position": position.asset,
        "analysis": comparison
    }


@app.get("/tax-planning/income-optimization")
def analyze_income_optimization(
    staking_income: float = 0,
    airdrop_income: float = 0,
    lending_income: float = 0,
    current_user = Depends(get_current_user),
):
    '''Analyze tax efficiency of different income recognition strategies.'''
    
    analysis = IncomeOptimizationScenario.compare_income_sources(
        staking_income=Decimal(str(staking_income)),
        airdrop_income=Decimal(str(airdrop_income)),
        lending_income=Decimal(str(lending_income)),
    )
    
    return analysis


@app.post("/tax-planning/portfolio-projection")
def project_portfolio_taxes(
    positions: list[dict],  # [{asset, qty, cost_basis, current_price}, ...]
    current_user = Depends(get_current_user),
):
    '''Project total portfolio tax liability with optimization recommendations.'''
    
    tax_positions = [
        TaxPosition(
            asset=p["asset"],
            quantity=Decimal(str(p["quantity"])),
            cost_basis=Decimal(str(p["cost_basis"])),
            current_price=Decimal(str(p["current_price"])),
            acquisition_date=datetime.fromisoformat(p["acquisition_date"]),
        )
        for p in positions
    ]
    
    total_gains = Decimal("0")
    total_losses = Decimal("0")
    long_term_gains = Decimal("0")
    short_term_gains = Decimal("0")
    
    for pos in tax_positions:
        if pos.unrealized_gain > 0:
            total_gains += pos.unrealized_gain
            if pos.is_long_term:
                long_term_gains += pos.unrealized_gain
            else:
                short_term_gains += pos.unrealized_gain
        else:
            total_losses += pos.unrealized_gain
    
    # Calculate estimated taxes
    long_term_tax = long_term_gains * Decimal("0.15")
    short_term_tax = short_term_gains * Decimal("0.35")
    
    return {
        "total_unrealized_gains": float(total_gains),
        "total_unrealized_losses": float(abs(total_losses)),
        "long_term_gains": float(long_term_gains),
        "short_term_gains": float(short_term_gains),
        "estimated_taxes": {
            "long_term_tax": float(long_term_tax),
            "short_term_tax": float(short_term_tax),
            "total": float(long_term_tax + short_term_tax),
        },
        "optimization_opportunities": [
            "Consider harvesting short-term losses to offset short-term gains",
            "Wait for long-term status on positions held <365 days",
            "Stagger sales to spread tax impact across multiple years",
        ]
    }
"""
