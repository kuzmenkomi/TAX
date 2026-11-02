"""Tax liability estimation helpers for dashboard and analysis summaries."""

from __future__ import annotations

from typing import Any

BRAZIL_COUNTRY_CODES = frozenset({"BR", "BRA", "BRAZIL"})
DEFAULT_CAPITAL_GAINS_RATE = 0.15
BRAZIL_MONTHLY_SALES_THRESHOLD_BRL = 35_000.0


def uses_monthly_tax_settlement(country: str | None) -> bool:
    """Brazil DARF-style: tax accrues per calendar month when sales exceed threshold."""
    normalized = (country or "").strip().upper()
    return normalized in BRAZIL_COUNTRY_CODES


def _filter_by_tax_year(values: dict[str, float], tax_year: int | None) -> dict[str, float]:
    if tax_year is None:
        return dict(values)
    prefix = f"{tax_year}-"
    return {key: float(amount) for key, amount in values.items() if str(key).startswith(prefix)}


def _annual_net_realized(
    monthly_gains: dict[str, float],
    monthly_losses: dict[str, float],
    tax_year: int | None,
) -> float:
    gains = _filter_by_tax_year(monthly_gains, tax_year)
    losses = _filter_by_tax_year(monthly_losses, tax_year)
    return sum(gains.values()) - sum(losses.values())


def compute_monthly_brazil_tax(
    monthly_gains: dict[str, float],
    monthly_losses: dict[str, float],
    *,
    monthly_sales_brl: dict[str, float] | None = None,
    tax_rate: float = DEFAULT_CAPITAL_GAINS_RATE,
    threshold_brl: float = BRAZIL_MONTHLY_SALES_THRESHOLD_BRL,
    tax_year: int | None = None,
) -> dict[str, float]:
    """Per-month DARF-style estimate (losses offset gains within the same month only)."""
    gains = _filter_by_tax_year(monthly_gains, tax_year)
    losses = _filter_by_tax_year(monthly_losses, tax_year)
    sales = _filter_by_tax_year(monthly_sales_brl or {}, tax_year)

    monthly_tax: dict[str, float] = {}
    for ym in set(gains) | set(losses):
        net_gain = gains.get(ym, 0.0) - losses.get(ym, 0.0)
        if net_gain <= 0:
            continue
        if sales.get(ym, 0.0) <= threshold_brl:
            continue
        monthly_tax[ym] = net_gain * tax_rate
    return monthly_tax


def compute_tax_liability(
    *,
    country: str | None,
    monthly_gains: dict[str, float],
    monthly_losses: dict[str, float],
    monthly_tax_from_run: dict[str, float] | None = None,
    monthly_sales_brl: dict[str, float] | None = None,
    tax_rate: float = DEFAULT_CAPITAL_GAINS_RATE,
    tax_year: int | None = None,
) -> tuple[float, dict[str, float]]:
    """
    Return (total_tax_usd, monthly_tax_breakdown).

    US / most jurisdictions: annual net realized × rate (losses offset gains across the year).
    Brazil: monthly settlement with BRL sales threshold (no cross-month loss carry on dashboard).
    """
    if uses_monthly_tax_settlement(country):
        existing = _filter_by_tax_year(monthly_tax_from_run or {}, tax_year)
        if existing:
            return sum(existing.values()), existing

        monthly_tax = compute_monthly_brazil_tax(
            monthly_gains,
            monthly_losses,
            monthly_sales_brl=monthly_sales_brl,
            tax_rate=tax_rate,
            tax_year=tax_year,
        )
        return sum(monthly_tax.values()), monthly_tax

    net_realized = _annual_net_realized(monthly_gains, monthly_losses, tax_year)
    total_tax = max(0.0, net_realized) * tax_rate
    return total_tax, {}


def attach_tax_to_pnl(
    pnl: dict[str, Any],
    *,
    country: str | None,
    monthly_sales_brl: dict[str, float] | None = None,
    tax_rate: float = DEFAULT_CAPITAL_GAINS_RATE,
    tax_year: int | None = None,
) -> dict[str, Any]:
    """Mutate-compatible helper: set total_tax_owed_usd and monthly_tax_owed on a pnl dict."""
    monthly_gains = pnl.get("monthly_gains") if isinstance(pnl.get("monthly_gains"), dict) else {}
    monthly_losses = pnl.get("monthly_losses") if isinstance(pnl.get("monthly_losses"), dict) else {}
    monthly_tax_existing = pnl.get("monthly_tax_owed") if isinstance(pnl.get("monthly_tax_owed"), dict) else {}

    total_tax, monthly_tax = compute_tax_liability(
        country=country,
        monthly_gains=monthly_gains,
        monthly_losses=monthly_losses,
        monthly_tax_from_run=monthly_tax_existing,
        monthly_sales_brl=monthly_sales_brl,
        tax_rate=tax_rate,
        tax_year=tax_year,
    )

    updated = dict(pnl)
    updated["monthly_tax_owed"] = monthly_tax
    updated["total_tax_owed_usd"] = float(total_tax)
    return updated
