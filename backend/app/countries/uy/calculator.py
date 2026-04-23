from .config import Uruguay
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Uruguay-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Uruguay())


__all__ = ["TaxCalculator"]
