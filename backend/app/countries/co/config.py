from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Colombia(SouthAmericaBase):
    """Colombia Tax Jurisdiction - Art. 241 ET (2025/2026)
    UVT 2025 = $49,799 COP / UVT 2026 = $52,374 COP
    Source: DIAN / Estatuto Tributario art. 241
    """
    country_code = "CO"
    country_name = "Colombia"
    currency = "COP"
    tax_authority = "DIAN"
    filing_deadline_full = "April 10"
    
    # UVT 2026 value for bracket calculation
    _UVT = Decimal("52374")
    
    def get_tax_rates(self) -> Dict:
        """Art. 241 ET progressive rates (7 brackets)
        Brackets in COP using UVT 2026 = $52,374"""
        uvt = self._UVT
        return {
            "income": [
                TaxBracket(0,                       int(uvt * 1090),     Decimal("0")),      # 0%
                TaxBracket(int(uvt * 1090),          int(uvt * 1700),     Decimal("0.19")),   # 19%
                TaxBracket(int(uvt * 1700),          int(uvt * 4100),     Decimal("0.28")),   # 28%
                TaxBracket(int(uvt * 4100),          int(uvt * 8670),     Decimal("0.33")),   # 33%
                TaxBracket(int(uvt * 8670),          int(uvt * 18970),    Decimal("0.35")),   # 35%
                TaxBracket(int(uvt * 18970),         int(uvt * 31000),    Decimal("0.37")),   # 37%
                TaxBracket(int(uvt * 31000),         float("inf"),        Decimal("0.39")),   # 39%
            ],
            "capital_gains": Decimal("0.15"),   # Occasional gains rate
            "vat": Decimal("0.19"),
            "crypto": Decimal("0.15"),          # Treated as occasional gain
            "dividends": Decimal("0.10"),       # 10% for residents (up to 1090 UVT)
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.25"), max_amount=float('inf')),  # 25% renta exenta
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "pension": DeductionRule("pension", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "210": TaxForm("210", "Annual Tax Return (Personas Naturales)", "April 10", True, []),
            "300": TaxForm("300", "IVA Declaration", "Bimonthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate NIT (9-10 digits)"""
        if not taxpayer_id or len(taxpayer_id) < 9 or len(taxpayer_id) > 10:
            return False
        return taxpayer_id.isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"${amount:,.0f} COP"
    
    def get_country_info(self) -> Dict:
        return {
            "code": self.country_code,
            "name": self.country_name,
            "currency": self.currency,
            "tax_authority": self.tax_authority,
            "filing_frequency": "yearly",
            "fiscal_year": "calendar",
            "holding_period_distinction": False,
            "vat_applicable": True,
            "crypto_treatment": "occasional_gain",
            "api_available": True,
            "regions": ["South America", "Andean Region", "LATAM Tax Network"],
            "region": "South America",
            "currency_symbol": "$",
        }
