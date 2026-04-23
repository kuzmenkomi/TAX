"""
CLI script to calculate taxes for a user
Usage: python -m app.cli.calculate_taxes --user-id=UUID --jurisdiction=MX --year=2024
"""
import sys
import argparse
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.integrations.tax_jurisdictions import get_jurisdiction, CapitalGain


def calculate_user_taxes(db: Session, user_id: str, jurisdiction_code: str, year: int):
    """
    Calculate taxes for user's transactions in a jurisdiction for a specific year
    
    Args:
        db: Database session
        user_id: User UUID
        jurisdiction_code: Jurisdiction code (MX, BR, AR, etc.)
        year: Tax year
    """
    # Get user
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        print(f"❌ User {user_id} not found")
        return
    
    # Get jurisdiction
    try:
        jurisdiction = get_jurisdiction(jurisdiction_code)
    except ValueError as e:
        print(f"❌ {e}")
        return
    
    print(f"\n📊 Calculating taxes for {user.email} ({jurisdiction.name})")
    print(f"   Year: {year}")
    print(f"   Currency: {jurisdiction.currency}")
    print("-" * 60)
    
    # Get transactions for user in that year
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).all()
    
    if not transactions:
        print(f"❌ No transactions found for {year}")
        return
    
    print(f"✓ Found {len(transactions)} transactions")
    
    # Group transactions
    capital_gains = []
    total_income = Decimal("0")
    total_fees = Decimal("0")
    
    for txn in transactions:
        if txn.type == "sell" and txn.price_sold and txn.price_bought:
            # Create capital gain
            gain = CapitalGain(
                buy_date=txn.date,  # Simplified - in reality need matching
                sell_date=txn.date_sold or datetime.utcnow(),
                buy_price=Decimal(str(txn.price_bought)),
                sell_price=Decimal(str(txn.price_sold)),
                quantity=Decimal(str(txn.quantity)),
                fee=Decimal(str(txn.fee if txn.fee else 0))
            )
            capital_gains.append(gain)
        
        elif txn.type in ["income", "staking", "mining", "airdrop"]:
            total_income += Decimal(str(txn.cost_basis if txn.cost_basis else 0))
        
        if txn.fee:
            total_fees += Decimal(str(txn.fee))
    
    # Calculate taxes
    results = []
    
    if capital_gains:
        print(f"\n💰 Capital Gains: {len(capital_gains)} transactions")
        cg_result = jurisdiction.calculate_capital_gains_tax(capital_gains)
        results.append(cg_result)
        print(f"   Amount: {cg_result.amount} {jurisdiction.currency}")
        print(f"   Tax: {cg_result.calculated_tax} {jurisdiction.currency}")
        print(f"   Rate: {cg_result.tax_rate}%")
    
    if total_income > 0:
        print(f"\n📈 Ordinary Income: {total_income} {jurisdiction.currency}")
        income_result = jurisdiction.calculate_ordinary_income_tax(total_income)
        results.append(income_result)
        print(f"   Tax: {income_result.calculated_tax} {jurisdiction.currency}")
        print(f"   Rate: {income_result.tax_rate}%")
    
    # Summary
    total_tax = sum(r.calculated_tax for r in results)
    print("\n" + "=" * 60)
    print(f"📋 TOTAL TAX LIABILITY: {total_tax} {jurisdiction.currency}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Calculate taxes for a user")
    parser.add_argument("--user-id", required=True, help="User UUID")
    parser.add_argument("--jurisdiction", required=True, help="Jurisdiction code (MX, BR, AR, CO, PE, CL)")
    parser.add_argument("--year", type=int, default=datetime.now().year, help="Tax year (default: current year)")
    
    args = parser.parse_args()
    
    db = SessionLocal()
    try:
        calculate_user_taxes(db, args.user_id, args.jurisdiction, args.year)
    except Exception as e:
        print(f"❌ Error calculating taxes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
