"""
Pydantic schemas for TLH + Open Banking API
Request/Response validation
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ============================================================================
# TLH OPPORTUNITY SCHEMAS
# ============================================================================

class TLHPriorityBreakdown(BaseModel):
    """Score breakdown components"""
    tax_savings: float
    liquidity_score: float
    volatility_factor: float
    wash_sale_penalty: float
    fee_impact: float
    urgency_factor: float


class TLHOpportunityCreate(BaseModel):
    """Create new TLH opportunity"""
    position_id: str
    asset: str
    loss_amount: Decimal
    tax_rate: float = 24.0
    priority_score: float
    explanation: Optional[str] = None


class TLHOpportunityUpdate(BaseModel):
    """Update opportunity status"""
    status: Optional[str] = None
    execution_strategy: Optional[str] = None
    notes: Optional[str] = None


class TLHOpportunityExecute(BaseModel):
    """Execute opportunity"""
    strategy: str = Field(..., description="immediate, limit_price, or scheduled")
    limit_price: Optional[Decimal] = None
    scheduled_for: Optional[datetime] = None
    dry_run: bool = True


class TLHOpportunityResponse(BaseModel):
    """TLH opportunity response"""
    id: str
    user_id: str
    asset: str
    loss_amount: Decimal
    priority_score: float
    priority_breakdown: Optional[dict] = None
    explanation: Optional[str] = None
    status: str
    execution_strategy: Optional[str] = None
    wash_sale_risk: bool
    wash_sale_days_remaining: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TLHExecutionHistoryResponse(BaseModel):
    """Execution history entry"""
    id: str
    strategy: str
    status: str
    dry_run: bool
    order_id: Optional[str] = None
    quantity_executed: Optional[Decimal] = None
    average_price: Optional[Decimal] = None
    fees_paid: Optional[Decimal] = None
    executed_at: datetime
    
    class Config:
        from_attributes = True


class TLHExecutionResult(BaseModel):
    """Execution result"""
    success: bool
    opportunity_id: str
    order_id: Optional[str] = None
    status: str
    message: str
    dry_run: bool
    quantity_executed: Optional[Decimal] = None
    fees_paid: Optional[Decimal] = None


class TLHScanResult(BaseModel):
    """Scan portfolio for TLH opportunities"""
    opportunities_found: int
    total_harvestable_losses: Decimal
    total_tax_benefit: Decimal
    opportunities: list[TLHOpportunityResponse]


# ============================================================================
# BANK ACCOUNT SCHEMAS
# ============================================================================

class BankAccountConnect(BaseModel):
    """Connect new bank account"""
    bank_type: str = Field(..., description="nubank, mercado_pago, lemon, belo")
    account_number: str
    account_name: str
    currency: str = "BRL"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    # For OAuth flow - use auth code instead
    auth_code: Optional[str] = None


class BankAccountResponse(BaseModel):
    """Bank account response"""
    id: str
    bank_type: str
    account_number: str
    account_name: str
    currency: str
    balance: Decimal
    sync_status: str
    last_sync: Optional[datetime] = None
    connected_at: datetime
    
    class Config:
        from_attributes = True


class BankAccountSyncRequest(BaseModel):
    """Sync bank transactions"""
    days_back: int = 30
    force_full_sync: bool = False


class BankAccountSyncResponse(BaseModel):
    """Sync response"""
    account_id: str
    transactions_synced: int
    new_deposits: int
    new_withdrawals: int
    last_sync: datetime
    status: str


# ============================================================================
# BANK TRANSACTION SCHEMAS
# ============================================================================

class BankTransactionResponse(BaseModel):
    """Bank transaction response"""
    id: str
    date: datetime
    type: str
    amount: Decimal
    currency: str
    description: str
    counterparty: str
    balance_after: Optional[Decimal] = None
    matched_crypto_transaction_id: Optional[str] = None
    matched_confidence: float = 0.0
    
    class Config:
        from_attributes = True


class BankTransactionsFilterRequest(BaseModel):
    """Filter bank transactions"""
    account_id: str
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    type: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None


# ============================================================================
# TRANSACTION MATCHING SCHEMAS
# ============================================================================

class TransactionMatchRequest(BaseModel):
    """Create transaction match"""
    crypto_withdrawal_id: str
    bank_deposit_id: str
    crypto_amount: Decimal
    crypto_currency: str
    fiat_amount: Decimal
    fiat_currency: str
    exchange_rate: Decimal
    fees_paid: Decimal = 0
    notes: Optional[str] = None


class TransactionMatchResponse(BaseModel):
    """Transaction match response"""
    id: str
    crypto_withdrawal_id: str
    bank_deposit_id: str
    crypto_amount: Decimal
    crypto_currency: str
    fiat_amount: Decimal
    fiat_currency: str
    exchange_rate: Decimal
    fees_paid: Decimal
    confidence: float
    match_status: str
    crypto_date: datetime
    fiat_date: datetime
    time_delta_hours: float
    
    class Config:
        from_attributes = True


class TransactionMatchAutoRequest(BaseModel):
    """Auto-match crypto and bank transactions"""
    tolerance_percent: float = 2.0  # Tolerance for amount matching
    time_window_hours: int = 24


class TransactionMatchAutoResponse(BaseModel):
    """Auto-match results"""
    matches_found: int
    high_confidence_matches: int
    medium_confidence_matches: int
    matches: list[TransactionMatchResponse]


# ============================================================================
# CRYPTO WITHDRAWAL SCHEMAS
# ============================================================================

class CryptoWithdrawalResponse(BaseModel):
    """Crypto withdrawal response"""
    id: str
    exchange: str
    asset: str
    amount: Decimal
    amount_in_usd: Decimal
    destination_address: str
    tx_hash: str
    status: str
    matched_bank_deposit_id: Optional[str] = None
    match_confidence: float
    date_time: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMPLETE CYCLE DASHBOARD SCHEMAS
# ============================================================================

class CycleStageDetails(BaseModel):
    """Details for each stage"""
    stage_number: int
    stage_name: str
    status: str
    holdings: Optional[dict] = None
    exchange: Optional[dict] = None
    withdrawal: Optional[dict] = None
    blockchain: Optional[dict] = None
    bank: Optional[dict] = None


class CompleteCycleDashboard(BaseModel):
    """Complete crypto → fiat cycle"""
    user_id: str
    total_positions: int
    total_withdrawn_crypto: Decimal
    total_deposited_fiat: Decimal
    total_fees: Decimal
    matched_cycles: int
    pending_matches: int
    tax_ready: bool
    stages: list[CycleStageDetails]


# ============================================================================
# TAX AUDIT TRAIL SCHEMAS
# ============================================================================

class TaxAuditTrailEvent(BaseModel):
    """Individual audit trail event"""
    timestamp: datetime
    stage: str
    event_type: str
    description: str
    amount: Decimal
    currency: str
    proof_hash: Optional[str] = None


class TaxAuditTrailResponse(BaseModel):
    """Complete audit trail"""
    transaction_id: str
    events: list[TaxAuditTrailEvent]
    total_amount: Decimal
    currency: str
    completion_percentage: float


# ============================================================================
# PRICE EVENTS SCHEMAS
# ============================================================================

class PriceEventResponse(BaseModel):
    """Price event response"""
    id: str
    event_type: str
    asset: str
    previous_price: Decimal
    current_price: Decimal
    price_change_pct: float
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# BULK OPERATIONS SCHEMAS
# ============================================================================

class BulkExecuteRequest(BaseModel):
    """Execute multiple opportunities"""
    opportunity_ids: list[str]
    strategy: str = "immediate"
    dry_run: bool = True


class BulkExecuteResponse(BaseModel):
    """Bulk execution result"""
    total_opportunities: int
    successful: int
    failed: int
    pending: int
    total_harvestable_loss: Decimal
    total_tax_benefit: Decimal
    results: list[TLHExecutionResult]


# ============================================================================
# ANALYTICS SCHEMAS
# ============================================================================

class TLHMetrics(BaseModel):
    """TLH system metrics"""
    total_harvestable_losses: Decimal
    total_tax_benefit: Decimal
    average_priority_score: float
    wash_sale_risks: int
    executed_opportunities: int
    pending_executions: int
    success_rate: float
    average_fees: Decimal


class BankingMetrics(BaseModel):
    """Banking integration metrics"""
    connected_banks: int
    synced_accounts: int
    total_transactions: int
    unmatched_transactions: int
    matched_deposits: int
    average_match_confidence: float
    total_volume: Decimal
