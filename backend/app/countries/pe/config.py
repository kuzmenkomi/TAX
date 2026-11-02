"""Peru — SUNAT 2026 (UIT 2026 = S/ 5,350 confirmed by D.S. 410-2025-EF)"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Peru(SouthAmericaBase):
    country_code = "PE"; country_name = "Peru"; currency = "PEN"; currency_symbol = "S/."
    tax_authority = "SUNAT"; tax_authority_url = "https://www.sunat.gob.pe"
    filing_deadline_full = "April 15"; filing_deadline_month_day = "04-15"; tax_year = 2026
    _UIT = Decimal("5550")
    taxpayer_id_format = "RUC (11) / DNI (8)"; taxpayer_id_regex = r"^\d{8,11}$"; taxpayer_id_length = 11

    def get_tax_rates(self) -> Dict:
        uit = self._UIT; exempt = uit * 7
        return {
            "income": [
                TaxBracket(0,                      int(exempt),           Decimal("0")),
                TaxBracket(int(exempt),             int(exempt+uit*5),     Decimal("0.08")),
                TaxBracket(int(exempt+uit*5),       int(exempt+uit*20),    Decimal("0.14")),
                TaxBracket(int(exempt+uit*20),      int(exempt+uit*35),    Decimal("0.17")),
                TaxBracket(int(exempt+uit*35),      int(exempt+uit*45),    Decimal("0.20")),
                TaxBracket(int(exempt+uit*45),      float("inf"),          Decimal("0.30")),
            ],
            "capital_gains": Decimal("0.05"), "vat": Decimal("0.18"),
            "crypto": Decimal("0.30"), "dividends": Decimal("0.05"), "staking_income": Decimal("0.30"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.20"), max_amount=float("inf")),
            "AFP":          DeductionRule("AFP",          Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "709": TaxForm("709", "Declaración Anual IR",  "April 15", True,  []),
            "621": TaxForm("621", "IGV-Renta Mensual",     "Monthly",  False, ["has_business"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.isdigit() and len(taxpayer_id) in (8, 11)

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"S/. {val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "ordinary_income", "uit_2026": int(self._UIT),
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
        }
