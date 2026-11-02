from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.orm import Session

from app.accounting.avco_engine import compute_positions_with_unrealized_pnl
from app.accounting.pricing import PriceService
from app.models import Portfolio, User


def get_or_create_portfolio(db: Session, user: User) -> Portfolio:
    from app.countries.registries.country_registry import CountryRegistry

    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        code = (getattr(user, "jurisdiction_code", None) or "BR").upper()
        currency = "BRL"
        try:
            currency = str(CountryRegistry.get_country(code).currency)
        except ValueError:
            pass
        portfolio = Portfolio(
            user_id=user.id,
            country_code=code,
            name="Principal",
            base_currency=currency,
            geo_jurisdiction_applied=bool(getattr(user, "jurisdiction_code", None)),
            jurisdiction_source="registration" if getattr(user, "jurisdiction_code", None) else None,
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    return portfolio


def _resolve_accounting_method(db: Session, user: User) -> str:
    """Use the same cost-basis method as the latest tax analysis when available."""
    import json

    from app.models.analysis import AnalysisRun
    from app.models.tax_profile import UserTaxProfile

    latest_run = (
        db.query(AnalysisRun)
        .filter(AnalysisRun.user_id == user.id)
        .order_by(AnalysisRun.created_at.desc())
        .first()
    )
    if latest_run and latest_run.summary_json:
        try:
            summary = json.loads(latest_run.summary_json)
            method = str(summary.get("accounting_method") or "").strip().upper()
            if method:
                return method
        except json.JSONDecodeError:
            pass

    profile = db.query(UserTaxProfile).filter(UserTaxProfile.user_id == user.id).first()
    if profile and profile.calculation_method:
        method = profile.calculation_method.strip().upper().replace("AVERAGE_COST", "AVCO")
        if method:
            return method

    portfolio = get_or_create_portfolio(db, user)
    country = (portfolio.country_code or "US").upper()
    if country in {"BR", "UK", "DE"}:
        return "AVCO"
    return "FIFO"


def complete_onboarding(
    db: Session,
    user: User,
    country_code: str,
    tax_structure: str,
    portfolio_size: str,
) -> Portfolio:
    portfolio = get_or_create_portfolio(db, user)
    code = country_code.strip().upper()
    portfolio.country_code = code
    user.jurisdiction_code = code
    portfolio.tax_structure = tax_structure.strip().lower()
    portfolio.portfolio_size = portfolio_size.strip().lower()
    portfolio.is_onboarded = True
    portfolio.country_locked = True
    portfolio.geo_jurisdiction_applied = True
    portfolio.jurisdiction_source = "user"
    db.commit()
    db.refresh(portfolio)
    return portfolio


def _portfolio_transactions_df(db: Session, user_id: int, tax_year: int | None) -> pd.DataFrame:
    from app.models.transaction import Transaction

    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    if tax_year is not None:
        query = query.filter(Transaction.timestamp < datetime(tax_year + 1, 1, 1))

    rows = query.order_by(Transaction.timestamp.asc(), Transaction.id.asc()).all()
    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(
        [
            {
                "timestamp": row.timestamp,
                "asset": row.asset,
                "type": row.tx_type,
                "amount": float(row.amount),
                "fee": float(row.fee or 0),
                "price": float(row.price) if row.price is not None else None,
                "total_value": float(row.total_value) if row.total_value is not None else None,
                "from_wallet": row.from_wallet or "",
                "to_wallet": row.to_wallet or "",
                "external_id": row.external_id or "",
                "audit_hash": row.audit_hash or "",
            }
            for row in rows
        ]
    )


def _latest_known_prices(df: pd.DataFrame) -> dict[str, float]:
    prices: dict[str, float] = {}
    if df.empty or "price" not in df.columns:
        return prices

    stablecoins = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP"}
    for asset in stablecoins:
        prices[asset.lower()] = 1.0

    ordered = df.sort_values("timestamp")
    for _, row in ordered.iterrows():
        asset = str(row.get("asset") or "").upper()
        if not asset:
            continue
        try:
            price = float(row.get("price") or 0.0)
        except (TypeError, ValueError):
            price = 0.0
        if price > 0:
            prices[asset.lower()] = price
    return prices


def _live_prices_for_positions(df: pd.DataFrame, accounting_method: str = "AVCO") -> dict[str, float]:
    """Fetch real-time USD prices for every open position (not stale tx prices)."""
    from app.accounting.inventory_engine import compute_open_inventory

    inventory = compute_open_inventory(df, accounting_method)
    open_assets = [asset.upper() for asset in inventory if inventory[asset].get("quantity", 0) > 0]
    if not open_assets:
        return {}

    stablecoins = {"USDT", "USDC", "BUSD", "DAI", "TUSD", "USDP"}
    current_prices: dict[str, float] = {s.lower(): 1.0 for s in stablecoins if s in open_assets}

    live_assets = [asset for asset in open_assets if asset not in stablecoins]
    if not live_assets:
        return current_prices

    try:
        live_prices = PriceService().get_current_prices_for_assets(live_assets)
        current_prices.update({key: value for key, value in live_prices.items() if value > 0})
    except Exception:
        pass

    # Last-resort fallback: most recent price from the user's own transaction history.
    if any(current_prices.get(asset.lower(), 0.0) <= 0 for asset in live_assets):
        fallback = _latest_known_prices(df)
        for asset in live_assets:
            key = asset.lower()
            if current_prices.get(key, 0.0) <= 0 and fallback.get(key, 0.0) > 0:
                current_prices[key] = fallback[key]

    return current_prices


def get_dashboard(db: Session, user: User, tax_year: int | None = None) -> dict:
    portfolio = get_or_create_portfolio(db, user)
    empty_response = {
        "portfolio_id": portfolio.id,
        "total_cost_basis_usd": 0.0,
        "total_current_value_usd": 0.0,
        "total_unrealized_pnl_usd": 0.0,
        "total_unrealized_pnl_pct": 0.0,
        "positions": [],
        "tax_year": tax_year,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    # Holdings = transactions up to the selected tax year (Dec 31 snapshot).
    df = _portfolio_transactions_df(db, user.id, tax_year)
    if df.empty:
        return empty_response

    accounting_method = _resolve_accounting_method(db, user)
    current_year = datetime.now(timezone.utc).year
    use_live_prices = tax_year is None or tax_year >= current_year
    current_prices = (
        _live_prices_for_positions(df, accounting_method) if use_live_prices else _latest_known_prices(df)
    )
    positions = compute_positions_with_unrealized_pnl(df, current_prices, accounting_method)

    total_cost = sum(position["cost_basis_usd"] for position in positions)
    total_value = sum(position["current_value_usd"] for position in positions)
    total_pnl = total_value - total_cost
    pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0

    # Add Parallel Rate if in Argentina
    from app.models.tax_profile import UserTaxProfile
    from app.services.financial_data_service import FinancialDataService
    
    profile = db.query(UserTaxProfile).filter(UserTaxProfile.user_id == user.id).first()
    
    response = {
        "portfolio_id": portfolio.id,
        "total_cost_basis_usd": float(total_cost),
        "total_current_value_usd": float(total_value),
        "total_unrealized_pnl_usd": float(total_pnl),
        "total_unrealized_pnl_pct": float(pct),
        "positions": positions,
        "tax_year": tax_year,
        "prices_as_of": "live" if use_live_prices else "year_end",
        "accounting_method": accounting_method,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }

    if profile and profile.dashboard_rate_preference == "PARALLEL":
        # Currently only ARS Blue is implemented in get_parallel_rate
        blue_rate = FinancialDataService.get_parallel_rate("USD", "ARS")
        response["parallel_rate"] = float(blue_rate)
        response["total_current_value_ars_blue"] = float(total_value * float(blue_rate))
        response["is_parallel"] = True

    return response
