import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.api_errors import server_error
from app.core.db import get_db
from app.models import BankTransaction, User
from app.integrations.parsers.bank_parsers import NubankParser, MercadoPagoParser
from app.services.matching_service import MatchingService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/import", tags=["Import"])

@router.post("/bank-csv/{bank_type}")
async def import_bank_csv(
    bank_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and parse bank CSV statements.
    Supported bank_type: nubank, mercado_pago, lemon, belo
    """
    content = await file.read()
    
    if bank_type == "nubank":
        parser = NubankParser()
    elif bank_type == "mercado_pago":
        parser = MercadoPagoParser()
    else:
        from app.integrations.parsers.local_exchange_parsers import get_parser_for_exchange
        parser = get_parser_for_exchange(bank_type)
        
    if not parser:
        raise HTTPException(status_code=400, detail="Unsupported bank/exchange type")
        
    try:
        df = parser.parse(content)
        
        # Save to database (Simplified)
        # Note: In real app, we should check for duplicates
        for _, row in df.iterrows():
            txn = BankTransaction(
                id=str(row.get('external_id') or row['timestamp'].timestamp()),
                account_id="UPLOADED_CSV", # Placeholder or link to a real account
                date=row['timestamp'],
                type=row['type'],
                amount=row['amount'],
                currency=row['asset'],
                description=row.get('description', ''),
                counterparty="CSV_IMPORT"
            )
            db.merge(txn) # Use merge to avoid duplicates if ID exists
            
        db.commit()
        return {"status": "success", "rows_imported": len(df)}
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Failed to parse bank CSV")
        raise server_error(logger, e) from e

@router.post("/run-p2p-matching")
async def run_p2p_matching(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Trigger the P2P matching algorithm for the user.
    """
    matches = MatchingService.match_p2p_purchases(db, current_user.id)
    return {"status": "success", "matches_found": matches}
