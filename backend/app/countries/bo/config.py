"""Bolivia — SIN 2026 (RC-IVA flat 13%, SMN 2026 = Bs.2,500/month)
Changes 2026: SMN raised to Bs.2,500; crypto still RC-IVA 13% flat;
Decreto 5.319/2025 requires virtual asset reporting via SIN portal
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Bolivia(SouthAmericaBase):
    country_code = "BO"; country_name = "Bolivia"; currency = "BOB"; currency_symbol = "Bs."
    tax_authority = "SIN"; tax_authority_url = "https://www.impuestos.gob.bo"
    filing_deadline_full = "Quarterly"; filing_deadline_month_day = "04-30"; tax_year = 2026
    taxpayer_id_format = "NIT (10-13 digits)"; taxpayer_id_regex = r"^\d{10,13}$"; taxpayer_id_length = 13

    def get_tax_rates(self) -> Dict:
        return {
            "income": [
                TaxBracket(0, float("inf"), Decimal("0.13")),  # RC-IVA flat 13%
            ],
            "capital_gains": Decimal("0.13"),
            "vat":           Decimal("0.13"),   # IVA nominal 13% (effective ~14.94%)
            "crypto":        Decimal("0.13"),   # Decreto 5.319/2025 — RC-IVA applies
            "dividends":     Decimal("0.13"),
            "staking_income":Decimal("0.13"),
        }

    def get_deductions(self) -> Dict:
        return {
            "invoice_credit":         DeductionRule("invoice_credit",         Decimal("1.00"), max_amount=float("inf")),
            "minimum_wage_allowance": DeductionRule("minimum_wage_allowance", Decimal("1.00"), max_amount=float("inf")),
            "trading_fees":           DeductionRule("trading_fees",           Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "Form-610": TaxForm("Form-610", "RC-IVA Trimestral",          "Quarterly", True,  []),
            "Form-110": TaxForm("Form-110", "Detalle de Facturas",         "Quarterly", False, ["has_deductions"]),
            "VA-SIN":   TaxForm("VA-SIN",   "Reporte Activos Virtuales",   "Annual",    False, ["has_crypto"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.isdigit() and 10 <= len(taxpayer_id) <= 13

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"Bs. {val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "quarterly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "rc_iva", "smn_2026_bob": 2500,
            "api_available": False, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
        }
