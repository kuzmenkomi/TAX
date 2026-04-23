"""
Smart Reconciliation Engine
Intelligently matches transactions with unknown cost basis
"""

from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.advanced_tax.services.base_service import BaseService
from app.advanced_tax.models.reconciliation_models import (
    MissingCostBasis,
    ReconciliationMatch,
    ReconciliationHistory,
)
from app.advanced_tax.utils import ReconciliationStatus, ServiceException

logger = logging.getLogger(__name__)


class SmartReconciliationEngine(BaseService):
    """
    Intelligently detects and resolves missing cost basis in transactions.
    
    Uses multiple matching strategies:
    - Same-address transfers
    - Exchange deposit matching
    - Timestamp-based pairing
    - User manual entry
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.confidence_threshold = 0.85
    
    def validate_inputs(self, **kwargs) -> bool:
        """Validate input parameters"""
        if 'transaction_id' in kwargs:
            txn_id = kwargs['transaction_id']
            if not isinstance(txn_id, int) or txn_id <= 0:
                raise ServiceException(f"Invalid transaction_id: {txn_id}")
        return True
    
    def scan_for_gaps(self) -> List[Dict[str, Any]]:
        """
        Scan all transactions and find ones with missing cost basis.
        Returns prioritized list of gaps to fill.
        """
        try:
            self.log_event("GAP_SCAN_STARTED", {"user_id": self.user_id})
            
            # TODO: Query transactions from backend
            # Get all receive/transfer_in transactions
            
            gaps = []
            
            # Filter for gaps
            # For each gap, calculate impact and add to list
            
            # Sort by impact (most important first)
            gaps.sort(key=lambda g: g['severity_score'], reverse=True)
            
            # Save to database
            for gap_data in gaps:
                gap = MissingCostBasis(
                    user_id=self.user_id,
                    transaction_id=gap_data.get('transaction_id'),
                    asset=gap_data['asset'],
                    quantity=gap_data['quantity'],
                    transaction_date=gap_data['date'],
                    transaction_type=gap_data['type'],
                    error_description=gap_data['description'],
                    current_estimated_value=gap_data['estimated_value'],
                    potential_tax_impact=gap_data['tax_impact'],
                    severity_score=gap_data['severity_score'],
                    status=ReconciliationStatus.PENDING,
                )
                self.db.add(gap)
            
            self.db.commit()
            
            self.log_event("GAP_SCAN_COMPLETE", {
                "gaps_found": len(gaps),
                "total_tax_impact": sum(g['tax_impact'] for g in gaps),
            })
            
            return gaps
        
        except Exception as e:
            self.db.rollback()
            self.log_error("GAP_SCAN_ERROR", str(e))
            raise ServiceException(f"Gap scan failed: {str(e)}")
    
    def find_matching_transactions(
        self,
        transaction_id: int,
        search_depth_hours: int = 72
    ) -> List[Dict[str, Any]]:
        """
        Find potential source transactions for a receive with missing cost basis.
        
        Search strategies:
        1. Same-address transfers (blockchain)
        2. Exchange deposits
        3. Import records with matching timestamp
        
        Returns:
            List of suggestions ranked by confidence score
        """
        try:
            self.log_event("MATCHING_STARTED", {
                "transaction_id": transaction_id,
                "search_depth_hours": search_depth_hours
            })
            
            suggestions = []
            
            # Strategy 1: Direct address matching
            # TODO: Query blockchain for transfers to this address
            
            # Strategy 2: Exchange deposits
            # TODO: Query exchanges for deposits matching asset/qty/date
            
            # Strategy 3: Import records
            # TODO: Query import records for timestamp matches
            
            # Sort by confidence
            suggestions.sort(key=lambda s: s['confidence'], reverse=True)
            
            self.log_event("MATCHING_SUGGESTIONS_FOUND", {
                "transaction_id": transaction_id,
                "suggestions_count": len(suggestions),
            })
            
            return suggestions
        
        except Exception as e:
            self.log_error("MATCHING_ERROR", str(e))
            raise ServiceException(f"Matching failed: {str(e)}")
    
    def accept_match(
        self,
        receive_txn_id: int,
        send_txn_id: int,
        reason: str = "user_accepted"
    ) -> Dict[str, Any]:
        """
        User accepts a suggested match - link them permanently.
        """
        try:
            # Create match record
            match = ReconciliationMatch(
                user_id=self.user_id,
                send_transaction_id=send_txn_id,
                receive_transaction_id=receive_txn_id,
                matching_score=0.99,  # User confirmed
                matched_by='user',
                matching_reason=reason,
                confirmed_by_user=True,
                confirmed_at=datetime.utcnow(),
            )
            
            self.db.add(match)
            
            # Update the gap record
            gap = self.db.query(MissingCostBasis).filter(
                MissingCostBasis.transaction_id == receive_txn_id,
                MissingCostBasis.user_id == self.user_id,
            ).first()
            
            if gap:
                gap.status = ReconciliationStatus.MATCHED
                gap.matched_transaction_id = send_txn_id
                # TODO: Calculate cost basis from send transaction
            
            # Create history record
            history = ReconciliationHistory(
                user_id=self.user_id,
                action_type='match',
                transaction_id=receive_txn_id,
                old_value='{"status": "pending", "cost_basis": null}',
                new_value=f'{{"status": "matched", "matched_to": {send_txn_id}}}',
                reason=reason,
            )
            
            self.db.add(history)
            self.db.commit()
            
            self.log_event("MATCH_ACCEPTED", {
                "send_txn_id": send_txn_id,
                "receive_txn_id": receive_txn_id,
            })
            
            return {
                'status': 'success',
                'message': 'Transactions linked successfully',
                'cost_basis': gap.cost_basis if gap else None,
            }
        
        except Exception as e:
            self.db.rollback()
            self.log_error("MATCH_ACCEPTANCE_FAILED", str(e))
            raise ServiceException(f"Match acceptance failed: {str(e)}")
    
    def manual_entry(
        self,
        transaction_id: int,
        cost_basis: Decimal,
        source: str = "user_entry",
        notes: str = ""
    ) -> Dict[str, Any]:
        """User manually sets cost basis for transaction"""
        try:
            # Get or create gap record
            gap = self.db.query(MissingCostBasis).filter(
                MissingCostBasis.transaction_id == transaction_id,
                MissingCostBasis.user_id == self.user_id,
            ).first()
            
            if gap:
                old_value = f'{{"cost_basis": {gap.cost_basis}, "status": "{gap.status}"}}'
                gap.cost_basis = cost_basis
                gap.status = ReconciliationStatus.MANUAL_ENTRY
                gap.cost_basis_source = source
            else:
                # Create new gap (rare case)
                gap = MissingCostBasis(
                    user_id=self.user_id,
                    transaction_id=transaction_id,
                    asset="UNKNOWN",  # TODO: Get from transaction
                    quantity=0,
                    transaction_date=datetime.utcnow(),
                    transaction_type="UNKNOWN",
                    error_description="Manual entry",
                    current_estimated_value=Decimal(0),
                    potential_tax_impact=Decimal(0),
                    severity_score=0,
                    cost_basis=cost_basis,
                    status=ReconciliationStatus.MANUAL_ENTRY,
                    cost_basis_source=source,
                )
                old_value = '{"cost_basis": null}'
                self.db.add(gap)
            
            # Create history record
            history = ReconciliationHistory(
                user_id=self.user_id,
                action_type='manual_entry',
                transaction_id=transaction_id,
                old_value=old_value,
                new_value=f'{{"cost_basis": {cost_basis}, "status": "manual_entry"}}',
                reason=source,
                user_notes=notes,
            )
            
            self.db.add(history)
            self.db.commit()
            
            self.log_event("MANUAL_ENTRY_SAVED", {
                "transaction_id": transaction_id,
                "cost_basis": float(cost_basis),
            })
            
            return {
                'status': 'success',
                'message': 'Cost basis set manually',
                'cost_basis': float(cost_basis),
            }
        
        except Exception as e:
            self.db.rollback()
            self.log_error("MANUAL_ENTRY_FAILED", str(e))
            raise ServiceException(f"Manual entry failed: {str(e)}")
    
    def get_reconciliation_summary(self) -> Dict[str, Any]:
        """Get summary of all reconciliation gaps"""
        gaps = self.db.query(MissingCostBasis).filter(
            MissingCostBasis.user_id == self.user_id,
        ).all()
        
        pending = [g for g in gaps if g.status == ReconciliationStatus.PENDING]
        matched = [g for g in gaps if g.status == ReconciliationStatus.MATCHED]
        manual = [g for g in gaps if g.status == ReconciliationStatus.MANUAL_ENTRY]
        
        total_impact = sum(g.potential_tax_impact for g in gaps)
        
        return {
            'total_gaps': len(gaps),
            'pending_count': len(pending),
            'matched_count': len(matched),
            'manual_count': len(manual),
            'total_tax_impact': float(total_impact),
            'pending_gaps': [g.to_dict() for g in pending[:10]],  # Top 10
        }
