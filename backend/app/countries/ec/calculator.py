from .config import Ecuador
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Ecuador-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Ecuador())


__all__ = ["TaxCalculator"]
