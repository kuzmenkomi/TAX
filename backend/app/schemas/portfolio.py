from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class PortfolioOut(BaseModel):
    id: int
    country_code: str
    name: str
    base_currency: str
    is_onboarded: bool

    model_config = {"from_attributes": True}


class OnboardingRequest(BaseModel):
    country_code: str
    tax_structure: str   # individual / business / fund
    portfolio_size: str  # <10k / 10k-50k / 10k-100k / 100k-500k / >500k


class PortfolioPosition(BaseModel):
    asset: str
    quantity: float
    avg_cost_usd: float
    current_price_usd: float
    cost_basis_usd: float
    current_value_usd: float
    unrealized_pnl_usd: float
    unrealized_pnl_pct: float


class DashboardResponse(BaseModel):
    portfolio_id: int
    total_cost_basis_usd: float
    total_current_value_usd: float
    total_unrealized_pnl_usd: float
    total_unrealized_pnl_pct: float
    positions: list[PortfolioPosition]
    last_updated: Optional[str] = None
