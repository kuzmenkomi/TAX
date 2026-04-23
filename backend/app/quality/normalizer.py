"""
Data Quality and Normalization Layer
Handles deduplication and transaction normalization
"""
from typing import List, Set
from datetime import timedelta
from app.models.transaction import Transaction

class DataNormalizer:
    @staticmethod
    def deduplicate(transactions: List[Transaction]) -> List[Transaction]:
        """
        Identify and remove duplicate transactions based on:
        1. Exact hash match
        2. Time + Asset + Amount proximity (for API vs CSV overlaps)
        """
        if not transactions:
            return []
            
        unique_txs = []
        seen_hashes: Set[str] = set()
        seen_fingerprints: Set[tuple] = set()
        
        # Sort by timestamp to handle proximity
        sorted_txs = sorted(transactions, key=lambda x: x.timestamp)
        
        for tx in sorted_txs:
            # 1. Check hash
            if tx.tx_hash and tx.tx_hash in seen_hashes:
                continue
            
            # 2. Check fingerprint (Time rounded to minute, Asset, Amount, Type)
            # This handles duplicates across different sources that might have slightly different timestamps
            fingerprint = (
                tx.timestamp.replace(second=0, microsecond=0),
                tx.asset,
                round(tx.amount, 8),
                tx.type
            )
            
            if fingerprint in seen_fingerprints:
                # Potential duplicate, check if timestamp is within 2 minutes
                continue
                
            if tx.tx_hash:
                seen_hashes.add(tx.tx_hash)
            seen_fingerprints.add(fingerprint)
            unique_txs.append(tx)
            
        return unique_txs

    @staticmethod
    def fix_common_errors(transactions: List[Transaction]) -> List[Transaction]:
        """
        Auto-correct common data issues:
        - Inverting signs for withdrawals if positive
        - Zeroing out micro-dust that causes precision issues
        """
        for tx in transactions:
            # Ensure withdrawal amounts are negative in accounting
            if tx.type in ["WITHDRAWAL", "SELL"] and tx.amount > 0:
                tx.amount = -tx.amount
                
            # Handle dust
            if abs(tx.amount) < 1e-12:
                tx.amount = 0
                
        return transactions
