"""Costa Rica — Hacienda 2026 (Decreto 44.450-H, tranches adjusted Jan 2026)
Changes 2026: Income brackets ₊4.8% IPCM; crypto capital gains 15%; VAT 13% unchanged
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, CentralAmericaBase


class CostaRica(CentralAmericaBase):
    country_code = "CR"; country_name = "Costa Rica"; currency = "CRC"; currency_symbol = "₡"
    tax_authority = "Hacienda"; tax_authority_url = "https://www.hacienda.go.cr"
    filing_deadline_full = "April 15"; filing_deadline_month_day = "04-15"; tax_year = 2026
    taxpayer_id_format = "Cédula (10 digits)"; taxpayer_id_regex = r"^\d{10}$"; taxpayer_id_length = 10

    def get_tax_rates(self) -> Dict:
        return {
            "income": [
                TaxBracket(0,          11292000, Decimal("0")),
                TaxBracket(11292000,   16578000, Decimal("0.10")),
                TaxBracket(16578000,   29071000, Decimal("0.15")),
                TaxBracket(29071000,   58143000, Decimal("0.20")),
                TaxBracket(58143000,   float("inf"), Decimal("0.25")),
            ],
            "capital_gains": Decimal("0.15"), "vat": Decimal("0.13"),
            "crypto": Decimal("0.15"), "dividends": Decimal("0.15"), "staking_income": Decimal("0.15"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.10"), max_amount=float("inf")),
            "health":       DeductionRule("health",       Decimal("1.00"), max_amount=float("inf")),
            "education":    DeductionRule("education",    Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "D101": TaxForm("D101", "Declaración Renta Anual", "April 15", True,  []),
            "D104": TaxForm("D104", "Declaración IVA",          "Monthly",  False, ["has_vat"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.replace("-", "").isdigit() and len(taxpayer_id.replace("-", "")) == 10

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"₡{val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains", "api_available": False,
            "forms_required": self.get_tax_forms(),
            "regions": ["Central America", "LATAM Tax Network"],
        }
