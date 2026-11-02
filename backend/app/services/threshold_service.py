from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models import Transaction, Portfolio, ExchangeConnection
from app.services.financial_data_service import FinancialDataService

class ThresholdService:
    """
    Service to track tax-free thresholds and provide smart advice.
    Focus: Brazil 35,000 BRL exemption and similar global rules.
    """
    
    # Mapping of domestic exchanges for Brazil
    BRAZIL_DOMESTIC_EXCHANGES = ["mercadobitcoin", "foxbit", "novadax", "bitso", "ripio"]

    @staticmethod
    def get_monthly_status(db: Session, user_id: int, jurisdiction_code: str = "BR"):
        if jurisdiction_code.upper() != "BR":
            return {"supported": False, "message": "Threshold tracking not yet implemented for this jurisdiction"}

        # 1. Get current month range
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        # 2. Get user's base currency (usually BRL for Brazil)
        # For simplicity, assuming BRL. In production, fetch from Portfolio.
        base_currency = "BRL"
        threshold_limit = Decimal("35000.00")

        # 3. Fetch all Sell/Trade transactions for the current month
        # We need to filter by domestic exchanges for the 35k rule
        stmt = select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.timestamp >= start_of_month,
            Transaction.tx_type.in_(["sell", "trade"])
        )
        result = db.execute(stmt)
        transactions = result.scalars().all()

        domestic_sales = Decimal("0.0")
        offshore_sales = Decimal("0.0")

        for tx in transactions:
            # Determine if exchange is domestic
            is_domestic = any(ex in (tx.from_wallet or "").lower() for ex in ThresholdService.BRAZIL_DOMESTIC_EXCHANGES)
            
            # Convert value to BRL if it's in USD or other
            val_brl = tx.total_value
            if tx.asset != "BRL": # If total_value is not in BRL, we'd need conversion
                # Simplified: assuming total_value is stored in base currency or USD
                # In real app, use FinancialDataService.get_exchange_rate("USD", "BRL")
                pass

            if is_domestic:
                domestic_sales += val_brl
            else:
                offshore_sales += val_brl

        remaining = max(Decimal("0"), threshold_limit - domestic_sales)
        percent = (domestic_sales / threshold_limit * 100) if threshold_limit > 0 else 0

        # 4. Generate Smart Advice
        advice = ""
        days_in_month = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).day if now.month < 12 else 31
        days_left = days_in_month - now.day

        if domestic_sales >= threshold_limit:
            advice = "⚠️ Limite de 35k atingido! Todas as vendas deste mês serão tributadas em 15%."
        elif percent > 80:
            advice = f"🚨 Atenção! Você usou {percent:.1f}% do seu limite. Faltam apenas {remaining:.2f} BRL para começar a pagar imposto."
        elif days_left <= 5 and domestic_sales < threshold_limit:
            advice = f"💡 Dica: Faltam {days_left} dias para o fim do mês. Se possível, aguarde o dia 1º para realizar novas vendas e aproveitar o limite do próximo mês."
        else:
            advice = f"✅ Você ainda tem {remaining:.2f} BRL de limite isento para este mês em exchanges nacionais."

        return {
            "jurisdiction": "BR",
            "limit": float(threshold_limit),
            "current_domestic": float(domestic_sales),
            "current_offshore": float(offshore_sales),
            "remaining": float(remaining),
            "percent": float(percent),
            "advice": advice,
            "days_left": days_left
        }
