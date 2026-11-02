"""
United States Tax Calculator
Implements IRS 2025 rules for crypto/DeFi taxation.

Key rules applied:
- Short-term gains (≤365 days)  → ordinary income rates (10%–37%)
- Long-term gains (>365 days)   → preferential rates (0%, 15%, 20%)
- Staking rewards               → ordinary income at FMV on receipt
- Mining income                 → ordinary income (Schedule C if business)
- DeFi swaps                    → taxable at swap time
- NIIT 3.8%                     → applies on gains when MAGI > $200k (single)
"""

from .config import UnitedStates
from ..base.tax_calculator import BaseTaxCalculator
from ..base.definitions import TaxType, TaxBracket
from decimal import Decimal
from typing import Dict, Any


class TaxCalculator(BaseTaxCalculator):
    """US-specific tax calculator (IRS 2025)."""

    def __init__(self):
        super().__init__(UnitedStates())
        self._us = self.country  # convenience alias

    # ------------------------------------------------------------------
    # Override: Capital Gains — short vs long-term distinction
    # ------------------------------------------------------------------

    def calculate_capital_gains_tax(
        self,
        capital_gains: float,
        holding_period_days: int = 366,
        magi: float = 0.0,
        filing_status: str = "single",
    ) -> Dict[str, Any]:
        """
        IRS capital gains tax with short/long-term split.

        Short-term (≤ 365 days): taxed at ordinary income rates.
        Long-term  (> 365 days): taxed at preferential 0/15/20% rates.
        NIIT 3.8% added when MAGI > threshold.
        """
        is_long = self._us.is_long_term(holding_period_days)
        gain_type = "long_term" if is_long else "short_term"

        if is_long:
            # Long-term: use LTCG brackets
            rate_key = "capital_gains"  # mapped to LTCG_BRACKETS_SINGLE
            brackets = self._us.LTCG_BRACKETS_SINGLE
        else:
            # Short-term: ordinary income rates
            brackets = self._us.INCOME_BRACKETS_SINGLE
            rate_key = "income"

        tax = self._apply_brackets(capital_gains, brackets)
        niit = self._us.calculate_niit(capital_gains, magi or capital_gains, filing_status)

        return {
            "capital_gains": capital_gains,
            "holding_period_days": holding_period_days,
            "gain_type": gain_type,
            "capital_gains_tax": round(tax + niit, 2),
            "base_tax": round(tax, 2),
            "niit": round(niit, 2),
            "effective_rate": round((tax + niit) / capital_gains, 4) if capital_gains > 0 else 0,
            "filing_status": filing_status,
        }

    # ------------------------------------------------------------------
    # Override: Crypto — property rules, per IRS Notice 2014-21
    # ------------------------------------------------------------------

    def calculate_cryptocurrency_tax(
        self,
        crypto_gains: float = 0,
        staking_income: float = 0,
        mining_income: float = 0,
        holding_period_days: int = 366,
        magi: float = 0.0,
        filing_status: str = "single",
    ) -> Dict[str, Any]:
        """
        IRS crypto tax calculation (property treatment).
        - Gains: short or long-term capital gains.
        - Staking / mining: ordinary income.
        """
        gains_tax = self.calculate_capital_gains_tax(
            crypto_gains, holding_period_days, magi, filing_status
        )
        staking_tax = self.calculate_income_tax(staking_income)
        mining_tax = self.calculate_income_tax(mining_income)

        total = (
            gains_tax["capital_gains_tax"]
            + staking_tax["income_tax"]
            + mining_tax["income_tax"]
        )

        return {
            "total_crypto_income": crypto_gains + staking_income + mining_income,
            "crypto_treatment": "property (IRS Notice 2014-21)",
            "components": {
                "crypto_gains": gains_tax,
                "staking_income": staking_tax,
                "mining_income": mining_tax,
            },
            "total_cryptocurrency_tax": round(total, 2),
        }

    # ------------------------------------------------------------------
    # Override: DeFi — IRS final regs Dec 2024
    # ------------------------------------------------------------------

    def calculate_defi_tax(
        self,
        farming_income: float = 0,
        yield_income: float = 0,
        swap_gains: float = 0,
        liquidity_pool_gains: float = 0,
        holding_period_days: int = 366,
        magi: float = 0.0,
        filing_status: str = "single",
    ) -> Dict[str, Any]:
        """
        DeFi tax under IRS final broker regulations (Dec 2024).
        - Farming / yield: ordinary income at FMV on receipt.
        - Swaps: taxable at swap time, short or long-term.
        - LP gains: capital gains treatment.
        """
        farming_tax = self.calculate_income_tax(farming_income)
        yield_tax = self.calculate_income_tax(yield_income)
        swap_tax = self.calculate_capital_gains_tax(swap_gains, holding_period_days, magi, filing_status)
        lp_tax = self.calculate_capital_gains_tax(liquidity_pool_gains, holding_period_days, magi, filing_status)

        total = (
            farming_tax["income_tax"]
            + yield_tax["income_tax"]
            + swap_tax["capital_gains_tax"]
            + lp_tax["capital_gains_tax"]
        )

        return {
            "farming_income": farming_income,
            "yield_income": yield_income,
            "swap_gains": swap_gains,
            "liquidity_pool_gains": liquidity_pool_gains,
            "total_defi_income": farming_income + yield_income + swap_gains + liquidity_pool_gains,
            "farming_tax": farming_tax,
            "yield_tax": yield_tax,
            "swap_tax": swap_tax,
            "lp_tax": lp_tax,
            "total_defi_tax": round(total, 2),
            "irs_rule": "IRS Final Regs Dec 2024 — DeFi swaps are taxable disposals",
        }

    # ------------------------------------------------------------------
    # Internal helper: apply bracket list directly
    # ------------------------------------------------------------------

    def _apply_brackets(self, amount: float, brackets: list) -> float:
        """Apply a list of TaxBracket objects to an amount."""
        try:
            dec_amount = Decimal(str(amount))
        except Exception:
            return 0.0

        total = Decimal(0)
        for b in sorted(brackets, key=lambda x: float(x.min_amount)):
            dec_min = Decimal(str(b.min_amount))
            if dec_amount <= dec_min:
                break
            dec_max = Decimal(str(b.max_amount))
            taxable = min(dec_amount, dec_max) - dec_min
            total += taxable * Decimal(str(b.rate))

        return float(total)

    # ------------------------------------------------------------------
    # Convenience: summary for a US crypto investor
    # ------------------------------------------------------------------

    def calculate_us_crypto_summary(
        self,
        short_term_gains: float = 0,
        long_term_gains: float = 0,
        staking_income: float = 0,
        mining_income: float = 0,
        gross_income: float = 0,
        filing_status: str = "single",
        use_standard_deduction: bool = True,
    ) -> Dict[str, Any]:
        """
        Full US investor tax summary.
        Applies standard deduction to ordinary income, then computes all components.
        """
        std_deduction = float(
            self._us.STANDARD_DEDUCTION_MFJ if filing_status == "mfj"
            else self._us.STANDARD_DEDUCTION_SINGLE
        )
        deductions = {"standard": std_deduction} if use_standard_deduction else {}

        magi = gross_income + short_term_gains + long_term_gains + staking_income + mining_income

        st = self.calculate_capital_gains_tax(short_term_gains, 180, magi, filing_status)
        lt = self.calculate_capital_gains_tax(long_term_gains, 400, magi, filing_status)
        stk = self.calculate_income_tax(staking_income, deductions)
        mine = self.calculate_income_tax(mining_income, deductions)
        income = self.calculate_income_tax(gross_income, deductions)

        total = (
            st["capital_gains_tax"]
            + lt["capital_gains_tax"]
            + stk["income_tax"]
            + mine["income_tax"]
            + income["income_tax"]
        )

        return {
            "jurisdiction": "US",
            "tax_year": 2025,
            "filing_status": filing_status,
            "magi": round(magi, 2),
            "standard_deduction_applied": std_deduction if use_standard_deduction else 0,
            "breakdown": {
                "short_term_gains_tax": st,
                "long_term_gains_tax": lt,
                "staking_income_tax": stk,
                "mining_income_tax": mine,
                "employment_income_tax": income,
            },
            "total_federal_tax": round(total, 2),
            "effective_rate": round(total / magi, 4) if magi > 0 else 0,
            "forms_needed": ["Form 1040", "Form 8949", "Schedule D"],
            "notes": [
                "Short-term gains taxed as ordinary income (10%–37%)",
                "Long-term gains taxed at 0%, 15%, or 20%",
                "Staking/mining = ordinary income at FMV on receipt",
                "3.8% NIIT may apply if MAGI > $200k (single) / $250k (MFJ)",
                "Wash-sale rule does NOT apply to crypto in 2025",
                "Report disposals on Form 8949 + Schedule D",
            ],
        }


__all__ = ["TaxCalculator"]
