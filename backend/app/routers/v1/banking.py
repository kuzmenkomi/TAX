"""
Open Banking API Router
Endpoints for bank account management and transaction matching.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.api_errors import server_error
from app.core.db import get_db
from app.models import (
    BankAccount,
    BankTransaction,
    CryptoWithdrawal,
    TransactionMatch,
    BankType,
    User,
)
from app.schemas.tlh_schemas import (
    BankAccountConnect,
    BankAccountResponse,
    BankAccountSyncRequest,
    BankAccountSyncResponse,
    BankTransactionResponse,
    TransactionMatchAutoRequest,
    TransactionMatchAutoResponse,
    TransactionMatchRequest,
    TransactionMatchResponse,
    CompleteCycleDashboard,
    BankingMetrics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/banking", tags=["Banking"])


def _banking_user_id(current_user: User) -> str:
    return str(current_user.id)


# ============================================================================
# BANK ACCOUNT ENDPOINTS
# ============================================================================


@router.post("/accounts/connect", response_model=BankAccountResponse)
def connect_bank_account(
    request: BankAccountConnect,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Connect new bank account via Open Banking API."""
    user_id = _banking_user_id(current_user)
    try:
        valid_banks = [b.value for b in BankType]
        if request.bank_type not in valid_banks:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid bank type. Supported: {', '.join(valid_banks)}",
            )

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
        db.commit()
        db.refresh(account)

        logger.info("Connected %s account for user %s", request.bank_type, user_id)
        return BankAccountResponse.model_validate(account)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise server_error(logger, e) from e


@router.get("/accounts", response_model=list[BankAccountResponse])
def list_bank_accounts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all connected bank accounts."""
    user_id = _banking_user_id(current_user)
    try:
        stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        accounts = db.execute(stmt).scalars().all()
        return [BankAccountResponse.model_validate(acc) for acc in accounts]
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
def get_bank_account(
    account_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get specific bank account details."""
    user_id = _banking_user_id(current_user)
    try:
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id,
        )
        account = db.execute(stmt).scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        return BankAccountResponse.model_validate(account)
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.post("/accounts/{account_id}/sync", response_model=BankAccountSyncResponse)
def sync_bank_transactions(
    account_id: str = Path(...),
    body: BankAccountSyncRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Sync transactions from bank account."""
    user_id = _banking_user_id(current_user)
    req = body if body is not None else BankAccountSyncRequest()
    try:
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id,
        )
        account = db.execute(stmt).scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        previous_last_sync = account.last_sync
        account.sync_status = "syncing"
        account.last_sync = datetime.utcnow()

        synced_txns = 0
        new_deposits = 0
        new_withdrawals = 0

        if req.force_full_sync or (
            previous_last_sync is None
            or (datetime.utcnow() - previous_last_sync).days >= 1
        ):
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
        db.commit()
        db.refresh(account)

        logger.info("Synced %s transactions for account %s", synced_txns, account_id)
        return BankAccountSyncResponse(
            account_id=account.id,
            transactions_synced=synced_txns,
            new_deposits=new_deposits,
            new_withdrawals=new_withdrawals,
            last_sync=account.last_sync or datetime.utcnow(),
            status="success" if synced_txns > 0 else "no_new_transactions",
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise server_error(logger, e) from e


@router.delete("/accounts/{account_id}")
def disconnect_bank_account(
    account_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Disconnect bank account."""
    user_id = _banking_user_id(current_user)
    try:
        stmt = select(BankAccount).where(
            BankAccount.id == account_id,
            BankAccount.user_id == user_id,
        )
        account = db.execute(stmt).scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        db.delete(account)
        db.commit()
        return {"status": "disconnected", "account_id": account_id}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise server_error(logger, e) from e


# ============================================================================
# BANK TRANSACTION ENDPOINTS
# ============================================================================


@router.get("/transactions", response_model=list[BankTransactionResponse])
def list_bank_transactions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    account_id: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    min_amount: Optional[Decimal] = Query(None),
    max_amount: Optional[Decimal] = Query(None),
    days: int = Query(30),
):
    """List bank transactions with filtering."""
    user_id = _banking_user_id(current_user)
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        accounts = db.execute(stmt).scalars().all()
        account_ids = [a.id for a in accounts]
        if not account_ids:
            return []

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

        stmt_tx = (
            select(BankTransaction).where(and_(*filters)).order_by(BankTransaction.date.desc())
        )
        transactions = db.execute(stmt_tx).scalars().all()
        return [BankTransactionResponse.model_validate(t) for t in transactions]
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


# ============================================================================
# TRANSACTION MATCHING ENDPOINTS
# ============================================================================


