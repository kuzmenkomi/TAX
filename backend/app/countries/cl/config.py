"""Chile — SII 2026 (UTA 2026 = $835,368 CLP, Ley 21.420, Circular 33/2025)"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Chile(SouthAmericaBase):
    country_code = "CL"; country_name = "Chile"; currency = "CLP"; currency_symbol = "$"
    tax_authority = "SII"; tax_authority_url = "https://www.sii.cl"
    filing_deadline_full = "April 30"; filing_deadline_month_day = "04-30"; tax_year = 2026
    taxpayer_id_format = "RUT (9-10 chars)"; taxpayer_id_regex = r"^\d{7,8}-?[\dkK]$"; taxpayer_id_length = 10

    def get_tax_rates(self) -> Dict:
        uta = Decimal("790000")
        return {
            "income": [
                TaxBracket(0,                          int(uta*Decimal("13.5")), Decimal("0")),
                TaxBracket(int(uta*Decimal("13.5")),   int(uta*30),  Decimal("0.04")),
                TaxBracket(int(uta*30),                int(uta*50),  Decimal("0.08")),
                TaxBracket(int(uta*50),                int(uta*70),  Decimal("0.135")),
                TaxBracket(int(uta*70),                int(uta*90),  Decimal("0.23")),
                TaxBracket(int(uta*90),                int(uta*120), Decimal("0.304")),
                TaxBracket(int(uta*120),               int(uta*310), Decimal("0.35")),
                TaxBracket(int(uta*310),               float("inf"), Decimal("0.40")),
            ],
            "capital_gains": Decimal("0.10"), "vat": Decimal("0.19"),
            "crypto": Decimal("0.20"), "dividends": Decimal("0.07"), "staking_income": Decimal("0.20"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.10"), max_amount=float("inf")),
            "health":       DeductionRule("health",       Decimal("0.07"), max_amount=float("inf")),
            "pension":      DeductionRule("pension",      Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "F22":   TaxForm("F22",  "Declaración Anual Renta", "April 30", True,  []),
            "F29":   TaxForm("F29",  "IVA Mensual",              "Monthly",  False, ["has_vat"]),
            "F1929": TaxForm("F1929","Reporte Cripto SII",        "Annual",   False, ["has_crypto"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        import re; return bool(re.match(self.taxpayer_id_regex, taxpayer_id or ""))

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"${val:,.0f} CLP" if symbol else f"{val:,.0f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains", "uta_2026": 835368,
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Southern Cone", "LATAM Tax Network"],
        }
