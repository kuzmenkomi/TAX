"""AI Tax Consultant API — ask questions, get alerts, analyze taxes."""
from __future__ import annotations


from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import User
from app.services.ai_service import AITaxService
from app.services.ai_alerts import ProactiveAlertEngine
from app.services.llm_provider import get_llm_provider
from app.services import billing_service

router = APIRouter(prefix="/ai", tags=["ai-consultant"])


class AskRequest(BaseModel):
    question: str
    run_id: int
    country_code: str = "BR"


@router.post("/ask")
def ask_ai(
    payload: AskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Ask the AI tax consultant a question with full portfolio context."""
    billing_service.check_limit(db, current_user.id, "ai")
    service = AITaxService(db)
    result = service.ask(
        question=payload.question,
        user_id=current_user.id,
        run_id=payload.run_id,
        country_code=payload.country_code,
    )
    return result


@router.get("/presets")
def get_presets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get preset questions for the AI consultant."""
    service = AITaxService(db)
    return {"presets": service.get_presets()}


@router.get("/alerts/{run_id}")
def get_alerts(
    run_id: int,
    country: str = "BR",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Get proactive tax alerts for an analysis run."""
    billing_service.check_limit(db, current_user.id, "ai")
    engine = ProactiveAlertEngine(db)
    alerts = engine.check_alerts(current_user.id, run_id, country)
    return {
        "alerts": [a.to_dict() for a in alerts],
        "count": len(alerts),
    }


@router.get("/provider-info")
def provider_info(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get info about the currently configured LLM provider."""
    provider = get_llm_provider()
    return {
        "provider": provider.name,
        "available": provider.is_available(),
        "upgrade_options": [
            {"name": "ollama", "type": "free", "description": "Local LLM via Ollama (requires Ollama installed)"},
            {"name": "openai", "type": "paid", "description": "OpenAI GPT-4 (requires API key)"},
            {"name": "anthropic", "type": "paid", "description": "Anthropic Claude (requires API key)"},
        ],
    }
