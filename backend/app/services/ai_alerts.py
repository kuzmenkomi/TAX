"""
Proactive AI Tax Alerts — scans portfolio for tax optimization opportunities
and warns users about upcoming thresholds, holding periods, and risks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import AnalysisRun


@dataclass
class TaxAlert:
    """A proactive tax alert."""
    id: str
    urgency: str  # critical, warning, info, opportunity
    title: str
    message: str
    action_label: str | None = None
    action_type: str | None = None  # navigate, sell, wait, etc.
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "urgency": self.urgency,
            "title": self.title,
            "message": self.message,
            "action_label": self.action_label,
            "action_type": self.action_type,
            "metadata": self.metadata,
        }


class ProactiveAlertEngine:
    """Scans the user's data and generates proactive tax alerts."""

    def __init__(self, db: Session):
        self.db = db

    def check_alerts(self, user_id: int, run_id: int, country: str = "BR") -> list[TaxAlert]:
        """Generate alerts for the given analysis run."""
        alerts: list[TaxAlert] = []

        run = (
            self.db.query(AnalysisRun)
            .filter(AnalysisRun.id == run_id, AnalysisRun.user_id == user_id)
            .first()
        )
        if not run:
            return alerts

        import json
        try:
            summary = json.loads(run.summary_json or "{}")
        except (json.JSONDecodeError, TypeError):
            summary = {}

        pnl = summary.get("pnl", {})
        monthly_sales = summary.get("monthly_sales_brl", {})
        income_events = summary.get("income_events", {})

        # Alert 1: Monthly exemption threshold approaching
        alerts.extend(self._check_monthly_threshold(monthly_sales, country))

        # Alert 2: Holding period optimization
        alerts.extend(self._check_holding_periods(summary))

        # Alert 3: Unreported income
        alerts.extend(self._check_unreported_income(income_events))

        # Alert 4: Large unrealized gains
        alerts.extend(self._check_unrealized_gains(pnl))

        # Alert 5: DeCripto reporting threshold (Brazil)
        if country.upper() == "BR":
            alerts.extend(self._check_decripto_threshold(monthly_sales))

        return alerts

    def _check_monthly_threshold(self, monthly_sales: dict, country: str) -> list[TaxAlert]:
        """Check if monthly sales are approaching the exemption threshold."""
        alerts = []
        threshold = 35000.0 if country.upper() == "BR" else 0

        if not threshold or not monthly_sales:
            return alerts

        # Check the latest month
        sorted_months = sorted(monthly_sales.keys())
        if not sorted_months:
            return alerts

        latest_month = sorted_months[-1]
        sales = float(monthly_sales.get(latest_month, 0) or 0)

        if sales >= threshold:
            alerts.append(TaxAlert(
                id="threshold_exceeded",
                urgency="critical",
                title="⚠️ Monthly Exemption Exceeded",
                message=f"Your sales in {latest_month} totaled R${sales:,.2f}, exceeding the R${threshold:,.2f} tax-free limit. Capital gains tax applies to this month's transactions.",
                action_label="View Tax Breakdown",
                action_type="navigate:tax",
            ))
        elif sales >= threshold * 0.8:
            remaining = threshold - sales
            alerts.append(TaxAlert(
                id="threshold_approaching",
                urgency="warning",
                title="🔔 Approaching Monthly Limit",
                message=f"You've sold R${sales:,.2f} this month. Only R${remaining:,.2f} remaining before the R${threshold:,.2f} exemption limit. Consider delaying further sales.",
                action_label="Check Exemption",
                action_type="navigate:dashboard",
            ))

        return alerts

    def _check_holding_periods(self, summary: dict) -> list[TaxAlert]:
        """Check if any positions are close to long-term holding.

        Note: Brazil doesn't have holding period benefits, but
        other jurisdictions (US/UK/DE) do.
        """
        alerts = []
        # This would scan positions for holding periods near thresholds
        # Placeholder for extension
        return alerts

    def _check_unreported_income(self, income_events: Any) -> list[TaxAlert]:
        """Check for unreported staking/airdrop income."""
        alerts = []
        total_income = 0.0

        if isinstance(income_events, dict):
            by_type = income_events.get("by_type", {})
            total_income = sum(float(v) for v in by_type.values()) if by_type else 0
        elif isinstance(income_events, list):
            total_income = sum(float(e.get("amount_usd", 0) or 0) for e in income_events)

        if total_income > 100:
            alerts.append(TaxAlert(
                id="unreported_income",
                urgency="warning",
                title="💰 Crypto Income Detected",
                message=f"You have ${total_income:,.2f} in staking rewards, airdrops, and other income events. This is typically taxed as ordinary income at the time of receipt.",
                action_label="Review Income Events",
                action_type="navigate:transactions",
                metadata={"total_income": total_income},
            ))

        return alerts

    def _check_unrealized_gains(self, pnl: Any) -> list[TaxAlert]:
        """Alert on large unrealized gains."""
        alerts = []
        gains = 0.0

        if isinstance(pnl, dict):
            gains = float(pnl.get("total_realized_pnl_usd", 0) or 0)
        elif isinstance(pnl, list):
            gains = sum(float(p.get("realized_pnl", 0) or 0) for p in pnl)

        if gains > 10000:
            alerts.append(TaxAlert(
                id="large_gains",
                urgency="info",
                title="📈 Significant Gains Detected",
                message=f"Your realized gains total ${gains:,.2f}. Consider tax-loss harvesting to offset some of these gains before year-end.",
                action_label="View TLH Opportunities",
                action_type="navigate:tax",
                metadata={"realized_gains": gains},
            ))

        return alerts

    def _check_decripto_threshold(self, monthly_sales: dict) -> list[TaxAlert]:
        """Check Brazil DeCripto (IN 1888) reporting threshold."""
        alerts = []
        decripto_threshold = 30000.0

        for month, sales in monthly_sales.items():
            if float(sales or 0) >= decripto_threshold:
                alerts.append(TaxAlert(
                    id=f"decripto_{month}",
                    urgency="critical",
                    title="📋 DeCripto Reporting Required",
                    message=f"Operations in {month} exceeded R${decripto_threshold:,.2f}. You must file a DeCripto declaration (IN 1888/2019) with the Receita Federal.",
                    action_label="Generate DeCripto Report",
                    action_type="navigate:exports",
                ))
                break  # One alert is enough

        return alerts
