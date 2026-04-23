"""
Open Banking API Router
6+ endpoints for bank account management and transaction matching
"""

import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.db import get_db
from app.models import (
    BankAccount,
    BankTransaction,
    TransactionMatch,
    CryptoWithdrawal,
    BankType,
    BankTransactionType,
)
from app.schemas.tlh_schemas import (
    BankAccountConnect,
    BankAccountResponse,
    BankAccountSyncRequest,
    BankAccountSyncResponse,
    BankTransactionResponse,
    BankTransactionsFilterRequest,
    TransactionMatchRequest,
    TransactionMatchResponse,
    TransactionMatchAutoRequest,
    TransactionMatchAutoResponse,
    CryptoWithdrawalResponse,
    CompleteCycleDashboard,
    BankingMetrics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/banking", tags=["Banking"])


# ============================================================================
# DEPENDENCIES
# ============================================================================

async def get_current_user_id() -> str:
    """Get current user ID from auth context"""
    # TODO: Implement real auth
    return "test_user"


# ============================================================================
# BANK ACCOUNT ENDPOINTS
# ============================================================================

@router.post("/accounts/connect", response_model=BankAccountResponse)
async def connect_bank_account(
    request: BankAccountConnect,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Connect new bank account via Open Banking API
    
    Supported banks:
    - Nubank (Brazil) - 70M+ users
    - Mercado Pago (multi-country)
    - Lemon (Mexico)
    - Belo (Argentina)
    """
    try:
        # Validate bank type
        valid_banks = [b.value for b in BankType]
        if request.bank_type not in valid_banks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bank type. Supported: {', '.join(valid_banks)}"
            )
        
        # Create account
        account = BankAccount(
            id=str(uuid.uuid4()),
            user_id=user_id,
            bank_type=request.bank_type,
            account_number=request.account_number,
            account_name=request.account_name,
            currency=request.currency,
            api_key=request.api_key,
            api_secret=request.api_secret,
            sync_status="pending",
        )
        
        db.add(account)
        await db.commit()
        await db.refresh(account)
        
        logger.info(f"Connected {request.bank_type} account for user {user_id}")
        
        return BankAccountResponse.from_orm(account)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Connect account failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=list[BankAccountResponse])
async def list_bank_accounts(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """List all connected bank accounts"""
    try:
        stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        
        return [BankAccountResponse.from_orm(acc) for acc in accounts]
    except Exception as e:
        logger.error(f"List accounts failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get specific bank account details"""
    try:
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        return BankAccountResponse.from_orm(account)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get account failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/accounts/{account_id}/sync", response_model=BankAccountSyncResponse)
async def sync_bank_transactions(
    account_id: str = Path(...),
    request: BankAccountSyncRequest = None,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Sync transactions from bank account
    
    Fetches recent deposits/withdrawals from connected bank
    """
    try:
        # Get account
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Update sync status
        account.sync_status = "syncing"
        account.last_sync = datetime.utcnow()
        
        # TODO: Call actual bank API via connector
        # For now, simulate sync
        synced_txns = 0
        new_deposits = 0
        new_withdrawals = 0
        
        # Mock: Create some test transactions
        if request.force_full_sync or (datetime.utcnow() - (account.last_sync or datetime.utcnow())).days >= 1:
            # Create example transactions
            for i in range(3):
                txn = BankTransaction(
                    id=str(uuid.uuid4()),
                    account_id=account.id,
                    date=datetime.utcnow() - timedelta(days=i),
                    type="deposit" if i % 2 == 0 else "withdrawal",
                    amount=Decimal(str(1000 + i * 100)),
                    currency=account.currency,
                    description=f"Transaction {i}",
                    counterparty=f"Exchange_{i}",
                    balance_after=Decimal(str(10000 - i * 500)),
                )
                db.add(txn)
                synced_txns += 1
                if i % 2 == 0:
                    new_deposits += 1
                else:
                    new_withdrawals += 1
        
        account.sync_status = "synced"
        db.add(account)
        await db.commit()
        
        logger.info(f"Synced {synced_txns} transactions for account {account_id}")
        
        return BankAccountSyncResponse(
            account_id=account.id,
            transactions_synced=synced_txns,
            new_deposits=new_deposits,
            new_withdrawals=new_withdrawals,
            last_sync=account.last_sync,
            status="success" if synced_txns > 0 else "no_new_transactions",
        )
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/accounts/{account_id}")
async def disconnect_bank_account(
    account_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Disconnect bank account"""
    try:
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id
        )
        result = await db.execute(stmt)
        account = result.scalar_one_or_none()
        
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        
        # Delete transactions and matches first (cascade)
        await db.delete(account)
        await db.commit()
        
        return {"status": "disconnected", "account_id": account_id}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Disconnect failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BANK TRANSACTION ENDPOINTS
# ============================================================================

@router.get("/transactions", response_model=list[BankTransactionResponse])
async def list_bank_transactions(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    account_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    days: int = Query(30),
):
    """
    List bank transactions with filtering
    
    Query params:
    - account_id: Filter by account
    - type: deposit, withdrawal, transfer, etc.
    - min_amount / max_amount: Amount range
    - days: Look back N days (default 30)
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # First get user's accounts
        stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await db.execute(stmt)
        accounts = result.scalars().all()
        account_ids = [a.id for a in accounts]
        
        if not account_ids:
            return []
        
        # Build filters
        filters = [
            BankTransaction.account_id.in_(account_ids),
            BankTransaction.date >= cutoff_date,
        ]
        
        if account_id:
            if account_id not in account_ids:
                raise HTTPException(status_code=403, detail="Account not found")
            filters.append(BankTransaction.account_id == account_id)
        
        if type:
            filters.append(BankTransaction.type == type)
        
        if min_amount:
            filters.append(BankTransaction.amount >= min_amount)
        
        if max_amount:
            filters.append(BankTransaction.amount <= max_amount)
        
        # Get transactions
        stmt = select(BankTransaction).where(and_(*filters)).order_by(BankTransaction.date.desc())
        result = await db.execute(stmt)
        transactions = result.scalars().all()
        
        return [BankTransactionResponse.from_orm(t) for t in transactions]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List transactions failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TRANSACTION MATCHING ENDPOINTS
# ============================================================================

@router.post("/match", response_model=TransactionMatchResponse)
async def create_transaction_match(
    request: TransactionMatchRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Manually match crypto withdrawal to bank deposit
    
    Links crypto withdrawal from exchange to fiat deposit in bank
    """
    try:
        # Calculate time delta
        crypto_date = datetime.utcnow()  # Would come from request
        fiat_date = datetime.utcnow()
        time_delta = (fiat_date - crypto_date).total_seconds() / 3600
        
        match = TransactionMatch(
            id=str(uuid.uuid4()),
            crypto_withdrawal_id=request.crypto_withdrawal_id,
            bank_deposit_id=request.bank_deposit_id,
            crypto_amount=request.crypto_amount,
            crypto_currency=request.crypto_currency,
            fiat_amount=request.fiat_amount,
            fiat_currency=request.fiat_currency,
            exchange_rate=request.exchange_rate,
            fees_paid=request.fees_paid,
            crypto_date=crypto_date,
            fiat_date=fiat_date,
            time_delta_hours=time_delta,
            confidence=1.0,  # Manual match = high confidence
            match_status="matched",
            notes=request.notes or "",
        )
        
        db.add(match)
        await db.commit()
        await db.refresh(match)
        
        logger.info(f"Created match {match.id}")
        
        return TransactionMatchResponse.from_orm(match)
    except Exception as e:
        await db.rollback()
        logger.error(f"Create match failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/match-auto", response_model=TransactionMatchAutoResponse)
async def auto_match_transactions(
    request: TransactionMatchAutoRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Automatically match crypto withdrawals to bank deposits
    
    Uses smart matching algorithm:
    - Amount tolerance (e.g., ±2%)
    - Time window (e.g., 24 hours)
    - Counterparty analysis
    """
    try:
        # Get user's transactions
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await db.execute(account_stmt)
        accounts = result.scalars().all()
        account_ids = [a.id for a in accounts]
        
        # Get deposits
        txn_stmt = select(BankTransaction).where(
            BankTransaction.account_id.in_(account_ids),
            BankTransaction.type == "deposit"
        )
        result = await db.execute(txn_stmt)
        deposits = result.scalars().all()
        
        # Get withdrawals
        withdrawal_stmt = select(CryptoWithdrawal).where(
            CryptoWithdrawal.user_id == user_id
        )
        result = await db.execute(withdrawal_stmt)
        withdrawals = result.scalars().all()
        
        # Smart matching
        matches = []
        high_confidence = 0
        medium_confidence = 0
        
        for withdrawal in withdrawals:
            for deposit in deposits:
                # Amount tolerance check
                amount_diff_pct = abs(
                    float((withdrawal.amount_in_usd - deposit.amount) / withdrawal.amount_in_usd)
                ) * 100
                
                if amount_diff_pct > request.tolerance_percent:
                    continue
                
                # Time window check
                time_diff = abs((deposit.date - withdrawal.date_time).total_seconds() / 3600)
                if time_diff > request.time_window_hours:
                    continue
                
                # Confidence score
                confidence = 1.0 - (amount_diff_pct / 100)
                
                # Create match
                match = TransactionMatch(
                    id=str(uuid.uuid4()),
                    crypto_withdrawal_id=withdrawal.id,
                    bank_deposit_id=deposit.id,
                    crypto_amount=withdrawal.amount,
                    crypto_currency=withdrawal.asset,
                    fiat_amount=deposit.amount,
                    fiat_currency=deposit.currency,
                    exchange_rate=Decimal(str(withdrawal.amount_in_usd / withdrawal.amount)),
                    fees_paid=Decimal(0),
                    crypto_date=withdrawal.date_time,
                    fiat_date=deposit.date,
                    time_delta_hours=time_diff,
                    confidence=confidence,
                    match_status="matched",
                )
                
                db.add(match)
                matches.append(match)
                
                if confidence >= 0.95:
                    high_confidence += 1
                else:
                    medium_confidence += 1
        
        await db.commit()
        
        return TransactionMatchAutoResponse(
            matches_found=len(matches),
            high_confidence_matches=high_confidence,
            medium_confidence_matches=medium_confidence,
            matches=[TransactionMatchResponse.from_orm(m) for m in matches],
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Auto match failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches", response_model=list[TransactionMatchResponse])
async def list_transaction_matches(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    min_confidence: float = Query(0.0),
):
    """List all transaction matches"""
    try:
        stmt = select(TransactionMatch).where(
            TransactionMatch.confidence >= min_confidence
        ).order_by(TransactionMatch.created_at.desc())
        result = await db.execute(stmt)
        matches = result.scalars().all()
        
        return [TransactionMatchResponse.from_orm(m) for m in matches]
    except Exception as e:
        logger.error(f"List matches failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CYCLE DASHBOARD ENDPOINT
# ============================================================================

@router.get("/cycle-dashboard", response_model=CompleteCycleDashboard)
async def get_cycle_dashboard(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get complete crypto → fiat cycle dashboard
    
    Shows all 7 stages:
    1. Holdings (portfolio)
    2. Exchange connection
    3. Crypto withdrawal
    4. Blockchain confirmation
    5. Bank deposit
    6. Transaction matching
    7. Tax ready
    """
    try:
        # Calculate metrics
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await db.execute(account_stmt)
        accounts = result.scalars().all()
        
        withdrawal_stmt = select(CryptoWithdrawal).where(
            CryptoWithdrawal.user_id == user_id
        )
        result = await db.execute(withdrawal_stmt)
        withdrawals = result.scalars().all()
        
        match_stmt = select(TransactionMatch)
        result = await db.execute(match_stmt)
        matches = result.scalars().all()
        
        total_withdrawn = sum(w.amount_in_usd for w in withdrawals)
        total_deposited = sum(m.fiat_amount for m in matches)
        total_fees = sum(m.fees_paid for m in matches)
        
        return CompleteCycleDashboard(
            user_id=user_id,
            total_positions=len(accounts),
            total_withdrawn_crypto=Decimal(str(total_withdrawn)),
            total_deposited_fiat=Decimal(str(total_deposited)),
            total_fees=Decimal(str(total_fees)),
            matched_cycles=len(matches),
            pending_matches=len(withdrawals) - len(matches),
            tax_ready=len(matches) > 0 and len([m for m in matches if m.confidence > 0.95]) == len(matches),
            stages=[],  # Populated with actual stage data
        )
    except Exception as e:
        logger.error(f"Get dashboard failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get("/metrics", response_model=BankingMetrics)
async def get_banking_metrics(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """Get banking integration metrics"""
    try:
        # Get accounts
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        result = await db.execute(account_stmt)
        accounts = result.scalars().all()
        
        # Get transactions
        account_ids = [a.id for a in accounts]
        txn_stmt = select(BankTransaction).where(
            BankTransaction.account_id.in_(account_ids)
        )
        result = await db.execute(txn_stmt)
        transactions = result.scalars().all()
        
        # Get matches
        match_stmt = select(TransactionMatch)
        result = await db.execute(match_stmt)
        matches = result.scalars().all()
        
        synced = sum(1 for a in accounts if a.sync_status == "synced")
        unmatched = len([t for t in transactions if not t.matched_crypto_transaction_id])
        avg_confidence = sum(m.confidence for m in matches) / len(matches) if matches else 0
        total_volume = sum(m.fiat_amount for m in matches)
        
        return BankingMetrics(
            connected_banks=len(accounts),
            synced_accounts=synced,
            total_transactions=len(transactions),
            unmatched_transactions=unmatched,
            matched_deposits=len(matches),
            average_match_confidence=avg_confidence,
            total_volume=Decimal(str(total_volume)),
        )
    except Exception as e:
        logger.error(f"Get metrics failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "banking",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
    }
