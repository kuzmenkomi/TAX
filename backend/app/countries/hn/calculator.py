from .config import Honduras
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Honduras-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Honduras())


__all__ = ["TaxCalculator"]
