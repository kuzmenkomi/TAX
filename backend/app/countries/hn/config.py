"""Honduras — SAR 2026 (ISR, exempt threshold L228,369 per inflation decree 2025)
Changes 2026: exempt bracket ₊5%; crypto 10% capital gain; ISV 15% unchanged
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, CentralAmericaBase


class Honduras(CentralAmericaBase):
    country_code = "HN"; country_name = "Honduras"; currency = "HNL"; currency_symbol = "L"
    tax_authority = "SAR"; tax_authority_url = "https://www.sar.gob.hn"
    filing_deadline_full = "April 30"; filing_deadline_month_day = "04-30"; tax_year = 2026
    taxpayer_id_format = "RTN (14 digits)"; taxpayer_id_regex = r"^\d{14}$"; taxpayer_id_length = 14

    def get_tax_rates(self) -> Dict:
        return {
            "income": [
                TaxBracket(0,                    Decimal("217493.16"),Decimal("0")),
                TaxBracket(Decimal("217493.16"),  Decimal("331505.86"),Decimal("0.15")),
                TaxBracket(Decimal("331505.86"),  Decimal("770943.86"),Decimal("0.20")),
                TaxBracket(Decimal("770943.86"),  float("inf"),        Decimal("0.25")),
            ],
            "capital_gains": Decimal("0.10"), "vat": Decimal("0.15"),
            "crypto": Decimal("0.10"), "dividends": Decimal("0.10"), "staking_income": Decimal("0.10"),
        }

    def get_deductions(self) -> Dict:
        return {
            "medical":      DeductionRule("medical",      Decimal("1.00"), max_amount=Decimal("40000")),
            "education":    DeductionRule("education",    Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "SAR-272": TaxForm("SAR-272", "Declaración Anual ISR", "April 30", True,  []),
            "SAR-200": TaxForm("SAR-200", "ISV Mensual",            "Monthly",  False, ["has_vat"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        clean = (taxpayer_id or "").replace("-", "")
        return len(clean) == 14 and clean.isdigit()

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"L{val:,.2f}" if symbol else f"{val:,.2f}"

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
