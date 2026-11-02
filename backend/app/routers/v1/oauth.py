import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.auth import get_current_user
from app.core.api_errors import bad_request_from_exc
from app.core.db import get_db
from app.models import User, ExchangeConnection
from app.services.oauth import oauth_manager
from app.core.config import get_settings
from app.core.security import encrypt_secret_if_needed
from app.services.exchange_service import _ensure_portfolio

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/oauth", tags=["OAuth"])

@router.get("/{provider}/initiate")
async def oauth_initiate(
    provider: str,
    current_user: User = Depends(get_current_user)
):
    """Start the OAuth flow by generating the authorization URL."""
    mgr_provider = oauth_manager.get_provider(provider)
    settings = get_settings()
    # Frontend landing page shows a spinner, then POSTs the code to the backend.
    frontend_callback_url = f"{settings.FRONTEND_URL}/oauth/callback"
    
    state = oauth_manager.generate_state(current_user.id)
    auth_url = mgr_provider.get_auth_url(state, frontend_callback_url)
    
    return {"url": auth_url, "state": state}

@router.post("/{provider}/finalize")
async def oauth_finalize(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize OAuth flow: exchange code for tokens and save connection."""
    if not oauth_manager.verify_state(state, current_user.id):
        raise HTTPException(status_code=400, detail="Invalid or expired state token")
    
    mgr_provider = oauth_manager.get_provider(provider)
    settings = get_settings()
    frontend_callback_url = f"{settings.FRONTEND_URL}/oauth/callback"
    
    try:
        tokens = await mgr_provider.exchange_code(code, frontend_callback_url)
        _user_info = await mgr_provider.get_user_info(tokens.access_token)
        logger.debug("OAuth user info retrieved for %s: %s", provider, bool(_user_info))

        portfolio = _ensure_portfolio(db, current_user)
        
        # Check if connection already exists
        conn = db.query(ExchangeConnection).filter(
            ExchangeConnection.user_id == current_user.id,
            ExchangeConnection.provider == provider.lower()
        ).first()
        
        if not conn:
            conn = ExchangeConnection(
                user_id=current_user.id,
                portfolio_id=portfolio.id,
                provider=provider.lower(),
                exchange_name=provider.lower(),
            )
            db.add(conn)
        
        conn.api_key = encrypt_secret_if_needed(tokens.access_token)
        conn.api_secret = encrypt_secret_if_needed(tokens.refresh_token)
        conn.is_oauth = True
        conn.has_credentials = True
        conn.status = "connected"
        conn.updated_at = datetime.now(timezone.utc)
        
        if tokens.expires_in:
            conn.oauth_expires_at = datetime.now(timezone.utc) + timedelta(seconds=tokens.expires_in)
            
        db.commit()
        db.refresh(conn)
        
        return {
            "status": "success",
            "exchange_name": conn.exchange_name,
            "id": conn.id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise bad_request_from_exc(
            logger,
            e,
            public_message="Unable to complete OAuth. Please try again.",
        ) from e
