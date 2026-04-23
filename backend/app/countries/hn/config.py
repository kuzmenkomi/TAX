from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm
from typing import Dict

class Honduras(BaseCountryDefinition):
    """Honduras Tax Jurisdiction - ISR 2025
    Source: SAR table generated from 2024 inflation
    """
    country_code = "HN"
    country_name = "Honduras"
    currency = "HNL"
    tax_authority = "SAR"
    filing_deadline_full = "April 30"
    region = "Central America"
    
    def get_tax_rates(self) -> Dict:
        """ISR progressive rates 2025 for individuals
        Includes the exempt bracket up to L217,493.16
        """
        return {
            "income": [
                TaxBracket(0, Decimal("217493.16"), Decimal("0")),                  # Exempt
                TaxBracket(Decimal("217493.16"), Decimal("331638.50"), Decimal("0.15")), # 15%
                TaxBracket(Decimal("331638.50"), Decimal("771252.38"), Decimal("0.20")), # 20%
                TaxBracket(Decimal("771252.38"), float("inf"), Decimal("0.25")),    # 25%
            ],
            "capital_gains": Decimal("0.10"),   # 10% on capital gains
            "vat": Decimal("0.15"),             # ISV (Impuesto Sobre Ventas)
            "crypto": Decimal("0.10"),          # Treated as capital gain
            "dividends": Decimal("0.10"),       # 10% withholding
        }
    
    def get_deductions(self) -> Dict:
        return {
            "medical": DeductionRule("medical", Decimal("1.00"), max_amount=Decimal("40000")), # Standard medical deduction
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "SAR-272": TaxForm("SAR-272", "Annual Income Declaration", "April 30", True, []),
            "SAR-200": TaxForm("SAR-200", "ISV Declaration", "Monthly", False, ["has_vat_obligation"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate RTN (14 digits: 0801-XXXX-XXXXXX format)"""
        if not taxpayer_id:
            return False
        taxpayer_id = taxpayer_id.replace("-", "")
        return len(taxpayer_id) == 14 and taxpayer_id.isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"L{amount:,.2f}"
    
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
            "api_available": False,
            "regions": ["Central America", "LATAM Tax Network"],
            "region": "Central America",
            "currency_symbol": "L",
        }
