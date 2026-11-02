"""Mexico — SAT 2026 (ISR art.152 LISR + Anexo 8 RMF 2026)
Sources:
  - DOF 28/12/2025 — RMF 2026 Anexo 8 (nueva tabla ISR anual)
  - SAT Regla 3.11.14 RMF 2026 — cripto como ingreso acumulable
  - SAT Criterio Normativo 2024 — exchanges obligados a reportar desde 2025
Changes 2026: brackets inflated by INPC; crypto reporting via DIOT obligatorio
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, NorthAmericaBase


class Mexico(NorthAmericaBase):
    country_code = "MX"
    country_name = "Mexico"
    currency = "MXN"
    currency_symbol = "$"
    tax_authority = "SAT"
    tax_authority_url = "https://www.sat.gob.mx"
    filing_deadline_full = "April 30"
    filing_deadline_month_day = "04-30"
    tax_year = 2026
    taxpayer_id_format = "RFC (13 chars)"
    taxpayer_id_regex = r"^[A-Z]{3,6}\d{6}[A-Z0-9]{1,3}$"
    taxpayer_id_length = 13

    def get_tax_rates(self) -> Dict:
        """ISR art. 152 LISR — 11 brackets RMF 2026"""
        return {
            "income": [
                TaxBracket(Decimal("0"),          Decimal("8952.49"),   Decimal("0.0192")),
                TaxBracket(Decimal("8952.49"),     Decimal("75984.55"),  Decimal("0.0640")),
                TaxBracket(Decimal("75984.55"),    Decimal("133536.07"), Decimal("0.1088")),
                TaxBracket(Decimal("133536.07"),   Decimal("155229.80"), Decimal("0.1600")),
                TaxBracket(Decimal("155229.80"),   Decimal("185852.57"), Decimal("0.1792")),
                TaxBracket(Decimal("185852.57"),   Decimal("374837.88"), Decimal("0.2136")),
                TaxBracket(Decimal("374837.88"),   Decimal("590795.99"), Decimal("0.2352")),
                TaxBracket(Decimal("590795.99"),   Decimal("1127926.22"),Decimal("0.3000")),
                TaxBracket(Decimal("1127926.22"),  Decimal("1503902.46"),Decimal("0.3200")),
                TaxBracket(Decimal("1503902.46"),  Decimal("4511707.37"),Decimal("0.3400")),
                TaxBracket(Decimal("4511707.37"),  float("inf"),         Decimal("0.3500")),
            ],
            "capital_gains": Decimal("0.10"),
            "vat":           Decimal("0.16"),
            "crypto":        Decimal("0.35"),   # ingreso acumulable — top marginal
            "dividends":     Decimal("0.10"),
            "staking_income":Decimal("0.35"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":         DeductionRule("standard",         Decimal("0.08"), max_amount=Decimal("10000")),
            "health_insurance": DeductionRule("health_insurance", Decimal("1.00"), max_amount=float("inf")),
            "housing":          DeductionRule("housing",          Decimal("0.20"), max_amount=Decimal("150000")),
            "education":        DeductionRule("education",        Decimal("1.00"), max_amount=float("inf")),
            "trading_fees":     DeductionRule("trading_fees",     Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "ANUAL":  TaxForm("DECLARACIÓN ANUAL", "Annual Income Declaration", "April 30", True,  []),
            "DIOT":   TaxForm("DIOT",              "Declaración Informativa de Ops. con Terceros (crypto)", "Monthly", False, ["has_crypto"]),
            "ANEXO8": TaxForm("ANEXO 8",           "Capital Gains Schedule",    "April 30", False, ["has_capital_gains"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        import re
        return bool(re.match(self.taxpayer_id_regex, taxpayer_id or ""))

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"${val:,.2f} MXN" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name,
            "region": self.country_region, "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority,
            "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full,
            "filing_frequency": "yearly", "fiscal_year": "calendar",
            "holding_period_distinction": True, "vat_applicable": True,
            "crypto_treatment": "ordinary_income",
            "crypto_reporting_via_diot": True,
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["North America", "Latin America", "LATAM Tax Network"],
        }
