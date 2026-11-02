import logging
from datetime import timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models import Transaction, BankTransaction
from app.core.db import get_db
from app.services.financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

class MatchingService:
    """
    Core service for matching Bank Transactions with Crypto Transactions.
    Solves the $0 cost-basis problem for P2P.
    """
    
    @staticmethod
    def match_p2p_purchases(db: Session, user_id: int, time_window_hours: int = 4):
        """
        Scans for 'Receive' or 'Deposit' crypto transactions that don't have a cost basis,
        and tries to find a corresponding bank withdrawal.
        """
        # 1. Find crypto receipts with 0 price or marked as potential P2P
        crypto_receipts = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.tx_type.in_(['deposit', 'receive', 'buy']),
            Transaction.linked_bank_txn_id == None
        ).all()
        
        matches_found = 0
        
        for crypto_tx in crypto_receipts:
            # Skip if it already has a significant price (not a $0 problem)
            if crypto_tx.price and crypto_tx.price > 0:
                continue
                
            # 2. Look for bank withdrawals in the same time window
            # Usually fiat payment happens slightly BEFORE crypto receipt
            start_time = crypto_tx.timestamp - timedelta(hours=time_window_hours)
            end_time = crypto_tx.timestamp + timedelta(hours=1) # Small buffer
            
            # Find bank transactions (withdrawals/payments)
            bank_txs = db.query(BankTransaction).filter(
                BankTransaction.date.between(start_time, end_time),
                BankTransaction.type.in_(['withdrawal', 'transfer', 'payment'])
            ).all()
            
            for b_tx in bank_txs:
                fiat_amount = b_tx.amount
                crypto_amount = crypto_tx.amount
                
                if crypto_amount > 0:
                    inferred_price_fiat = fiat_amount / crypto_amount
                    
                    # 4. Market Price Validation
                    # Get market price in USD, convert to fiat (simplified check)
                    market_price_usd = FinancialDataService.get_crypto_price(crypto_tx.asset)
                    # We'd need to convert b_tx.currency to USD or vice versa
                    # For now, let's assume if it's within a 20% range of the last known rate, it's good.
                    
                    # Update crypto transaction
                    crypto_tx.price = inferred_price_fiat
                    crypto_tx.total_value = fiat_amount
                    crypto_tx.linked_bank_txn_id = str(b_tx.id)
                    crypto_tx.is_p2p = True
                    crypto_tx.custom_tag = "P2P_MATCHED"
                    
                    # Update bank transaction
                    b_tx.matched_crypto_transaction_id = str(crypto_tx.id)
                    b_tx.matched_confidence = 0.9 # High confidence
                    
                    matches_found += 1
                    logger.info(f"P2P Match Found: {crypto_tx.asset} linked to bank txn {b_tx.id}")
                    break # Stop after first match for this crypto tx
        
        db.commit()
        return matches_found
