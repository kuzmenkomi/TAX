from decimal import Decimal
from datetime import datetime
from typing import List, Dict, Any
import logging
from uuid import uuid4

from sqlalchemy.orm import Session
from app.models import Transaction, TLHOpportunity, RecommendationStatus
from app.advanced_tax.services.tlh_engine import TLHEngine
from app.advanced_tax.services.tlh_scorer import TLHScorer
from app.advanced_tax.services.tlh_executor import TLHExecutor
from app.services.financial_data_service import FinancialDataService

logger = logging.getLogger(__name__)

class TLHBridgeService:
    """
    Bridge service to connect application transactions with advanced TLH logic.
    Converts DB transactions into TLH positions and orchestrates the scanning process.
    """
    
    @classmethod
    def run_scan(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Runs a complete TLH scan for the user:
        1. Fetches transactions
        2. Calculates current positions
        3. Scans for harvestable losses
        4. Persists opportunities
        """
        # 1. Fetch transactions
        transactions = db.query(Transaction).filter(Transaction.user_id == user_id).all()
        if not transactions:
            return {
                "opportunities_found": 0,
                "total_harvestable_losses": Decimal("0"),
                "total_tax_benefit": Decimal("0"),
            }

        # 2. Calculate current positions (simplistic approach for the bridge)
        # In a full implementation, we'd use CostBasisCalculator more extensively
        positions_map = {}
        for tx in transactions:
            asset = tx.asset
            if asset not in positions_map:
                positions_map[asset] = {"quantity": Decimal("0"), "total_cost": Decimal("0"), "count": 0}
            
            if tx.tx_type.lower() in ["buy", "purchase", "deposit", "in"]:
                positions_map[asset]["quantity"] += tx.amount
                positions_map[asset]["total_cost"] += (tx.amount * (tx.price or Decimal("0")))
                positions_map[asset]["count"] += 1
            elif tx.tx_type.lower() in ["sell", "withdrawal", "out"]:
                positions_map[asset]["quantity"] -= tx.amount
                # Basic cost basis reduction (simplified)
                if positions_map[asset]["quantity"] > 0:
                    avg_cost_before = positions_map[asset]["total_cost"] / (positions_map[asset]["quantity"] + tx.amount)
                    positions_map[asset]["total_cost"] -= (tx.amount * avg_cost_before)

        # 3. Enrich positions with current market data
        final_positions = []
        for asset, data in positions_map.items():
            if data["quantity"] <= 0.00000001:
                continue
                
            current_price = FinancialDataService.get_crypto_price(asset)
            avg_cost = data["total_cost"] / data["quantity"] if data["quantity"] > 0 else Decimal("0")
            
            final_positions.append({
                "id": f"pos_{asset}_{user_id}",
                "asset": asset,
                "quantity": data["quantity"],
                "average_cost": avg_cost,
                "current_price": current_price,
                "purchase_date": datetime.now(), # Placeholder for scoring
            })

        # 4. Initialize Engine and Scan
        engine = TLHEngine(
            scorer=TLHScorer(),
            executor=TLHExecutor(),
            db_service=db
        )
        
        recommendations = engine.scan_portfolio(final_positions)
        
        # 5. Persist to DB
        # First, clear old "New" opportunities for this user to avoid duplicates
        db.query(TLHOpportunity).filter(
            TLHOpportunity.user_id == str(user_id),
            TLHOpportunity.status == RecommendationStatus.NEW.value
        ).delete()
        
        total_loss = Decimal("0")
        for rec in recommendations:
            opp = TLHOpportunity(
                id=str(uuid4()),
                user_id=str(user_id),
                position_id=rec.position_id,
                asset=rec.asset,
                loss_amount=rec.loss_amount,
                tax_rate=rec.tax_rate,
                priority_score=rec.priority_score,
                priority_breakdown=rec.priority_breakdown,
                explanation=rec.explanation,
                status=RecommendationStatus.NEW.value,
                wash_sale_risk=rec.wash_sale_risk,
                wash_sale_days_remaining=rec.wash_sale_days_remaining
            )
            db.add(opp)
            total_loss += rec.loss_amount
            
        db.commit()
        
        return {
            "opportunities_found": len(recommendations),
            "total_harvestable_losses": total_loss,
            "total_tax_benefit": total_loss * Decimal("0.24")
        }
