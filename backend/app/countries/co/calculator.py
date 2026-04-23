from .config import Colombia
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Colombia-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Colombia())


__all__ = ["TaxCalculator"]
