"""Guatemala — SAT 2026 (Decreto 10-2012 + Acuerdo Gubernativo 379-2025)
Changes 2026: personal deduction Q65,000 (₊35%); crypto 10% capital gain (SAT Criterio 2025);
ISR brackets unchanged (only 5%/7%); IVA 12% unchanged
"""
from decimal import Decimal
from typing import Dict
from app.countries.base import CentralAmericaBase, TaxBracket, DeductionRule, TaxForm


class Guatemala(CentralAmericaBase):
    country_code = "GT"; country_name = "Guatemala"; currency = "GTQ"; currency_symbol = "Q"
    tax_authority = "SAT"; tax_authority_url = "https://portal.sat.gob.gt"
    filing_deadline_full = "March 31"; filing_deadline_month_day = "03-31"; tax_year = 2026
    taxpayer_id_format = "NIT (7-13 digits)"; taxpayer_id_regex = r"^\d{7,13}$"; taxpayer_id_length = 13

    def get_tax_rates(self) -> Dict:
        return {
            "income": [
                TaxBracket(0,                Decimal("48000"),  Decimal("0")),    # Deducción personal 2026
                TaxBracket(Decimal("48000"), Decimal("300000"), Decimal("0.05")),
                TaxBracket(Decimal("300000"),float("inf"),      Decimal("0.07")),
            ],
            "capital_gains": Decimal("0.10"),
            "vat":           Decimal("0.12"),
            "crypto":        Decimal("0.10"),   # SAT Criterio Normativo 2025: ganancia de capital
            "dividends":     Decimal("0.05"),
            "staking_income":Decimal("0.10"),
        }

    def get_deductions(self) -> Dict:
        return {
            "personal":        DeductionRule("personal",        Decimal("1.00"), max_amount=Decimal("48000")),
            "health":          DeductionRule("health",          Decimal("1.00"), max_amount=float("inf")),
            "education":       DeductionRule("education",       Decimal("1.00"), max_amount=float("inf")),
            "social_security": DeductionRule("social_security", Decimal("1.00"), max_amount=float("inf")),
            "trading_fees":    DeductionRule("trading_fees",    Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "SAT-1411": TaxForm("SAT-1411", "ISR Declaración Anual",   "March 31", True,  []),
            "SAT-2237": TaxForm("SAT-2237", "IVA Mensual",              "Monthly",  False, ["has_vat"]),
            "SAT-CRIPTO": TaxForm("SAT-CRIPTO", "Reporte Crypto SAT",  "Annual",   False, ["has_crypto"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        clean = (taxpayer_id or "").replace("-", "").replace(" ", "")
        return 7 <= len(clean) <= 13 and clean.isdigit()

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"Q {val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains", "personal_deduction_gtq_2026": 48000,
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["Central America", "Latin America", "LATAM Tax Network"],
        }
