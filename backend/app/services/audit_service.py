"""
Audit and Explainability Service
Provides detailed breakdown of tax calculations (Trust Layer)
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.accounting import LotMatch
from app.models.transaction import Transaction

class AuditService:
    @staticmethod
    def get_audit_trail(db: Session, user_id: str, year: int) -> List[Dict[str, Any]]:
        """
        Generate a detailed audit trail showing exactly which Buy lots 
        were matched with which Sell transactions.
        """
        matches = db.query(LotMatch).filter(
            LotMatch.user_id == user_id
        ).all()
        
        trail = []
        for match in matches:
            # Filter by year if needed (based on sell transaction date)
            sell_tx = match.sell_transaction
            if sell_tx.timestamp.year != year:
                continue
                
            buy_tx = match.buy_transaction
            
            trail.append({
                "asset": sell_tx.asset,
                "quantity": float(match.quantity),
                "sell": {
                    "date": sell_tx.timestamp.isoformat(),
                    "price": float(sell_tx.price),
                    "total": float(sell_tx.price * match.quantity),
                    "tx_hash": sell_tx.tx_hash
                },
                "buy": {
                    "date": buy_tx.timestamp.isoformat(),
                    "price": float(buy_tx.price),
                    "total": float(buy_tx.price * match.quantity),
                    "tx_hash": buy_tx.tx_hash
                },
                "gain_loss": float(match.realized_pnl),
                "holding_period": (sell_tx.timestamp - buy_tx.timestamp).days
            })
            
        return trail

    @staticmethod
    def format_audit_trail_csv(trail: List[Dict[str, Any]]) -> str:
        """Format audit trail as CSV for expert review"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Asset", "Quantity", 
            "Buy Date", "Buy Price", "Buy Total",
            "Sell Date", "Sell Price", "Sell Total",
            "Gain/Loss", "Holding Period (Days)"
        ])
        
        for entry in trail:
            writer.writerow([
                entry["asset"],
                entry["quantity"],
                entry["buy"]["date"],
                entry["buy"]["price"],
                entry["buy"]["total"],
                entry["sell"]["date"],
                entry["sell"]["price"],
                entry["sell"]["total"],
                entry["gain_loss"],
                entry["holding_period"]
            ])
            
        return output.getvalue()
