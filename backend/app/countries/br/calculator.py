from .config import Brazil
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Brazil-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Brazil())
    
    def calculate_irpf(self, income: float, deductions: float = 0) -> float:
        """Calculate IRPF (tax) for Brazil"""
        return self.calculate_income_tax(income, deductions)


__all__ = ["TaxCalculator"]