@router.post("/match", response_model=TransactionMatchResponse)
def create_transaction_match(
    request: TransactionMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually match crypto withdrawal to bank deposit."""
    try:
        crypto_date = datetime.utcnow()
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
            confidence=1.0,
            match_status="matched",
            notes=request.notes or "",
        )

        db.add(match)
        db.commit()
        db.refresh(match)
        logger.info("Created match %s", match.id)
        return TransactionMatchResponse.model_validate(match)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise server_error(logger, e) from e


@router.post("/match-auto", response_model=TransactionMatchAutoResponse)
def auto_match_transactions(
    request: TransactionMatchAutoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Automatically match crypto withdrawals to bank deposits."""
    user_id = _banking_user_id(current_user)
    try:
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        accounts = db.execute(account_stmt).scalars().all()
        account_ids = [a.id for a in accounts]

        txn_stmt = select(BankTransaction).where(
            BankTransaction.account_id.in_(account_ids),
            BankTransaction.type == "deposit",
        )
        deposits = db.execute(txn_stmt).scalars().all()

        withdrawal_stmt = select(CryptoWithdrawal).where(CryptoWithdrawal.user_id == user_id)
        withdrawals = db.execute(withdrawal_stmt).scalars().all()

        matches: list[TransactionMatch] = []
        high_confidence = 0
        medium_confidence = 0

        for withdrawal in withdrawals:
            for deposit in deposits:
                if withdrawal.amount_in_usd and withdrawal.amount_in_usd > 0:
                    amount_diff_pct = abs(
                        float((withdrawal.amount_in_usd - deposit.amount) / withdrawal.amount_in_usd)
                    ) * 100
                else:
                    continue

                if amount_diff_pct > request.tolerance_percent:
                    continue

                time_diff = abs((deposit.date - withdrawal.date_time).total_seconds() / 3600)
                if time_diff > request.time_window_hours:
                    continue

                confidence = 1.0 - (amount_diff_pct / 100)
                match = TransactionMatch(
                    id=str(uuid.uuid4()),
                    crypto_withdrawal_id=withdrawal.id,
                    bank_deposit_id=deposit.id,
                    crypto_amount=withdrawal.amount,
                    crypto_currency=withdrawal.asset,
                    fiat_amount=deposit.amount,
                    fiat_currency=deposit.currency,
                    exchange_rate=Decimal(str(withdrawal.amount_in_usd / withdrawal.amount))
                    if withdrawal.amount and withdrawal.amount != 0
                    else Decimal(0),
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

        db.commit()
        for m in matches:
            db.refresh(m)

        return TransactionMatchAutoResponse(
            matches_found=len(matches),
            high_confidence_matches=high_confidence,
            medium_confidence_matches=medium_confidence,
            matches=[TransactionMatchResponse.model_validate(m) for m in matches],
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise server_error(logger, e) from e


@router.get("/matches", response_model=list[TransactionMatchResponse])
def list_transaction_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    min_confidence: float = Query(0.0),
):
    """List transaction matches for the current user's bank data only."""
    user_id = _banking_user_id(current_user)
    try:
        stmt = (
            select(TransactionMatch)
            .join(BankTransaction, TransactionMatch.bank_deposit_id == BankTransaction.id)
            .join(BankAccount, BankTransaction.account_id == BankAccount.id)
            .where(
                BankAccount.user_id == user_id,
                TransactionMatch.confidence >= min_confidence,
            )
            .order_by(TransactionMatch.created_at.desc())
        )
        matches = db.execute(stmt).scalars().all()
        return [TransactionMatchResponse.model_validate(m) for m in matches]
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.get("/cycle-dashboard", response_model=CompleteCycleDashboard)
def get_cycle_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Complete crypto to fiat cycle dashboard."""
    user_id = _banking_user_id(current_user)
    try:
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        accounts = db.execute(account_stmt).scalars().all()

        withdrawal_stmt = select(CryptoWithdrawal).where(CryptoWithdrawal.user_id == user_id)
        withdrawals = db.execute(withdrawal_stmt).scalars().all()

        match_stmt = (
            select(TransactionMatch)
            .join(BankTransaction, TransactionMatch.bank_deposit_id == BankTransaction.id)
            .join(BankAccount, BankTransaction.account_id == BankAccount.id)
            .where(BankAccount.user_id == user_id)
        )
        matches = db.execute(match_stmt).scalars().all()

        total_withdrawn = sum(w.amount_in_usd for w in withdrawals if w.amount_in_usd)
        total_deposited = sum(m.fiat_amount for m in matches)
        total_fees = sum(m.fees_paid for m in matches)

        return CompleteCycleDashboard(
            user_id=user_id,
            total_positions=len(accounts),
            total_withdrawn_crypto=Decimal(str(total_withdrawn)),
            total_deposited_fiat=Decimal(str(total_deposited)),
            total_fees=Decimal(str(total_fees)),
            matched_cycles=len(matches),
            pending_matches=max(0, len(withdrawals) - len(matches)),
            tax_ready=len(matches) > 0
            and len([m for m in matches if m.confidence > 0.95]) == len(matches),
            stages=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.get("/metrics", response_model=BankingMetrics)
def get_banking_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Banking integration metrics (scoped to current user)."""
    user_id = _banking_user_id(current_user)
    try:
        account_stmt = select(BankAccount).where(BankAccount.user_id == user_id)
        accounts = db.execute(account_stmt).scalars().all()
        account_ids = [a.id for a in accounts]

        if not account_ids:
            return BankingMetrics(
                connected_banks=0,
                synced_accounts=0,
                total_transactions=0,
                unmatched_transactions=0,
                matched_deposits=0,
                average_match_confidence=0,
                total_volume=Decimal(0),
            )

        txn_stmt = select(BankTransaction).where(BankTransaction.account_id.in_(account_ids))
        transactions = db.execute(txn_stmt).scalars().all()

        match_stmt = (
            select(TransactionMatch)
            .join(BankTransaction, TransactionMatch.bank_deposit_id == BankTransaction.id)
            .join(BankAccount, BankTransaction.account_id == BankAccount.id)
            .where(BankAccount.user_id == user_id)
        )
        matches = db.execute(match_stmt).scalars().all()

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
    except HTTPException:
        raise
    except Exception as e:
        raise server_error(logger, e) from e


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "banking",
        "version": "1.0.0",
        "timestamp": datetime.utcnow(),
    }
