"""Colombia — DIAN 2026 (ET art. 241 + UVT 2026 = $52,374 COP)
Sources:
  - Ley 2294/2023 + DIAN Res. 000187/2025 — UVT 2026 = $52,374
  - ET art. 35 (ganancia ocasional) — crypto = 15% ocasional
  - DIAN Concepto 100208192-1145/2024 — obligación reporte cripto
Changes 2026: UVT ₊5.2% vs 2025; crypto reporting mandatory for exchanges
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Colombia(SouthAmericaBase):
    country_code = "CO"
    country_name = "Colombia"
    currency = "COP"
    currency_symbol = "$"
    tax_authority = "DIAN"
    tax_authority_url = "https://www.dian.gov.co"
    filing_deadline_full = "April 10"
    filing_deadline_month_day = "04-10"
    tax_year = 2026
    _UVT = Decimal("52374")
    taxpayer_id_format = "NIT (9-10 digits)"
    taxpayer_id_regex = r"^\d{9,10}$"
    taxpayer_id_length = 10

    def get_tax_rates(self) -> Dict:
        uvt = self._UVT
        return {
            "income": [
                TaxBracket(0,                  int(uvt * 1090),  Decimal("0")),
                TaxBracket(int(uvt * 1090),    int(uvt * 1700),  Decimal("0.19")),
                TaxBracket(int(uvt * 1700),    int(uvt * 4100),  Decimal("0.28")),
                TaxBracket(int(uvt * 4100),    int(uvt * 8670),  Decimal("0.33")),
                TaxBracket(int(uvt * 8670),    int(uvt * 18970), Decimal("0.35")),
                TaxBracket(int(uvt * 18970),   int(uvt * 31000), Decimal("0.37")),
                TaxBracket(int(uvt * 31000),   float("inf"),     Decimal("0.39")),
            ],
            "capital_gains": Decimal("0.15"),
            "vat":           Decimal("0.19"),
            "crypto":        Decimal("0.15"),   # ganancia ocasional art. 35 ET
            "dividends":     Decimal("0.10"),
            "staking_income":Decimal("0.15"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.25"), max_amount=float("inf")),
            "health":       DeductionRule("health",       Decimal("1.00"), max_amount=float("inf")),
            "pension":      DeductionRule("pension",      Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "210":   TaxForm("210",   "Declaración Renta Personas Naturales", "April 10", True,  []),
            "300":   TaxForm("300",   "IVA Bimestral",                        "Bimonthly",False, ["has_vat"]),
            "CRIPTO":TaxForm("CRIPTO","Reporte Operaciones Cripto (DIAN)",    "Annual",   False, ["has_crypto"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.isdigit() and 9 <= len(taxpayer_id) <= 10

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"${val:,.0f} COP" if symbol else f"{val:,.0f}"

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
            "crypto_treatment": "occasional_gain", "uvt_2026": int(self._UVT),
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
        }
