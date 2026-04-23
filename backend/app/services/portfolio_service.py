from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.accounting.avco_engine import compute_positions_with_unrealized_pnl
from app.accounting.pricing import PriceService
from app.models import AnalysisRun, Portfolio, User

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def get_or_create_portfolio(db: Session, user: User) -> Portfolio:
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user.id,
            country_code="BR",
            name="Principal",
            base_currency="BRL",
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def complete_onboarding(
    db: Session,
    user: User,
    country_code: str,
    tax_structure: str,
    portfolio_size: str,
) -> Portfolio:
    portfolio = get_or_create_portfolio(db, user)
    portfolio.country_code = country_code.strip().upper()
    portfolio.tax_structure = tax_structure.strip().lower()
    portfolio.portfolio_size = portfolio_size.strip().lower()
    portfolio.is_onboarded = True
    db.commit()
    db.refresh(portfolio)
    return portfolio


def get_dashboard(db: Session, user: User) -> dict:
    portfolio = get_or_create_portfolio(db, user)
    last_run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == user.id)
        .order_by(AnalysisRun.created_at.desc())
        .first()
    )

    empty_response = {
        "portfolio_id": portfolio.id,
        "total_cost_basis_usd": 0.0,
        "total_current_value_usd": 0.0,
        "total_unrealized_pnl_usd": 0.0,
        "total_unrealized_pnl_pct": 0.0,
        "positions": [],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    if not last_run or not last_run.csv_rel_path:
        return empty_response

    csv_path = Path(last_run.csv_rel_path)
    if not csv_path.is_absolute():
        csv_path = BACKEND_ROOT / csv_path
    if not csv_path.exists():
        return empty_response

    df = pd.read_csv(csv_path)
    assets = [asset.upper() for asset in df["asset"].dropna().unique().tolist() if asset]
    current_prices = PriceService().get_current_prices_for_assets(assets)
    positions = compute_positions_with_unrealized_pnl(df, current_prices)

    total_cost = sum(position["cost_basis_usd"] for position in positions)
    total_value = sum(position["current_value_usd"] for position in positions)
    total_pnl = total_value - total_cost
    pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    return {
        "portfolio_id": portfolio.id,
        "total_cost_basis_usd": round(total_cost, 2),
        "total_current_value_usd": round(total_value, 2),
        "total_unrealized_pnl_usd": round(total_pnl, 2),
        "total_unrealized_pnl_pct": round(pct, 2),
        "positions": positions,
        "last_updated": last_run.created_at.isoformat(),
    }
