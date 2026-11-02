"""Uruguay — DGI 2026 (IRPF + BPC 2026 = $7,115 UYU, Ley 20.212/2023)
Changes 2026: BPC ₊8.6% wage adjustment; crypto IRPF cat. II (12% IRNR/12% IRPF)
"""
from decimal import Decimal
from typing import Dict
from ..base.definitions import TaxBracket, DeductionRule, TaxForm, SouthAmericaBase


class Uruguay(SouthAmericaBase):
    country_code = "UY"; country_name = "Uruguay"; currency = "UYU"; currency_symbol = "$U"
    tax_authority = "DGI"; tax_authority_url = "https://www.dgi.gub.uy"
    filing_deadline_full = "April 30"; filing_deadline_month_day = "04-30"; tax_year = 2026
    _BPC = Decimal("6550")
    taxpayer_id_format = "CI (8) / RUT (12)"; taxpayer_id_regex = r"^\d{8,12}$"; taxpayer_id_length = 12

    def get_tax_rates(self) -> Dict:
        bpc = self._BPC
        return {
            "income": [
                TaxBracket(0,                    int(bpc*84),   Decimal("0")),
                TaxBracket(int(bpc*84),           int(bpc*120),  Decimal("0.10")),
                TaxBracket(int(bpc*120),          int(bpc*180),  Decimal("0.15")),
                TaxBracket(int(bpc*180),          int(bpc*360),  Decimal("0.24")),
                TaxBracket(int(bpc*360),          int(bpc*600),  Decimal("0.25")),
                TaxBracket(int(bpc*600),          int(bpc*900),  Decimal("0.27")),
                TaxBracket(int(bpc*900),          int(bpc*1380), Decimal("0.31")),
                TaxBracket(int(bpc*1380),         float("inf"),  Decimal("0.36")),
            ],
            "capital_gains": Decimal("0.12"), "vat": Decimal("0.22"),
            "crypto": Decimal("0.12"),  # IRPF Categoría II / IRNR
            "dividends": Decimal("0.07"), "staking_income": Decimal("0.12"),
        }

    def get_deductions(self) -> Dict:
        return {
            "standard":     DeductionRule("standard",     Decimal("0.10"), max_amount=float("inf")),
            "health":       DeductionRule("health",       Decimal("1.00"), max_amount=float("inf")),
            "pension":      DeductionRule("pension",      Decimal("1.00"), max_amount=float("inf")),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float("inf")),
        }

    def get_tax_forms(self) -> Dict:
        return {
            "M3":  TaxForm("M3",  "IRPF Declaración Anual", "April 30", True,  []),
            "IVA": TaxForm("IVA", "IVA Mensual",             "Monthly",  False, ["has_vat"]),
        }

    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        return bool(taxpayer_id) and taxpayer_id.isdigit() and len(taxpayer_id) in (8, 12)

    def format_currency(self, amount, symbol: bool = True) -> str:
        val = float(amount) if amount else 0.0
        return f"$U {val:,.2f}" if symbol else f"{val:,.2f}"

    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code, "name": self.country_name, "region": self.country_region,
            "currency": self.currency, "currency_symbol": self.currency_symbol,
            "tax_authority": self.tax_authority, "tax_authority_url": self.tax_authority_url,
            "filing_deadline": self.filing_deadline_full, "filing_frequency": "yearly",
            "fiscal_year": "calendar", "holding_period_distinction": False, "vat_applicable": True,
            "crypto_treatment": "capital_gains", "bpc_2026": int(self._BPC),
            "api_available": True, "forms_required": self.get_tax_forms(),
            "regions": ["South America", "Southern Cone", "LATAM Tax Network"],
        }
