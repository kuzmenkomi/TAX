"""Apply Cloudflare geo hints to user portfolio / tax jurisdiction."""

from __future__ import annotations

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.cloudflare_geo import get_cf_ip_country, resolve_jurisdiction
from app.countries.registries.country_registry import CountryRegistry
from app.models import Portfolio, User
from app.services.portfolio_service import get_or_create_portfolio


def jurisdiction_from_request(request: Request) -> tuple[str, str, str | None]:
    """Return (jurisdiction_code, display_name, raw_cf_country)."""
    cf_code = get_cf_ip_country(request)
    code, name = resolve_jurisdiction(cf_code)
    return code, name, cf_code


def _country_currency(code: str) -> str:
    try:
        return str(CountryRegistry.get_country(code).currency)
    except ValueError:
        return "USD"


def apply_registration_geo(db: Session, user: User, request: Request) -> dict[str, object]:
    """
    Set user.jurisdiction_code and initial portfolio from CF-IPCountry at sign-up.
    """
    code, name, cf_code = jurisdiction_from_request(request)
    source = "cloudflare" if cf_code and CountryRegistry.is_supported(cf_code) else "default"

    user.jurisdiction_code = code
    db.flush()

    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not portfolio:
        portfolio = Portfolio(
            user_id=user.id,
            country_code=code,
            base_currency=_country_currency(code),
            geo_jurisdiction_applied=True,
            country_locked=False,
            jurisdiction_source=source,
        )
        db.add(portfolio)
    else:
        portfolio.country_code = code
        portfolio.base_currency = _country_currency(code)
        portfolio.geo_jurisdiction_applied = True
        portfolio.jurisdiction_source = source

    db.commit()
    db.refresh(user)

    return {
        "jurisdiction_code": code,
        "jurisdiction_name": name,
        "cf_country": cf_code,
        "source": source,
    }


def apply_tax_center_geo(
    db: Session,
    user: User,
    request: Request,
    *,
    force: bool = False,
) -> dict[str, object]:
    """
    On first Tax Center visit, set portfolio country from CF-IPCountry.

    Skips when the user has manually chosen a jurisdiction (country_locked).
    """
    portfolio = get_or_create_portfolio(db, user)
    cf_code = get_cf_ip_country(request)
    code, name = resolve_jurisdiction(cf_code)

    already_applied = bool(getattr(portfolio, "geo_jurisdiction_applied", False))
    user_locked = bool(getattr(portfolio, "country_locked", False))
    user_code = (getattr(user, "jurisdiction_code", None) or "").upper()

    applied_now = False
    if user_code and not force:
        code = user_code
        name = _jurisdiction_display_name(code)
    elif not user_locked and (force or not already_applied):
        portfolio.country_code = code
        portfolio.base_currency = _country_currency(code)
        portfolio.geo_jurisdiction_applied = True
        if cf_code and CountryRegistry.is_supported(cf_code):
            portfolio.jurisdiction_source = "cloudflare"
        else:
            portfolio.jurisdiction_source = "default"
        user.jurisdiction_code = code
        db.commit()
        db.refresh(portfolio)
        db.refresh(user)
        applied_now = True

    return {
        "jurisdiction_code": portfolio.country_code,
        "jurisdiction_name": _jurisdiction_display_name(portfolio.country_code),
        "base_currency": portfolio.base_currency,
        "applied_now": applied_now,
        "geo_jurisdiction_applied": bool(portfolio.geo_jurisdiction_applied),
        "country_locked": bool(portfolio.country_locked),
        "source": portfolio.jurisdiction_source,
        "cf_country": cf_code,
    }


def set_user_jurisdiction(
    db: Session,
    user: User,
    jurisdiction_code: str,
    *,
    locked: bool = True,
) -> dict[str, object]:
    """Persist explicit user jurisdiction choice."""
    code = jurisdiction_code.strip().upper()
    if not CountryRegistry.is_supported(code):
        raise ValueError(f"Unsupported jurisdiction: {code}")

    portfolio = get_or_create_portfolio(db, user)
    user.jurisdiction_code = code
    portfolio.country_code = code
    portfolio.base_currency = _country_currency(code)
    portfolio.country_locked = locked
    portfolio.jurisdiction_source = "user"
    portfolio.geo_jurisdiction_applied = True
    db.add(user)
    db.add(portfolio)
    db.commit()
    db.refresh(user)
    db.refresh(portfolio)

    return {
        "jurisdiction_code": code,
        "jurisdiction_name": _jurisdiction_display_name(code),
        "base_currency": portfolio.base_currency,
        "country_locked": portfolio.country_locked,
        "source": portfolio.jurisdiction_source,
    }


def _jurisdiction_display_name(code: str) -> str:
    try:
        return str(CountryRegistry.get_country(code).country_name)
    except ValueError:
        return code
