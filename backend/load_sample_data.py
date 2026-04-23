"""
Load sample transaction data for Phase 10 testing
"""

import csv
from datetime import datetime
from decimal import Decimal

from app.db import SessionLocal
from app.models import User, Portfolio, AnalysisRun, Transaction


def load_sample_transactions(user_id: int = 1, run_id: int = 1):
    """Load sample transactions from CSV for testing."""
    db = SessionLocal()
    try:
        # Check if user exists, create test user if not
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            user = User(
                id=user_id,
                email=f"test_user_{user_id}@example.com",
                hashed_password="dummy",
                created_at=datetime.now(),
                is_active=True
            )
            db.add(user)
            db.flush()
        
        # Check if portfolio exists
        portfolio = db.query(Portfolio).filter(Portfolio.user_id == user_id).first()
        if not portfolio:
            portfolio = Portfolio(
                user_id=user_id,
                country_code="BR",
                name="Principal",
                is_onboarded=True,
                created_at=datetime.now()
            )
            db.add(portfolio)
            db.flush()
        
        # Check if analysis run exists
        run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
        if not run:
            run = AnalysisRun(
                user_id=user_id,
                csv_rel_path="data/sample.csv",
                created_at=datetime.now()
            )
            db.add(run)
            db.flush()
        
        # Load transactions from sample.csv
        sample_path = "data/sample.csv"
        count = 0
        
        with open(sample_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if transaction already exists
                if db.query(Transaction).filter(
                    Transaction.external_id == row['external_id']
                ).first():
                    continue
                
                tx = Transaction(
                    user_id=user_id,
                    run_id=run_id,
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    asset=row['asset'],
                    tx_type=row['type'],
                    amount=Decimal(row['amount']),
                    fee=Decimal(row['fee']),
                    price=Decimal(row['price']) if row['price'] else None,
                    total_value=Decimal(row['total_value']),
                    from_wallet=row['from_wallet'] if row['from_wallet'] else None,
                    to_wallet=row['to_wallet'] if row['to_wallet'] else None,
                    external_id=row['external_id']
                )
                db.add(tx)
                count += 1
        
        db.commit()
        print(f"✅ Loaded {count} transactions")
        print(f"✅ User ID: {user_id}, Analysis Run ID: {run_id}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error loading sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_transactions()
