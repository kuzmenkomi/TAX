from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.core.db import get_db
from app.models import User
from app.schemas.portfolio import DashboardResponse, OnboardingRequest, PortfolioOut
from app.services.portfolio_service import complete_onboarding, get_dashboard, get_or_create_portfolio

router = APIRouter(tags=["portfolio"])


@router.post("/onboarding")
def onboard_user(
    body: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    portfolio = complete_onboarding(
        db,
        current_user,
        body.country_code,
        body.tax_structure,
        body.portfolio_size,
    )
    return {
        "status": "ok",
        "portfolio_id": portfolio.id,
        "country_code": portfolio.country_code,
        "tax_structure": portfolio.tax_structure,
        "portfolio_size": portfolio.portfolio_size,
    }


@router.get("/br/portfolio", response_model=PortfolioOut)
def read_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioOut:
    return PortfolioOut.model_validate(get_or_create_portfolio(db, current_user))


@router.get("/br/dashboard", response_model=DashboardResponse)
def read_dashboard(
    tax_year: int | None = Query(default=None, ge=1900, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    return DashboardResponse.model_validate(get_dashboard(db, current_user, tax_year=tax_year))


def _portfolio_summary(
    tax_year: int | None,
    current_user: User,
    db: Session,
) -> DashboardResponse:
    return DashboardResponse.model_validate(get_dashboard(db, current_user, tax_year=tax_year))


@router.get("/summary", response_model=DashboardResponse)
def get_summary(
    tax_year: int | None = Query(default=None, ge=1900, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Dashboard portfolio snapshot (live prices + open positions)."""
    return _portfolio_summary(tax_year, current_user, db)


@router.get("/portfolio/summary", response_model=DashboardResponse, include_in_schema=False)
def get_summary_frontend_alias(
    tax_year: int | None = Query(default=None, ge=1900, le=2100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    """Frontend client calls /portfolio/summary."""
    return _portfolio_summary(tax_year, current_user, db)


@router.get("/unrealized-pnl")
def get_pnl(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Returns unrealized P&L in USD and BRL."""
    data = get_dashboard(db, current_user)
    return {
        "amount_usd": data.get("total_unrealized_pnl_usd", 0.0),
        "amount_brl": round(data.get("total_unrealized_pnl_usd", 0.0) * 5.0, 2), # Simplified multiplier for now
        "percentage": data.get("total_unrealized_pnl_pct", 0.0),
    }
