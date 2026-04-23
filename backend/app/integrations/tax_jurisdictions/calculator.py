"""
Tax Calculation Engine
Core tax calculation logic for all jurisdictions
"""
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from .base import CapitalGain, TaxCalculationResult


class TaxCalculator:
    """
    Universal tax calculator with common methods
    Used by all jurisdiction implementations
    """
    
    @staticmethod
    def apply_progressive_rates(
        amount: Decimal,
        rate_tiers: List[Dict]
    ) -> Decimal:
        """
        Apply progressive tax rates
        
        Args:
            amount: Taxable amount
            rate_tiers: List of {"min": N, "max": M, "rate": R} dicts
        
        Returns:
            Calculated tax
        """
        tax = Decimal("0")
        
        for tier in rate_tiers:
            tier_min = Decimal(str(tier["min"]))
            tier_max = Decimal(str(tier["max"]))
            tier_rate = Decimal(str(tier["rate"]))
            
            if amount <= tier_min:
                break
            
            taxable_in_tier = min(amount, tier_max) - tier_min
            if taxable_in_tier > 0:
                tax += taxable_in_tier * tier_rate
        
        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_simple_tax(
        amount: Decimal,
        rate: Decimal
    ) -> Decimal:
        """
        Calculate simple flat tax
        
        Args:
            amount: Amount to tax
            rate: Tax rate (e.g., 0.15 for 15%)
        
        Returns:
            Calculated tax
        """
        tax = amount * rate
        return tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_fifo_cost_basis(transactions: List[Dict]) -> Decimal:
        """
        Calculate cost basis using FIFO (First In, First Out)
        
        Each sell transaction is matched with the earliest buy transactions
        
        Args:
            transactions: List of {type, quantity, price, date} dicts
        
        Returns:
            Total cost basis
        """
        sorted_txns = sorted(transactions, key=lambda x: x["date"])
        
        buy_stack = []
        total_cost = Decimal("0")
        
        for txn in sorted_txns:
            if txn["type"] == "buy":
                buy_stack.append({
                    "quantity": Decimal(str(txn["quantity"])),
                    "price": Decimal(str(txn["price"]))
                })
            elif txn["type"] == "sell":
                sell_qty = Decimal(str(txn["quantity"]))
                
                while sell_qty > 0 and buy_stack:
                    buy = buy_stack[0]
                    
                    qty_to_sell = min(sell_qty, buy["quantity"])
                    total_cost += qty_to_sell * buy["price"]
                    
                    buy["quantity"] -= qty_to_sell
                    sell_qty -= qty_to_sell
                    
                    if buy["quantity"] == 0:
                        buy_stack.pop(0)
        
        return total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_average_cost_basis(transactions: List[Dict]) -> Decimal:
        """
        Calculate cost basis using Average Cost method
        
        Maintains running average cost of all holdings
        
        Args:
            transactions: List of {type, quantity, price, date} dicts
        
        Returns:
            Total cost basis
        """
        sorted_txns = sorted(transactions, key=lambda x: x["date"])
        
        average_price = Decimal("0")
        total_quantity = Decimal("0")
        total_cost = Decimal("0")
        
        for txn in sorted_txns:
            if txn["type"] == "buy":
                qty = Decimal(str(txn["quantity"]))
                price = Decimal(str(txn["price"]))
                
                total_cost += qty * price
                total_quantity += qty
                
                if total_quantity > 0:
                    average_price = total_cost / total_quantity
            
            elif txn["type"] == "sell":
                qty = Decimal(str(txn["quantity"]))
                total_cost -= qty * average_price
                total_quantity -= qty
        
        return total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_lifo_cost_basis(transactions: List[Dict]) -> Decimal:
        """
        Calculate cost basis using LIFO (Last In, First Out)
        
        Each sell transaction is matched with the most recent buy transactions
        
        Args:
            transactions: List of {type, quantity, price, date} dicts
        
        Returns:
            Total cost basis
        """
        sorted_txns = sorted(transactions, key=lambda x: x["date"])
        
        buy_stack = []
        total_cost = Decimal("0")
        
        for txn in sorted_txns:
            if txn["type"] == "buy":
                buy_stack.append({
                    "quantity": Decimal(str(txn["quantity"])),
                    "price": Decimal(str(txn["price"]))
                })
            elif txn["type"] == "sell":
                sell_qty = Decimal(str(txn["quantity"]))
                
                while sell_qty > 0 and buy_stack:
                    buy = buy_stack[-1]  # Get last (most recent) buy
                    
                    qty_to_sell = min(sell_qty, buy["quantity"])
                    total_cost += qty_to_sell * buy["price"]
                    
                    buy["quantity"] -= qty_to_sell
                    sell_qty -= qty_to_sell
                    
                    if buy["quantity"] == 0:
                        buy_stack.pop()
        
        return total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def group_transactions_by_month(transactions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group transactions by year-month
        
        Args:
            transactions: List of transactions with date field
        
        Returns:
            Dictionary of {YYYY-MM: [transactions]}
        """
        grouped = {}
        
        for txn in transactions:
            date = txn["date"]
            key = f"{date.year}-{date.month:02d}"
            
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(txn)
        
        return grouped
    
    @staticmethod
    def group_transactions_by_year(transactions: List[Dict]) -> Dict[int, List[Dict]]:
        """
        Group transactions by year
        
        Args:
            transactions: List of transactions with date field
        
        Returns:
            Dictionary of {YYYY: [transactions]}
        """
        grouped = {}
        
        for txn in transactions:
            year = txn["date"].year
            
            if year not in grouped:
                grouped[year] = []
            grouped[year].append(txn)
        
        return grouped
    
    @staticmethod
    def calculate_short_vs_long_term(
        gains: List[CapitalGain],
        holding_period_days: int
    ) -> tuple[Decimal, Decimal]:
        """
        Calculate short-term and long-term gains separately
        
        Args:
            gains: List of CapitalGain objects
            holding_period_days: Threshold for long-term classification
        
        Returns:
            Tuple of (short_term_gain, long_term_gain)
        """
        short_term = Decimal("0")
        long_term = Decimal("0")
        
        for gain in gains:
            if gain.holding_days >= holding_period_days:
                long_term += gain.gain_amount
            else:
                short_term += gain.gain_amount
        
        return short_term, long_term
    
    @staticmethod
    def apply_trading_fee_offset(
        taxable_gain: Decimal,
        trading_fees: Decimal
    ) -> Decimal:
        """
        Apply trading fees as offset against taxable gains
        
        Args:
            taxable_gain: Taxable gain amount
            trading_fees: Total trading fees paid
        
        Returns:
            Net taxable amount after fee offset
        """
        net = taxable_gain - trading_fees
        return max(net, Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_monthly_threshold_tax(
        gains_by_month: Dict[str, Decimal],
        threshold: Decimal,
        tax_rate: Decimal
    ) -> Decimal:
        """
        Calculate tax based on monthly threshold (used by Brazil)
        
        Only months exceeding threshold are taxed
        
        Args:
            gains_by_month: Dictionary of {YYYY-MM: amount}
            threshold: Minimum amount to trigger tax
            tax_rate: Tax rate applied to taxable months
        
        Returns:
            Total tax
        """
        total_tax = Decimal("0")
        
        for month, gain in gains_by_month.items():
            if gain > threshold:
                total_tax += gain * tax_rate
        
        return total_tax.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
