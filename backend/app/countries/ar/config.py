"""Argentina — ARCA (ex-AFIP) 2026
Sources:
  - Ley 27.743/2024 (Medidas Fiscales Paliativas) — nuevo mínimo no imponible
  - Decreto 608/2024 + ARCA Res. 5.546/2025 — bracket update (IPC-indexed)
  - RG ARCA 5.616/2025 — crypto/activos digitales reporting obligatorio
Changes 2026: MNI raised ~140% (inflation adjustment); crypto still 15% cedular
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Argentina(SouthAmericaBase):
    country_code = "AR"
    country_name = "Argentina"
    currency = "ARS"
    currency_symbol = "$"
    tax_authority = "ARCA"
    tax_authority_url = "https://www.arca.gob.ar"
    filing_deadline_full = "June 30"
    filing_deadline_month_day = "06-30"
    tax_year = 2026
    taxpayer_id_format = "CUIT/CUIL (11 digits)"
    taxpayer_id_regex = r"^\d{11}$"
    taxpayer_id_length = 11

    def get_tax_rates(self) -> Dict:
        """Art. 94 LIG — 9 brackets indexed by IPC to June 2026 estimate"""
        return {
            "income": [
                TaxBracket(0,                        Decimal("3000000"),   Decimal("0")),
                TaxBracket(Decimal("3000000"),        Decimal("4200000"),   Decimal("0.05")),
                TaxBracket(Decimal("4200000"),        Decimal("8400000"),   Decimal("0.09")),
                TaxBracket(Decimal("8400000"),        Decimal("12600000"),  Decimal("0.12")),
                TaxBracket(Decimal("12600000"),       Decimal("16800000"),  Decimal("0.15")),
                TaxBracket(Decimal("16800000"),       Decimal("25200000"),  Decimal("0.19")),
                TaxBracket(Decimal("25200000"),       Decimal("33600000"),  Decimal("0.23")),
                TaxBracket(Decimal("33600000"),       Decimal("50400000"),  Decimal("0.27")),
                TaxBracket(Decimal("50400000"),       Decimal("67200000"),  Decimal("0.31")),
                TaxBracket(Decimal("67200000"),       float("inf"),         Decimal("0.35")),
            ],
            "capital_gains": Decimal("0.15"),   # Impuesto Cedular (art. 98 LIG)
            "vat":           Decimal("0.21"),
            "crypto":        Decimal("0.15"),   # Activos digitales = cedular 15%
            "dividends":     Decimal("0.07"),
            "staking_income":Decimal("0.15"),
        }

    def get_deductions(self) -> Dict:
        return {
            "minimo_no_imponible": DeductionRule("minimo_no_imponible", Decimal("1.00"), max_amount=float("inf")),
            "health":              DeductionRule("health",              Decimal("1.00"), max_amount=float("inf")),
            "education":           DeductionRule("education",           Decimal("1.00"), max_amount=float("inf")),
            "charity":             DeductionRule("charity",             Decimal("0.05"), max_amount=float("inf")),
            "trading_fees":        DeductionRule("trading_fees",        Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "F-711":  TaxForm("F-711",  "Ganancias Personas Humanas",      "June 30",  True,  []),
            "F-2002": TaxForm("F-2002", "IVA Mensual",                     "Monthly",  False, ["has_vat_obligation"]),
            "BIENES": TaxForm("BIENES", "Bienes Personales (patrimonio)",   "June 30",  False, ["has_wealth_over_threshold"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and len(taxpayer_id) == 11 and taxpayer_id.isdigit()

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"${val:,.0f} ARS" if symbol else f"{val:,.0f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name,
            "region": self.country_region, "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority,
            "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full,
            "filing_frequency": "yearly", "fiscal_year": "calendar",
            "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains",
            "crypto_reporting_mandatory": True,
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Southern Cone", "LATAM Tax Network"],
        }
