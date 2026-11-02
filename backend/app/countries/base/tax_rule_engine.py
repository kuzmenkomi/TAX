"""
Two-Layer Tax Architecture
==========================

Layer A  — Transaction Data (ALWAYS historical, NEVER modified)
    • Prices, amounts, dates, costs are taken at the moment of the transaction
    • PnL is calculated on historical actuals
    • This layer is IMMUTABLE — the past cannot change

Layer B  — Tax Rules (ALWAYS the latest enacted rules)
    • We store the CURRENT year's rules for each country
    • These rules are applied to Layer A data regardless of which tax_year the
      user is filing for
    • Example: user files for 2024 in 2026 → we apply 2026 rules to 2024 data
      (this is generally correct: tax authorities use the rules current at
       filing time, not at transaction time, for capital gains classification)

Usage
-----
    from app.countries.base.tax_rule_engine import TaxRuleEngine

    result = TaxRuleEngine.apply(
        country_code="BR",
        transactions=[...],          # Layer A: raw historical data
        tax_year=2024,               # which calendar year to filter
        accounting_method="FIFO",
    )
    # result["rules_version"] will tell the frontend which rule set was used
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.countries.registries.country_registry import CountryRegistry


class TaxRuleEngine:
    """
    Central engine that separates data (Layer A) from rules (Layer B).

    All tax calculation endpoints should use this class instead of calling
    CountryRegistry.get_calculator() directly, so the version metadata is
    always attached to every result.
    """

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @classmethod
    def apply(
        cls,
        country_code: str,
        tax_year: int,
        capital_gains: float = 0.0,
        staking_income: float = 0.0,
        mining_income: float = 0.0,
        gross_income: float = 0.0,
        holding_period_days: int = 366,
        accounting_method: str = "FIFO",
        filing_status: str = "single",
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Apply the CURRENT (2026) tax rules of *country_code* to the
        pre-computed P&L figures that come from historical Layer-A data.

        Parameters
        ----------
        country_code       : ISO-2 country code ("BR", "US", "MX", …)
        tax_year           : The year the user is FILING for (data filter)
        capital_gains      : Realised gains from Layer-A PnL engine
        staking_income     : Income from staking (Layer A)
        mining_income      : Income from mining (Layer A)
        gross_income       : Other ordinary income (Layer A)
        holding_period_days: Average / predominant holding period for the
                             gains (used by US short/long-term split)
        accounting_method  : FIFO / LIFO / HIFO / AVCO (applied in Layer A)
        filing_status      : "single" | "mfj" | "hoh" (relevant for US)
        extra              : Country-specific optional parameters

        Returns
        -------
        dict with:
            tax_year         – year being filed
            rules_version    – year of tax rules applied ("2026")
            country          – country code
            accounting_method– method used in Layer A
            layer_a_summary  – raw income/gains passed in
            layer_b_result   – tax calculation output from country calculator
            applied_at       – UTC timestamp
        """
        code = country_code.upper()
        calculator = CountryRegistry.get_calculator(code)
        country    = CountryRegistry.get_country(code)

        # -- Layer A summary (immutable historical facts) --
        layer_a: Dict[str, Any] = {
            "tax_year":           tax_year,
            "capital_gains":      capital_gains,
            "staking_income":     staking_income,
            "mining_income":      mining_income,
            "gross_income":       gross_income,
            "holding_period_days": holding_period_days,
            "accounting_method":  accounting_method,
        }

        # -- Layer B: apply current rules --
        if hasattr(calculator, "calculate_us_crypto_summary"):
            # US-specific path with short/long-term distinction
            layer_b = calculator.calculate_us_crypto_summary(
                short_term_gains=capital_gains if holding_period_days <= 365 else 0.0,
                long_term_gains=capital_gains  if holding_period_days > 365  else 0.0,
                staking_income=staking_income,
                mining_income=mining_income,
                gross_income=gross_income,
                filing_status=filing_status,
            )
        else:
            # Generic path for all LATAM countries
            layer_b = calculator.calculate_total_tax_liability(
                gross_income=gross_income,
                capital_gains=capital_gains,
                crypto_activity={
                    "crypto_gains": capital_gains,
                    "staking_income": staking_income,
                    "mining_income": mining_income,
                },
                deductions={},
            )

        info = country.get_country_info()

        return {
            "tax_year":        tax_year,
            "rules_version":   str(country.tax_year),   # always current
            "country":         code,
            "country_name":    info.get("name", code),
            "currency":        info.get("currency", "USD"),
            "accounting_method": accounting_method,
            "layer_a_summary": layer_a,
            "layer_b_result":  layer_b,
            "applied_at":      datetime.utcnow().isoformat() + "Z",
            "note": (
                f"Tax rules applied are {country.tax_year} (current). "
                f"Transaction data is from {tax_year} (historical Layer A). "
                "This is the correct approach: rules in force at filing time "
                "are applied to historical transaction data."
            ),
        }

    @classmethod
    def get_rule_version(cls, country_code: str) -> str:
        """Return the tax rule year currently in use for a country."""
        country = CountryRegistry.get_country(country_code.upper())
        return str(country.tax_year)

    @classmethod
    def list_rule_versions(cls) -> Dict[str, str]:
        """Return {country_code: rule_year} for all registered countries."""
        return {
            code: cls.get_rule_version(code)
            for code in CountryRegistry.list_codes()
        }
