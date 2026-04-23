from .config import Peru
from ..base.tax_calculator import BaseTaxCalculator


class TaxCalculator(BaseTaxCalculator):
    """Peru-specific tax calculator"""
    
    def __init__(self):
        super().__init__(Peru())


__all__ = ["TaxCalculator"]
