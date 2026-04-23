from .config import Chile
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Chile-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Chile())


__all__ = ["TaxCalculator"]
