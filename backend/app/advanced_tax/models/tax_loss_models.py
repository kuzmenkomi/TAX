"""
Tax-Loss Harvesting Models
Database schema for tax-loss optimization
"""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Numeric, DECIMAL, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.advanced_tax.integration.database import Base
from app.advanced_tax.models.shared import BaseModel
from app.advanced_tax.utils import HarvestStatus, RiskLevel


class TaxLossHarvest(BaseModel):
    """
    Tax-loss harvesting opportunity.
    Represents a potential tax-saving harvest action.
    """
    __tablename__ = "tax_loss_harvests"
    
    # User & country
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), index=True)
    country: Mapped[str] = mapped_column(String(2), index=True)  # MX, BR, AR, etc.
    
    # Asset details
    asset: Mapped[str] = mapped_column(String(12), index=True)  # BTC, ETH, ADA
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    quantity_to_sell: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))  # Partial sell support
    
    # Pricing
    purchase_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))  # Avg cost basis
    current_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    cost_basis_method: Mapped[str] = mapped_column(String(10), default="FIFO")  # FIFO, LIFO, AVCO
    
    # Loss calculation
    loss_amount: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))  # Negative if loss
    loss_percentage: Mapped[float] = mapped_column(Float)  # -10.5 for -10.5%
    
    # Fee handling
    estimated_fees: Mapped[Decimal] = mapped_column(DECIMAL(20, 2), default=Decimal("0"))
    fee_percentage: Mapped[float] = mapped_column(Float, default=0.1)  # Exchange fee %
    
    # Tax impact
    tax_rate: Mapped[float] = mapped_column(Float)  # User's marginal rate
    tax_savings: Mapped[Decimal] = mapped_column(DECIMAL(20, 2))  # Potential savings
    
    # Wash-sale tracking
    wash_sale_days_remaining: Mapped[int] = mapped_column(Integer, default=0)
    last_sell_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Risk assessment
    volatility: Mapped[float] = mapped_column(Float)  # 30-day volatility %
    liquidity_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100 (100=very liquid)
    risk_level: Mapped[str] = mapped_column(String(10), default="medium")  # low, medium, high
    
    # Priority score (0-100) - TRANSPARENT BREAKDOWN
    priority_score: Mapped[float] = mapped_column(Float)
    priority_breakdown: Mapped[dict] = mapped_column(JSON, nullable=True)  # Transparent breakdown
    # Example:
    # {
    #   "tax_savings_component": 0.40,      # 40%
    #   "liquidity_component": 0.35,        # 35%
    #   "volatility_component": 0.15,       # 15%
    #   "wash_sale_penalty": -0.10,         # -10% if near wash-sale
    #   "fee_impact": 0.10,                 # +10% if fees are low
    #   "total_score": 95.2
    # }
    
    # Status tracking
    status: Mapped[str] = mapped_column(
        String(20),
        default=HarvestStatus.IDENTIFIED,
        index=True
    )
    
    # Execution details
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    executed_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=True)
    exchange_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Where to execute
    
    # Rebuy scheduling
    rebuy_scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rebuy_executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    rebuy_price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=True)
    rebuy_asset: Mapped[str] = mapped_column(String(12), nullable=True)  # For diversification
    
    # Metadata
    notes: Mapped[str] = mapped_column(String(500), nullable=True)
    audit_data: Mapped[dict] = mapped_column(JSON, nullable=True)  # For debugging
    
    # Execution tracking (NEW!)
    execution_status: Mapped[str] = mapped_column(String(20), default="recommended")
    # recommended → dry_run → pending → executing → executed → failed → cancelled
    
    execution_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_execution_error: Mapped[str] = mapped_column(String(500), nullable=True)
    dry_run_result: Mapped[dict] = mapped_column(JSON, nullable=True)  # Results from dry run
    
    def can_harvest(self) -> bool:
        """Check if ready to harvest (no wash-sale conflict)"""
        return self.wash_sale_days_remaining == 0
    
    def net_tax_benefit(self) -> Decimal:
        """Calculate net benefit after fees"""
        return self.tax_savings - self.estimated_fees
    
    def __repr__(self):
        return f"<TaxLossHarvest {self.asset} -{self.loss_percentage:.1f}% τ{self.tax_savings}>"


class HarvestAction(BaseModel):
    """
    Individual sell/rebuy action for a harvest.
    Tracks execution and transaction history.
    """
    __tablename__ = "harvest_actions"
    
    # Link to harvest
    harvest_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tax_loss_harvests.id"),
        index=True
    )
    
    # Action details
    action_type: Mapped[str] = mapped_column(String(10))  # SELL, REBUY
    asset: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    price: Mapped[Decimal] = mapped_column(DECIMAL(20, 8))
    
    # Execution
    executed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20))  # pending, confirmed, failed
    
    # Transaction reference
    transaction_id: Mapped[str] = mapped_column(String(128), nullable=True)  # On-chain or exchange
    
    # Fee tracking
    fee_amount: Mapped[Decimal] = mapped_column(DECIMAL(20, 8), nullable=True)
    fee_currency: Mapped[str] = mapped_column(String(10), nullable=True)
    
    def __repr__(self):
        return f"<HarvestAction {self.action_type} {self.quantity} {self.asset}>"
