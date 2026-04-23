from .config import Bolivia
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Bolivia-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Bolivia())


__all__ = ["TaxCalculator"]
