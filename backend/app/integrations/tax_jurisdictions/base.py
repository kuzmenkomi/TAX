"""
Base Tax Jurisdiction Class
Abstract base class for all tax jurisdictions
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaxCalculationResult:
    """Result of tax calculation"""
    transaction_type: str
    amount: Decimal
    tax_category: str
    tax_rate: Decimal
    calculated_tax: Decimal
    notes: Optional[str] = None


@dataclass
class CapitalGain:
    """Single capital gain transaction"""
    buy_date: datetime
    sell_date: datetime
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    fee: Decimal = Decimal("0")
    
    @property
    def holding_days(self) -> int:
        return (self.sell_date - self.buy_date).days
    
    @property
    def gain_amount(self) -> Decimal:
        return (self.sell_price - self.buy_price) * self.quantity - self.fee
    
    @property
    def gain_percentage(self) -> Decimal:
        if self.buy_price == 0:
            return Decimal("0")
        return (self.gain_amount / (self.buy_price * self.quantity)) * 100


class BaseTaxJurisdiction(ABC):
    """
    Abstract base class for tax jurisdiction implementations
    Defines interface for all jurisdictions
    """
    
    # Jurisdiction metadata (override in subclass)
    code: str  # e.g., 'MX', 'BR', 'AR'
    name: str  # e.g., 'Mexico', 'Brazil'
    currency: str  # e.g., 'USD', 'MXN', 'BRL'
    vat_rate: Decimal
    
    # Tax rates (can be simple or progressive)
    tax_rate: Decimal  # Default/simple rate
    holding_period_days: int = 365
    
    def __init__(self):
        """Initialize jurisdiction"""
        self.validate_metadata()
    
    def validate_metadata(self):
        """Validate that required metadata is provided"""
        assert hasattr(self, 'code'), f"{self.__class__.__name__} missing 'code'"
        assert hasattr(self, 'name'), f"{self.__class__.__name__} missing 'name'"
        assert hasattr(self, 'currency'), f"{self.__class__.__name__} missing 'currency'"
        assert hasattr(self, 'vat_rate'), f"{self.__class__.__name__} missing 'vat_rate'"
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def calculate_capital_gains_tax(
        self,
        gains: List[CapitalGain],
        calculation_method: str = "fifo"
    ) -> TaxCalculationResult:
        """
        Calculate capital gains tax on crypto transactions
        
        Args:
            gains: List of capital gain transactions
            calculation_method: 'fifo', 'lifo', or 'average_cost'
        
        Returns:
            TaxCalculationResult with calculated tax
        """
        pass
    
    @abstractmethod
    def calculate_ordinary_income_tax(
        self,
        income_amount: Decimal
    ) -> TaxCalculationResult:
        """
        Calculate ordinary income tax (staking, mining, airdrops)
        
        Args:
            income_amount: Total income amount
        
        Returns:
            TaxCalculationResult with calculated tax
        """
        pass
    
    @abstractmethod
    def calculate_vat_tax(
        self,
        transaction_value: Decimal,
        transaction_type: str
    ) -> TaxCalculationResult:
        """
        Calculate VAT/IVA tax
        
        Args:
            transaction_value: Transaction value
            transaction_type: Type of transaction (buy, sell, transfer)
        
        Returns:
            TaxCalculationResult with VAT calculation
        """
        pass
    
    @abstractmethod
    def calculate_fee_deduction(
        self,
        fee_amount: Decimal
    ) -> Decimal:
        """
        Calculate deductible fees
        
        Args:
            fee_amount: Fee amount
        
        Returns:
            Deductible amount
        """
        pass
    
    @abstractmethod
    def apply_progressive_rates(
        self,
        taxable_amount: Decimal
    ) -> Decimal:
        """
        Apply progressive tax rates
        
        Args:
            taxable_amount: Total taxable income
        
        Returns:
            Calculated tax using progressive rates
        """
        pass
    
    # ==================== HELPER METHODS ====================
    
    def get_holding_period_category(self, days: int) -> str:
        """
        Categorize holding period as short-term or long-term
        
        Args:
            days: Number of days held
        
        Returns:
            'short_term' or 'long_term'
        """
        return "long_term" if days >= self.holding_period_days else "short_term"
    
    def calculate_total_gain(self, gains: List[CapitalGain]) -> Decimal:
        """
        Calculate total capital gains from multiple transactions
        
        Args:
            gains: List of capital gain transactions
        
        Returns:
            Total gain amount
        """
        return sum(gain.gain_amount for gain in gains)
    
    def group_by_holding_period(self, gains: List[CapitalGain]) -> Tuple[List[CapitalGain], List[CapitalGain]]:
        """
        Split gains into short-term and long-term
        
        Args:
            gains: List of capital gain transactions
        
        Returns:
            Tuple of (short_term_gains, long_term_gains)
        """
        short_term = [g for g in gains if self.get_holding_period_category(g.holding_days) == "short_term"]
        long_term = [g for g in gains if self.get_holding_period_category(g.holding_days) == "long_term"]
        return short_term, long_term
    
    def calculate_fifo_gains(self, transactions: List[Dict]) -> Decimal:
        """
        Calculate capital gains using FIFO method
        
        Args:
            transactions: List of buy/sell transactions with timestamps
        
        Returns:
            Total gain calculated using FIFO
        """
        # Implementation would sort by date and match youngest buys to each sell
        # This is a placeholder for the algorithm
        pass
    
    def calculate_average_cost_gains(self, transactions: List[Dict]) -> Decimal:
        """
        Calculate capital gains using Average Cost method
        
        Args:
            transactions: List of transactions
        
        Returns:
            Total gain calculated using average cost
        """
        # Implementation would maintain running average cost
        # This is a placeholder
        pass
    
    def is_taxable_transaction(self, transaction_type: str) -> bool:
        """
        Determine if transaction is taxable
        
        Args:
            transaction_type: Type of transaction
        
        Returns:
            True if taxable, False otherwise
        """
        # Some transactions might be exempt (e.g., transfers, small amounts)
        exempt_types = ['deposit', 'withdrawal', 'transfer']
        return transaction_type not in exempt_types
    
    def apply_inflation_adjustment(self, amount: Decimal, start_date: datetime, end_date: datetime) -> Decimal:
        """
        Apply inflation adjustment (used by Argentina CER, Colombia UVT, etc.)
        
        Args:
            amount: Original amount
            start_date: Start date for adjustment period
            end_date: End date for adjustment period
        
        Returns:
            Inflation-adjusted amount
        """
        # Override in Argentina/Colombia/Peru classes
        return amount
    
    def format_tax_calculation(self, result: TaxCalculationResult) -> Dict:
        """
        Format tax calculation for API response
        
        Args:
            result: TaxCalculationResult object
        
        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            "transaction_type": result.transaction_type,
            "amount": str(result.amount),
            "tax_category": result.tax_category,
            "tax_rate": str(result.tax_rate),
            "calculated_tax": str(result.calculated_tax),
            "notes": result.notes
        }
