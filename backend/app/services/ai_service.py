"""
AI Tax Service — RAG-powered tax consultant.

Builds real portfolio context from the database, injects jurisdiction-specific
tax rules, and queries the configured LLM provider for advice.
"""
from __future__ import annotations

import json
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import AnalysisRun, User
from app.services.llm_provider import LLMResponse, get_llm_provider
from app.tax.ai_consultant import AIConsultantPrompts, PRESET_QUESTIONS, PortfolioContext


class AITaxService:
    """Main service for AI-driven tax consultation."""

    def __init__(self, db: Session):
        self.db = db
        self.llm = get_llm_provider()

    # ---- Context Building (RAG) ----

    def build_portfolio_context(self, user_id: int, run_id: int) -> PortfolioContext:
        """Build a rich portfolio context from the latest analysis run."""
        run = (
            self.db.query(AnalysisRun)
            .filter(AnalysisRun.id == run_id, AnalysisRun.user_id == user_id)
            .first()
        )
        if not run:
            return self._empty_context()

        summary = {}
        try:
            summary = json.loads(run.summary_json or "{}")
        except (json.JSONDecodeError, TypeError):
            summary = {}

        pnl = summary.get("pnl", {})
        if isinstance(pnl, list):
            # Aggregate list-format PnL
            total_gain = sum(float(p.get("total_gain", 0) or p.get("realized_pnl", 0) or 0) for p in pnl)
            total_loss = sum(float(p.get("total_loss", 0) or 0) for p in pnl)
            positions = [
                {
                    "asset": p.get("asset", "?"),
                    "qty": float(p.get("qty", 0) or 0),
                    "price": float(p.get("price", 0) or 0),
                    "total_value": float(p.get("total_value", 0) or 0),
                    "unrealized_gain": float(p.get("unrealized_gain", 0) or 0),
                }
                for p in pnl
            ]
        else:
            total_gain = float(pnl.get("total_realized_pnl_usd", 0) or 0)
            total_loss = 0
            positions = []

        return PortfolioContext(
            total_usd_value=total_gain,
            total_cost_basis=float(pnl.get("cost_basis", 0) or 0) if isinstance(pnl, dict) else 0,
            unrealized_gains=total_gain - total_loss,
            positions=positions,
            transactions=[],
            income_events=summary.get("income_events", []) if isinstance(summary.get("income_events"), list) else [],
            tax_loss_harvesting_opportunities=summary.get("loss_harvesting", {}).get("opportunities", []) if isinstance(summary.get("loss_harvesting"), dict) else [],
            total_income=0,
            estimated_tax_liability=total_gain * 0.15,  # Rough estimate
        )

    def build_jurisdiction_context(self, country_code: str) -> str:
        """Build jurisdiction-specific tax rules text."""
        rules = JURISDICTION_RULES.get(country_code.upper(), JURISDICTION_RULES["DEFAULT"])
        return "\n".join(f"- {k}: {v}" for k, v in rules.items())

    # ---- Chat ----

    def ask(
        self,
        question: str,
        user_id: int,
        run_id: int,
        country_code: str = "BR",
    ) -> dict[str, Any]:
        """Ask the AI consultant a question with full portfolio context."""
        portfolio = self.build_portfolio_context(user_id, run_id)
        jurisdiction = self.build_jurisdiction_context(country_code)

        system_prompt = (
            AIConsultantPrompts.system_prompt()
            + f"\n\nJurisdiction Rules ({country_code}):\n{jurisdiction}"
        )
        user_prompt = AIConsultantPrompts.make_question_prompt(question, portfolio)

        response = self.llm.chat(system_prompt, user_prompt)

        return {
            "question": question,
            "answer": response.text,
            "provider": response.provider,
            "model": response.model,
            "confidence": response.confidence,
            "tokens_used": response.tokens_used,
            "portfolio_summary": {
                "total_value": portfolio.total_usd_value,
                "unrealized_gains": portfolio.unrealized_gains,
                "estimated_tax": portfolio.estimated_tax_liability,
            },
        }

    def get_presets(self) -> list[dict[str, str]]:
        """Get preset questions."""
        return [{"id": k, "question": v} for k, v in PRESET_QUESTIONS.items()]

    # ---- Helpers ----

    def _empty_context(self) -> PortfolioContext:
        return PortfolioContext(
            total_usd_value=0,
            total_cost_basis=0,
            unrealized_gains=0,
            positions=[],
            transactions=[],
            income_events=[],
            tax_loss_harvesting_opportunities=[],
            total_income=0,
            estimated_tax_liability=0,
        )


# ---------------------------------------------------------------------------
# Jurisdiction tax rule templates
# ---------------------------------------------------------------------------

JURISDICTION_RULES = {
    "BR": {
        "Exemption threshold": "Sales below R$35,000/month are exempt from capital gains",
        "Short-term rate": "15% on gains up to R$5M, 17.5% up to R$10M, 20% up to R$30M, 22.5% above R$30M",
        "Reporting requirement": "DeCripto (IN 1888/2019) required for operations above R$30,000/month",
        "Holding period benefit": "No holding period benefit in Brazil — rate depends on gain amount",
        "Staking income": "Taxed as ordinary income at progressive rates (7.5% to 27.5%)",
        "NFT taxation": "Treated as capital asset — same rules as crypto",
    },
    "US": {
        "Long-term threshold": "Assets held > 1 year qualify for long-term capital gains (0/15/20%)",
        "Short-term rate": "Same as ordinary income bracket",
        "Wash sale": "30-day wash sale rule applies (IRS interpretation pending)",
        "Staking income": "Taxed as ordinary income at fair market value upon receipt",
        "Reporting": "Form 8949 and Schedule D required",
    },
    "DEFAULT": {
        "General advice": "Consult a local tax professional for jurisdiction-specific rules",
        "Capital gains": "Most jurisdictions tax crypto gains as capital gains",
        "Income": "Staking/airdrops are typically taxed as ordinary income",
    },
}
