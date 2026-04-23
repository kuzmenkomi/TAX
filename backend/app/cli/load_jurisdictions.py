"""
CLI script to load jurisdiction data into database
Usage: python -m app.cli.load_jurisdictions
"""
import sys
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.jurisdiction import Jurisdiction, TaxRule
from app.integrations.tax_jurisdictions import get_all_jurisdictions


def load_jurisdictions_data(db: Session):
    """Load all tax jurisdiction data into database"""
    
    jurisdictions = get_all_jurisdictions()
    
    for code, jurisdiction in jurisdictions.items():
        info = jurisdiction.get_jurisdiction_info()
        
        # Check if already exists
        existing = db.query(Jurisdiction).filter_by(code=code).first()
        if existing:
            print(f"Jurisdiction {code} already exists, skipping")
            continue
        
        # Create jurisdiction
        j = Jurisdiction(
            code=code,
            name=info["name"],
            region="Latin America",
            vat_rate=Decimal(str(info.get("vat_rate", 0))),
            capital_gains_rate=Decimal(str(jurisdiction.tax_rate)),
            reporting_currency=info["currency"],
            holding_period_days=info.get("holding_period_days", 365),
            crypto_classification="Crypto income",
            filing_frequency=info.get("filing_frequency", "yearly"),
            filing_authority=info.get("filing_authority", "Tax Authority"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(j)
        db.flush()
        
        print(f"✓ Created jurisdiction: {code} {info['name']}")
    
    db.commit()
    print("\n✅ All jurisdictions loaded successfully!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        load_jurisdictions_data(db)
    except Exception as e:
        print(f"❌ Error loading jurisdictions: {e}")
        sys.exit(1)
    finally:
        db.close()
