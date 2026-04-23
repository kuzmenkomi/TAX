from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Argentina(SouthAmericaBase):
    """Argentina Tax Jurisdiction - Impuesto a las Ganancias 2025/2026
    Source: ARCA (ex-AFIP), Art 94 LIG. 
    Progressive from 5% to 35% in 9 brackets.
    """
    country_code = "AR"
    country_name = "Argentina"
    currency = "ARS"
    tax_authority = "ARCA"  # Replaced AFIP
    filing_deadline_full = "June 30"
    
    def get_tax_rates(self) -> Dict:
        """Progressive brackets (Art. 94) - 9 brackets from 5% to 35%
        Values are approximations for 2025/2026 given hyperinflation updates.
        """
        # Note: Actual bounds update semiannually via IPC.
        # These represent the 9-bracket structure.
        return {
            "income": [
                TaxBracket(0,                       Decimal("3000000"),    Decimal("0")),      # Mínimo no imponible
                TaxBracket(Decimal("3000000"),       Decimal("4200000"),    Decimal("0.05")),   # 5%
                TaxBracket(Decimal("4200000"),       Decimal("8400000"),    Decimal("0.09")),   # 9%
                TaxBracket(Decimal("8400000"),       Decimal("12600000"),   Decimal("0.12")),   # 12%
                TaxBracket(Decimal("12600000"),      Decimal("16800000"),   Decimal("0.15")),   # 15%
                TaxBracket(Decimal("16800000"),      Decimal("25200000"),   Decimal("0.19")),   # 19%
                TaxBracket(Decimal("25200000"),      Decimal("33600000"),   Decimal("0.23")),   # 23%
                TaxBracket(Decimal("33600000"),      Decimal("50400000"),   Decimal("0.27")),   # 27%
                TaxBracket(Decimal("50400000"),      Decimal("67200000"),   Decimal("0.31")),   # 31%
                TaxBracket(Decimal("67200000"),      float("inf"),          Decimal("0.35")),   # 35%
            ],
            "capital_gains": Decimal("0.15"),   # 15% (Impuesto Cedular)
            "vat": Decimal("0.21"),             # 21% General
            "crypto": Decimal("0.15"),          # Treated as capital gains (cedular)
            "dividends": Decimal("0.07"),       # 7%
        }
    
    def get_deductions(self) -> Dict:
        return {
            "minimo_no_imponible": DeductionRule("minimo_no_imponible", Decimal("1.00"), max_amount=float('inf')), # Deducciones personales art 30
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')), # Prepaga
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "charity": DeductionRule("charity", Decimal("0.05"), max_amount=float('inf')), # 5% of net profit
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "F-711": TaxForm("F-711", "Annual Ganancias Personas Humanas", "June 30", True, []),
            "F-2002": TaxForm("F-2002", "Monthly VAT", "Monthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate CUIT/CUIL (11 digits)"""
        if not taxpayer_id or len(taxpayer_id) != 11:
            return False
        return taxpayer_id.isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"${amount:,.2f} ARS"
    
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
            "crypto_treatment": "capital_gains",
            "api_available": True,
            "regions": ["South America", "Latin America", "LATAM Tax Network"],
            "region": "South America",
            "currency_symbol": "$",
        }
