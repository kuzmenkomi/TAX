"""Ecuador — SRI 2026 (NAC-DGERCGC25-00000038, IVA 15%, FBU $12,792)
Changes 2026: free base up to $12,792; IVA stays 15%; crypto ordinary income
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Ecuador(SouthAmericaBase):
    country_code = "EC"; country_name = "Ecuador"; currency = "USD"; currency_symbol = "$"
    tax_authority = "SRI"; tax_authority_url = "https://www.sri.gob.ec"
    filing_deadline_full = "March 28"; filing_deadline_month_day = "03-28"; tax_year = 2026
    taxpayer_id_format = "RUC (13) / Cédula (10)"; taxpayer_id_regex = r"^\d{10,13}$"; taxpayer_id_length = 13

    def get_tax_rates(self) -> Dict:
        return {
            "income": [
                TaxBracket(0,                    Decimal("12081"),  Decimal("0")),
                TaxBracket(Decimal("12081"),      Decimal("15387"),  Decimal("0.05")),
                TaxBracket(Decimal("15387"),      Decimal("19978"),  Decimal("0.10")),
                TaxBracket(Decimal("19978"),      Decimal("26422"),  Decimal("0.12")),
                TaxBracket(Decimal("26422"),      Decimal("34771"),  Decimal("0.15")),
                TaxBracket(Decimal("34771"),      Decimal("46051"),  Decimal("0.20")),
                TaxBracket(Decimal("46051"),      Decimal("61311"),  Decimal("0.25")),
                TaxBracket(Decimal("61311"),      Decimal("81671"),  Decimal("0.30")),
                TaxBracket(Decimal("81671"),      Decimal("108701"), Decimal("0.35")),
                TaxBracket(Decimal("108701"),     float("inf"),      Decimal("0.37")),
            ],
            "capital_gains": Decimal("0.10"), "vat": Decimal("0.15"),
            "crypto": Decimal("0.37"), "dividends": Decimal("0.10"), "staking_income": Decimal("0.37"),
        }

    def get_deductions(self) -> Dict:
        return {
            "personal_expenses": DeductionRule("personal_expenses", Decimal("1.00"), max_amount=Decimal("16200")),
            "health":            DeductionRule("health",            Decimal("1.00"), max_amount=float("inf")),
            "trading_fees":      DeductionRule("trading_fees",      Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "102": TaxForm("102", "Declaración IR Personas Naturales", "March 28", True,  []),
            "104": TaxForm("104", "IVA Mensual/Semestral",              "Monthly",  False, ["has_vat"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.isdigit() and len(taxpayer_id) in (10, 13)

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"${val:,.2f} USD" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "ordinary_income", "vat_rate_2026": "15%",
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
        }
