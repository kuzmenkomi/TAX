# Mexico Tax Configuration
# ISR art. 152 Ley del ISR + Anexo 8 RMF 2026
from decimal import Decimal
from typing import Dict, List
from ..base.definitions import (
    BaseCountryDefinition, 
    TaxBracket, 
    DeductionRule, 
    TaxForm,
    NorthAmericaBase
)

class Mexico(NorthAmericaBase):
    """
    Mexico Tax Jurisdiction (2025/2026)
    - ISR: Progressive tax on income (1.92% - 35%) per art. 152 LISR
    - IVA: 16% standard VAT
    - Crypto: Classified as ordinary income (Ingreso Acumulable)
    Source: SAT Anexo 8 RMF 2026 (DOF 28/12/2025)
    """
    
    country_code = "MX"
    country_name = "Mexico"
    currency = "MXN"
    tax_authority = "SAT"
    filing_deadline_full = "April 30"
    filing_deadline_estimated = "June 30"
    
    def get_tax_rates(self) -> Dict:
        """ISR progressive annual rates 2026 (art. 152 LISR)
        11 brackets from 1.92% to 35%"""
        return {
            "income": [
                TaxBracket(Decimal("0"),       Decimal("8952.49"),   Decimal("0.0192")),   # 1.92%
                TaxBracket(Decimal("8952.49"),  Decimal("75984.55"),  Decimal("0.0640")),   # 6.40%
                TaxBracket(Decimal("75984.55"), Decimal("133536.07"), Decimal("0.1088")),   # 10.88%
                TaxBracket(Decimal("133536.07"),Decimal("155229.80"), Decimal("0.16")),     # 16%
                TaxBracket(Decimal("155229.80"),Decimal("185852.57"), Decimal("0.1792")),   # 17.92%
                TaxBracket(Decimal("185852.57"),Decimal("374837.88"), Decimal("0.2136")),   # 21.36%
                TaxBracket(Decimal("374837.88"),Decimal("590795.99"), Decimal("0.2352")),   # 23.52%
                TaxBracket(Decimal("590795.99"),Decimal("1127926.84"),Decimal("0.30")),     # 30%
                TaxBracket(Decimal("1127926.84"),Decimal("1503902.46"),Decimal("0.32")),    # 32%
                TaxBracket(Decimal("1503902.46"),Decimal("4511707.37"),Decimal("0.34")),    # 34%
                TaxBracket(Decimal("4511707.37"),float("inf"),        Decimal("0.35")),     # 35%
            ],
            "capital_gains": Decimal("0.10"),   # 10% on real estate, ordinary for others
            "vat": Decimal("0.16"),
            "crypto": Decimal("0.35"),          # Treated as ordinary income (top marginal)
            "dividends": Decimal("0.10"),
            "interest": Decimal("0.0097"),      # Provisional retention rate
        }
    
    def get_deductions(self) -> Dict:
        """Allowed deductions for Mexican taxpayers"""
        return {
            "standard": DeductionRule("standard", Decimal("0.08"), max_amount=Decimal("10000")),
            "health_insurance": DeductionRule("health_insurance", Decimal("1.00"), max_amount=float('inf')),
            "housing": DeductionRule("housing", Decimal("0.20"), max_amount=Decimal("150000")),
            "education": DeductionRule("education", Decimal("1.00"), max_amount=float('inf')),
            "charitable": DeductionRule("charitable", Decimal("0.15"), max_amount=float('inf')),
            "business_expenses": DeductionRule("business_expenses", Decimal("1.00"), max_amount=float('inf')),
            "trading_fees": DeductionRule("trading_fees", Decimal("1.00"), max_amount=float('inf')),
        }
    
    def get_tax_forms(self) -> Dict:
        """Required tax forms for Mexico"""
        return {
            "F-101": TaxForm(
                code="DECLARACIÓN ANUAL",
                name="Annual Income Declaration",
                deadline="April 30",
                required=True,
                conditions=[]
            ),
            "F-102": TaxForm(
                code="ANEXO 1",
                name="Accumulated Income Schedule",
                deadline="April 30",
                required=True,
                conditions=["has_income"]
            ),
            "F-103": TaxForm(
                code="ANEXO 5",
                name="Deductible Expenses",
                deadline="April 30",
                required=False,
                conditions=["has_business_income"]
            ),
            "F-104": TaxForm(
                code="ANEXO (CAPITAL GAINS)",
                name="Capital Gains Declaration",
                deadline="April 30",
                required=False,
                conditions=["has_capital_gains"]
            ),
        }
    
    def validate_taxpayer_id(self, taxpayer_id: str) -> bool:
        """Validate RFC (Registro Federal de Contribuyentes)"""
        if not taxpayer_id or len(taxpayer_id) != 13:
            return False
        return taxpayer_id[:6].isalpha() and taxpayer_id[6:].isalnum()
    
    def format_currency(self, amount: Decimal) -> str:
        """Format amount in Mexican Pesos"""
        return f"${amount:,.2f} MXN"
    
    def get_country_info(self) -> Dict:
        """Extended country information"""
        return {
            "code": self.country_code,
            "name": self.country_name,
            "currency": self.currency,
            "tax_authority": self.tax_authority,
            "filing_frequency": "yearly",
            "fiscal_year": "calendar",
            "holding_period_distinction": True,
            "vat_applicable": True,
            "crypto_treatment": "ordinary_income",
            "api_available": True,
            "forms_required": self.get_tax_forms(),
            "tax_holidays": [],
            "regions": ["North America", "Latin America", "LATAM Tax Network"],
            "region": "North America",
            "currency_symbol": "$",
        }
