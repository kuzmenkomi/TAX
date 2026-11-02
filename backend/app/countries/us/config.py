"""
United States Tax Jurisdiction - IRS 2025 (Tax Year 2025)
Sources:
  - IRS Rev. Proc. 2024-61 (2025 inflation adjustments)
  - IRS Notice 2024-57 (Digital Asset / crypto guidance)
  - Infrastructure Investment & Jobs Act 2021 (Section 6050I / broker reporting)
  - IRS Form 1040 Schedule D + Form 8949 (Capital Gains)
  - IRS Notice 2023-34 / IRS Notice 2014-21 (Crypto = property)
  - IRS Q&A on Virtual Currencies (updated March 2025)
  - CAMT / Inflation Reduction Act 2022 (corporate min. tax — not applied here)
"""

from decimal import Decimal
from typing import Dict
from ..base.definitions import (
    BaseCountryDefinition,
    NorthAmericaBase,
    TaxBracket,
    DeductionRule,
    TaxForm,
    TaxType,
)


class UnitedStates(NorthAmericaBase):
    """
    United States Federal Tax Jurisdiction — IRS Tax Year 2025.

    Key crypto rules (latest IRS guidance):
    - Crypto is treated as PROPERTY, not currency (IRS Notice 2014-21, reaffirmed 2025).
    - Every disposal (sale, swap, spend) is a taxable event.
    - Short-term gains (held ≤ 365 days) → taxed as ordinary income.
    - Long-term gains (held > 365 days) → preferential 0%, 15%, or 20% rates.
    - Staking/mining rewards → ordinary income at fair-market value when received.
    - DeFi swaps → taxable at time of swap (IRS 2024 final broker regs).
    - NFT sales → capital gains (collectibles rate 28% may apply for some NFTs).
    - Wash-sale rule does NOT apply to crypto (as of 2025 — no legislation passed).
    - Annual reporting via Form 8949 + Schedule D.
    - Broker reporting expanded to DEX/non-custodial starting 2026 (IRS final regs Dec 2024).
    """

    country_code = "US"
    country_name = "United States"
    currency = "USD"
    currency_symbol = "$"
    tax_authority = "IRS"
    tax_authority_url = "https://www.irs.gov"
    filing_deadline_full = "April 15"
    filing_deadline_month_day = "04-15"
    tax_year = 2026

    # Taxpayer ID (SSN / EIN / ITIN)
    taxpayer_id_format = "SSN/EIN (9 digits)"
    taxpayer_id_regex = r"^\d{9}$"
    taxpayer_id_length = 9

    # IRS has no public real-time filing API (e-File via third parties)
    has_api = False

    # ------------------------------------------------------------------
    # 2025 Standard Deduction (Rev. Proc. 2024-61)
    # ------------------------------------------------------------------
    STANDARD_DEDUCTION_SINGLE = Decimal("15_000")      # Single / MFS
    STANDARD_DEDUCTION_MFJ    = Decimal("30_000")      # Married Filing Jointly
    STANDARD_DEDUCTION_HOH    = Decimal("22_500")      # Head of Household

    # ------------------------------------------------------------------
    # 2025 Ordinary Income Brackets — SINGLE filers (Rev. Proc. 2024-61)
    # ------------------------------------------------------------------
    INCOME_BRACKETS_SINGLE = [
        TaxBracket(0,          11_925,    0.10),
        TaxBracket(11_925,     48_475,    0.12),
        TaxBracket(48_475,    103_350,    0.22),
        TaxBracket(103_350,   197_300,    0.24),
        TaxBracket(197_300,   250_525,    0.32),
        TaxBracket(250_525,   626_350,    0.35),
        TaxBracket(626_350,   float("inf"), 0.37),
    ]

    # 2025 Ordinary Income Brackets — MARRIED FILING JOINTLY
    INCOME_BRACKETS_MFJ = [
        TaxBracket(0,          23_850,    0.10),
        TaxBracket(23_850,     96_950,    0.12),
        TaxBracket(96_950,    206_700,    0.22),
        TaxBracket(206_700,   394_600,    0.24),
        TaxBracket(394_600,   501_050,    0.32),
        TaxBracket(501_050,  751_600,     0.35),
        TaxBracket(751_600,   float("inf"), 0.37),
    ]

    # ------------------------------------------------------------------
    # 2025 Long-Term Capital Gains Brackets — SINGLE filers
    # ------------------------------------------------------------------
    LTCG_BRACKETS_SINGLE = [
        TaxBracket(0,          48_350,    0.00),   # 0%
        TaxBracket(48_350,    533_400,    0.15),   # 15%
        TaxBracket(533_400,   float("inf"), 0.20), # 20%
    ]

    # Net Investment Income Tax (NIIT) — 3.8% on gains above MAGI threshold
    NIIT_RATE = Decimal("0.038")
    NIIT_THRESHOLD_SINGLE = Decimal("200_000")
    NIIT_THRESHOLD_MFJ    = Decimal("250_000")

    # ------------------------------------------------------------------

    def get_tax_rates(self) -> Dict:
        """
        Returns IRS 2025 tax rates.
        INCOME_TAX brackets = single filer (default).
        CAPITAL_GAINS = long-term preferential brackets.
        Short-term gains are ordinary income → use INCOME_TAX brackets.
        """
        return {
            "income": self.INCOME_BRACKETS_SINGLE,
            "capital_gains": self.LTCG_BRACKETS_SINGLE,   # long-term
            "vat": Decimal("0"),                           # USA has no federal VAT
            "crypto_short_term": self.INCOME_BRACKETS_SINGLE,  # ≤365 days
            "crypto_long_term":  self.LTCG_BRACKETS_SINGLE,    # >365 days
            "staking_income":    self.INCOME_BRACKETS_SINGLE,  # ordinary income
            "mining_income":     self.INCOME_BRACKETS_SINGLE,  # ordinary income
            "nft_collectibles":  [TaxBracket(0, float("inf"), 0.28)],  # collectibles rate
        }

    def get_deductions(self) -> Dict:
        return {
            "standard_single": DeductionRule(
                "standard_single",
                rate=None,
                max_amount=float(self.STANDARD_DEDUCTION_SINGLE),
                description="2025 Standard deduction — Single / MFS",
                is_percentage=False,
            ),
            "standard_mfj": DeductionRule(
                "standard_mfj",
                rate=None,
                max_amount=float(self.STANDARD_DEDUCTION_MFJ),
                description="2025 Standard deduction — MFJ",
                is_percentage=False,
            ),
            "standard_hoh": DeductionRule(
                "standard_hoh",
                rate=None,
                max_amount=float(self.STANDARD_DEDUCTION_HOH),
                description="2025 Standard deduction — Head of Household",
                is_percentage=False,
            ),
            "trading_fees": DeductionRule(
                "trading_fees",
                rate=1.0,
                max_amount=float("inf"),
                description="Exchange fees deductible as cost basis adjustment (IRS Notice 2014-21)",
                is_percentage=True,
            ),
            "investment_interest": DeductionRule(
                "investment_interest",
                rate=1.0,
                max_amount=float("inf"),
                description="Investment interest expense (Schedule A)",
                is_percentage=True,
            ),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "1040": TaxForm(
                "1040",
                "U.S. Individual Income Tax Return",
                "April 15",
                True,
                [],
            ),
            "8949": TaxForm(
                "8949",
                "Sales and Other Dispositions of Capital Assets",
                "April 15",
                False,
                ["has_crypto_disposals", "has_stock_sales"],
            ),
            "ScheduleD": TaxForm(
                "ScheduleD",
                "Capital Gains and Losses (Summary)",
                "April 15",
                False,
                ["has_capital_gains"],
            ),
            "ScheduleC": TaxForm(
                "ScheduleC",
                "Profit or Loss From Business (Mining / self-employed staking)",
                "April 15",
                False,
                ["has_mining_income", "is_self_employed"],
            ),
            "1099-DA": TaxForm(
                "1099-DA",
                "Digital Asset Proceeds (new 2025 broker form)",
                "January 31",
                False,
                ["received_from_broker"],
            ),
            "FBAR": TaxForm(
                "FBAR",
                "FinCEN 114 — Foreign Bank Account Report (>$10k offshore)",
                "April 15",
                False,
                ["has_foreign_accounts"],
            ),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate SSN / EIN / ITIN (9 digits, no dashes)."""
        clean = taxpayer_id.replace("-", "").replace(" ", "")
        return len(clean) == 9 and clean.isdigit()

    def format_currency(self, amount, symbol: bool = True) -> str:
        try:
            amt = float(amount)
        except (TypeError, ValueError):
            amt = 0.0
        formatted = f"{amt:,.2f}"
        return f"${formatted}" if symbol else formatted

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code,
            "name": self.country_name,
            "region": self.country_region,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority,
            "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full,
            "filing_frequency": "yearly",
            "fiscal_year": "calendar",
            # Key USA-specific flags
            "holding_period_distinction": True,      # short vs long-term matters
            "short_term_ordinary_income": True,       # short-term = ordinary rates
            "wash_sale_applies_to_crypto": False,     # not yet (2025)
            "niit_applicable": True,                  # 3.8% NIIT on high earners
            "crypto_treatment": "property",           # IRS Notice 2014-21
            "staking_taxable_on_receipt": True,       # Jarrett case settled (2024)
            "defi_swaps_taxable": True,               # IRS final regs Dec 2024
            "broker_reporting_dex": "2026",           # DEX reporting starts 2026
            "vat_applicable": False,
            "api_available": False,
            "forms_required": self.get_tax_forms(),
            "regions": ["North America"],
        }

    # ------------------------------------------------------------------
    # USA-specific helpers
    # ------------------------------------------------------------------

    def calculate_niit(self, net_investment_income: float, magi: float,
                       filing_status: str = "single") -> float:
        """
        3.8% Net Investment Income Tax (IRC §1411).
        Applies when MAGI exceeds threshold.
        Crypto gains count as net investment income.
        """
        threshold = float(
            self.NIIT_THRESHOLD_MFJ if filing_status == "mfj"
            else self.NIIT_THRESHOLD_SINGLE
        )
        if magi <= threshold:
            return 0.0
        excess_magi = magi - threshold
        taxable_nii = min(net_investment_income, excess_magi)
        return round(taxable_nii * float(self.NIIT_RATE), 2)

    def is_long_term(self, holding_period_days: int) -> bool:
        """Return True if holding period qualifies for long-term rates (>365 days)."""
        return holding_period_days > 365
