"""
Cost Basis Calculator
Support for FIFO, LIFO, and AVCO methods
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime


class CostBasisLot:
    """Represents a single lot of purchases"""
    def __init__(self, asset: str, quantity: Decimal, purchase_price: Decimal, purchase_date: datetime):
        self.asset = asset
        self.quantity = quantity
        self.purchase_price = purchase_price
        self.purchase_date = purchase_date
        self.cost_basis = quantity * purchase_price
    
    def __repr__(self):
        return f"<Lot {self.asset}: {self.quantity} @ {self.purchase_price} on {self.purchase_date.date()}>"


class CostBasisCalculator:
    """
    Calculate cost basis using FIFO, LIFO, or AVCO method
    """
    
    def __init__(self, lots: List[CostBasisLot]):
        """Initialize with list of purchase lots"""
        self.lots = sorted(lots, key=lambda x: x.purchase_date)  # Sort by date
    
    @classmethod
    def fifo(cls, lots: List[CostBasisLot], quantity_to_sell: Decimal) -> Tuple[Decimal, List[CostBasisLot]]:
        """
        FIFO - First In, First Out
        Sell oldest lots first (good in rising markets)
        
        Args:
            lots: List of all purchase lots
            quantity_to_sell: How much to sell
        
        Returns:
            (average_cost_basis, lots_being_sold)
        """
        # Sort by purchase date (oldest first)
        sorted_lots = sorted(lots, key=lambda x: x.purchase_date)
        
        sold_lots = []
        remaining_qty = quantity_to_sell
        total_cost = Decimal("0")
        
        for lot in sorted_lots:
            if remaining_qty <= 0:
                break
            
            qty_sold = min(lot.quantity, remaining_qty)
            sold_lots.append(CostBasisLot(
                lot.asset,
                qty_sold,
                lot.purchase_price,
                lot.purchase_date
            ))
            
            total_cost += qty_sold * lot.purchase_price
            remaining_qty -= qty_sold
        
        avg_cost = total_cost / quantity_to_sell if quantity_to_sell > 0 else Decimal("0")
        return avg_cost, sold_lots
    
    @classmethod
    def lifo(cls, lots: List[CostBasisLot], quantity_to_sell: Decimal) -> Tuple[Decimal, List[CostBasisLot]]:
        """
        LIFO - Last In, First Out
        Sell newest lots first (good in falling markets, maximizes losses)
        
        Args:
            lots: List of all purchase lots
            quantity_to_sell: How much to sell
        
        Returns:
            (average_cost_basis, lots_being_sold)
        """
        # Sort by purchase date (newest first)
        sorted_lots = sorted(lots, key=lambda x: x.purchase_date, reverse=True)
        
        sold_lots = []
        remaining_qty = quantity_to_sell
        total_cost = Decimal("0")
        
        for lot in sorted_lots:
            if remaining_qty <= 0:
                break
            
            qty_sold = min(lot.quantity, remaining_qty)
            sold_lots.append(CostBasisLot(
                lot.asset,
                qty_sold,
                lot.purchase_price,
                lot.purchase_date
            ))
            
            total_cost += qty_sold * lot.purchase_price
            remaining_qty -= qty_sold
        
        avg_cost = total_cost / quantity_to_sell if quantity_to_sell > 0 else Decimal("0")
        return avg_cost, sold_lots
    
    @classmethod
    def avco(cls, lots: List[CostBasisLot], quantity_to_sell: Decimal) -> Tuple[Decimal, List[CostBasisLot]]:
        """
        AVCO - Average Cost, Continuous Inventory (WAC)
        Use weighted average price across all lots
        
        Args:
            lots: List of all purchase lots
            quantity_to_sell: How much to sell
        
        Returns:
            (average_cost_basis, lots_being_sold)
        """
        # Calculate weighted average
        total_qty = sum(lot.quantity for lot in lots)
        total_cost = sum(lot.cost_basis for lot in lots)
        
        if total_qty == 0:
            return Decimal("0"), []
        
        avg_price = total_cost / total_qty
        
        # For AVCO, we mark the sold quantity as one "lot" at avg price
        # But track the date as today (since it's weighted)
        sold_lot = CostBasisLot(
            lots[0].asset,
            quantity_to_sell,
            avg_price,
            datetime.now()
        )
        
        return avg_price, [sold_lot]
    
    @classmethod
    def specific_id(cls, lots: List[CostBasisLot], quantity_to_sell: Decimal, 
                   specific_lot_ids: List[int]) -> Tuple[Decimal, List[CostBasisLot]]:
        """
        Specific Identification
        Manually choose which lots to sell (maximum flexibility for tax optimization)
        
        Args:
            lots: List of all purchase lots
            quantity_to_sell: How much to sell
            specific_lot_ids: Indices of lots to sell
        
        Returns:
            (average_cost_basis, lots_being_sold)
        """
        sold_lots = []
        total_cost = Decimal("0")
        remaining_qty = quantity_to_sell
        
        # Select lots in specified order
        for i in specific_lot_ids:
            if i >= len(lots) or remaining_qty <= 0:
                break
            
            lot = lots[i]
            qty_sold = min(lot.quantity, remaining_qty)
            
            sold_lots.append(CostBasisLot(
                lot.asset,
                qty_sold,
                lot.purchase_price,
                lot.purchase_date
            ))
            
            total_cost += qty_sold * lot.purchase_price
            remaining_qty -= qty_sold
        
        avg_cost = total_cost / quantity_to_sell if quantity_to_sell > 0 else Decimal("0")
        return avg_cost, sold_lots
    
    @classmethod
    def calculate(cls, method: str, lots: List[CostBasisLot], quantity_to_sell: Decimal):
        """
        Generic method selector
        
        Args:
            method: "FIFO", "LIFO", "AVCO", or "SPECIFIC"
            lots: List of purchase lots
            quantity_to_sell: Quantity to sell
        
        Returns:
            (average_cost_basis, lots_being_sold)
        """
        method_upper = method.upper()
        
        if method_upper == "FIFO":
            return cls.fifo(lots, quantity_to_sell)
        elif method_upper == "LIFO":
            return cls.lifo(lots, quantity_to_sell)
        elif method_upper == "AVCO":
            return cls.avco(lots, quantity_to_sell)
        else:
            return cls.fifo(lots, quantity_to_sell)  # Default FIFO
    
    @classmethod
    def find_optimal_loss(cls, lots: List[CostBasisLot], quantity_to_sell: Decimal, 
                         current_price: Decimal) -> Tuple[str, Decimal, Decimal]:
        """
        Find which method maximizes loss (for tax-loss harvesting)
        
        Args:
            lots: List of purchase lots
            quantity_to_sell: Quantity to sell
            current_price: Current market price
        
        Returns:
            (best_method, loss_amount, avg_cost_basis)
        """
        methods = {
            "FIFO": cls.fifo(lots, quantity_to_sell),
            "LIFO": cls.lifo(lots, quantity_to_sell),
            "AVCO": cls.avco(lots, quantity_to_sell),
        }
        
        best_method = "FIFO"
        best_loss = Decimal("0")
        best_cost = Decimal("0")
        
        for method_name, (avg_cost, sold_lots) in methods.items():
            sale_proceeds = quantity_to_sell * current_price
            gain_loss = sale_proceeds - (quantity_to_sell * avg_cost)
            
            if gain_loss < best_loss:  # More negative = bigger loss
                best_loss = gain_loss
                best_method = method_name
                best_cost = avg_cost
        
        return best_method, abs(best_loss), best_cost  # Return loss as positive
    
    @classmethod
    def from_transactions(cls, transactions: List[Dict]) -> List[CostBasisLot]:
        """
        Build cost basis lots from transaction history
        
        Args:
            transactions: List of buy transactions with:
                - 'amount': quantity
                - 'price': price per unit
                - 'timestamp': purchase date
        
        Returns:
            List of CostBasisLot objects
        """
        lots = []
        for tx in transactions:
            if tx.get('tx_type') in ['buy', 'purchase', 'deposit', 'income']:
                lot = CostBasisLot(
                    asset=tx.get('asset'),
                    quantity=Decimal(str(tx.get('amount', 0))),
                    purchase_price=Decimal(str(tx.get('price', 0))),
                    purchase_date=tx.get('timestamp', datetime.now())
                )
                lots.append(lot)
        
        return lots


# Example usage
if __name__ == "__main__":
    from datetime import datetime, timedelta
    
    # Create sample lots
    lots = [
        CostBasisLot("BTC", Decimal("0.5"), Decimal("40000"), datetime.now() - timedelta(days=365)),
        CostBasisLot("BTC", Decimal("0.5"), Decimal("45000"), datetime.now() - timedelta(days=180)),
        CostBasisLot("BTC", Decimal("0.5"), Decimal("35000"), datetime.now() - timedelta(days=30)),
    ]
    
    quantity_to_sell = Decimal("1.0")
    current_price = Decimal("30000")  # Price is down
    
    # Compare methods
    fifo_cost, _ = CostBasisCalculator.fifo(lots, quantity_to_sell)
    lifo_cost, _ = CostBasisCalculator.lifo(lots, quantity_to_sell)
    avco_cost, _ = CostBasisCalculator.avco(lots, quantity_to_sell)
    
    print(f"FIFO cost basis: {fifo_cost}")
    print(f"LIFO cost basis: {lifo_cost}")
    print(f"AVCO cost basis: {avco_cost}")
    
    # Find optimal loss
    best_method, loss, cost = CostBasisCalculator.find_optimal_loss(lots, quantity_to_sell, current_price)
    print(f"\nOptimal method: {best_method}, Loss: {loss}, Cost basis: {cost}")
