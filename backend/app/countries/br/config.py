from decimal import Decimal
from ..base.definitions import BaseCountryDefinition, TaxBracket, DeductionRule, TaxForm, SouthAmericaBase
from typing import Dict

class Brazil(SouthAmericaBase):
    """Brazil Tax Jurisdiction - IRPF 2025/2026
    Source: Receita Federal / MP 1.294/2025 (updated May 2025)
    """
    country_code = "BR"
    country_name = "Brazil"
    currency = "BRL"
    tax_authority = "Receita Federal"
    filing_deadline_full = "April 30"
    
    def get_tax_rates(self) -> Dict:
        """IRPF progressive monthly table (2025/2026)"""
        return {
            "income": [
                TaxBracket(0, Decimal("2259.20"), Decimal("0")),           # Isento
                TaxBracket(Decimal("2259.20"), Decimal("2826.65"), Decimal("0.075")),  # 7.5%
                TaxBracket(Decimal("2826.65"), Decimal("3751.05"), Decimal("0.15")),   # 15%
                TaxBracket(Decimal("3751.05"), Decimal("4664.68"), Decimal("0.225")),  # 22.5%
                TaxBracket(Decimal("4664.68"), float("inf"), Decimal("0.275")),        # 27.5%
            ],
            "capital_gains": Decimal("0.15"),   # 15% flat for individuals
            "vat": Decimal("0.18"),             # ICMS varies by state, avg ~18%
            "crypto": Decimal("0.15"),          # Same as capital gains
            "dividends": Decimal("0"),          # Tax-free for residents
        }
    
    def get_deductions(self) -> Dict:
        return {
            "standard": DeductionRule("standard", Decimal("0.20"), max_amount=Decimal("16754.34")),
            "health": DeductionRule("health", Decimal("1.00"), max_amount=float('inf')),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=Decimal("3561.50")),
            "pension": DeductionRule("pension", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        return {
            "IRPF": TaxForm("IRPF", "Individual Income Declaration", "April 30", True, []),
            "DARF": TaxForm("DARF", "Tax Payment Coupon", "Monthly", False, ["has_estimated_taxes"]),
            "DIMOB": TaxForm("DIMOB", "Real Estate Declaration", "March 31", False, ["has_real_estate"]),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate CPF (11 digits)"""
        if not taxpayer_id or len(taxpayer_id) != 11:
            return False
        return taxpayer_id.isdigit()
    
    def format_currency(self, amount: Decimal) -> str:
        return f"R$ {amount:,.2f}"
    
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
            "forms_required": self.get_tax_forms(),
            "region": "South America",
            "currency_symbol": "R$",
            "regions": ["South America", "Latin America", "LATAM Tax Network"],
        }
