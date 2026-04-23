"""
Transaction Matching Engine
Real FIFO/LIFO/Average Cost implementation for accurate cost basis
"""
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MatchedTransaction:
    """Represents a matched buy-sell transaction pair"""
    buy_id: int
    sell_id: int
    buy_date: datetime
    sell_date: datetime
    buy_price: Decimal
    sell_price: Decimal
    quantity: Decimal
    cost_basis: Decimal
    proceeds: Decimal
    gain_loss: Decimal
    holding_days: int
    
    @property
    def gain_loss_percentage(self) -> Decimal:
        """Calculate gain/loss percentage"""
        if self.cost_basis == 0:
            return Decimal("0")
        return ((self.gain_loss / self.cost_basis) * 100).quantize(Decimal("0.01"))


class TransactionMatcher:
    """
    Matches buy and sell transactions using various methods:
    - FIFO (First In, First Out)
    - LIFO (Last In, First Out)
    - Average Cost
    """
    
    def __init__(self, asset: str, transactions: List[Dict]):
        """
        Initialize matcher
        
        Args:
            asset: Asset symbol (e.g., 'BTC', 'ETH')
            transactions: List of transaction dicts with:
                - id, date, type ('buy'/'sell'), quantity, price, fee
        """
        self.asset = asset
        self.transactions = sorted(transactions, key=lambda x: x["date"])
        self.trades: List[MatchedTransaction] = []
    
    # ==================== FIFO METHOD ====================
    
    def match_fifo(self) -> List[MatchedTransaction]:
        """
        Match using FIFO (First In, First Out)
        Each sell is matched with earliest available buys
        
        Returns:
            List of matched transaction pairs
        """
        self.trades = []
        buy_stack: List[Dict] = []
        
        for txn in self.transactions:
            if txn["type"] == "buy":
                buy_stack.append({
                    **txn,
                    "remaining": Decimal(str(txn["quantity"]))
                })
            
            elif txn["type"] == "sell":
                sell_date = txn["date"]
                sell_price = Decimal(str(txn["price"]))
                sell_qty = Decimal(str(txn["quantity"]))
                sell_id = txn["id"]
                
                while sell_qty > 0 and buy_stack:
                    buy = buy_stack[0]
                    
                    qty_to_match = min(sell_qty, buy["remaining"])
                    buy_price = Decimal(str(buy["price"]))
                    buy_date = buy["date"]
                    
                    cost_basis = qty_to_match * buy_price
                    proceeds = qty_to_match * sell_price
                    gain_loss = proceeds - cost_basis
                    
                    holding_days = (sell_date - buy_date).days
                    
                    matched = MatchedTransaction(
                        buy_id=buy["id"],
                        sell_id=sell_id,
                        buy_date=buy_date,
                        sell_date=sell_date,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        quantity=qty_to_match,
                        cost_basis=cost_basis.quantize(Decimal("0.01")),
                        proceeds=proceeds.quantize(Decimal("0.01")),
                        gain_loss=gain_loss.quantize(Decimal("0.01")),
                        holding_days=holding_days
                    )
                    
                    self.trades.append(matched)
                    
                    buy["remaining"] -= qty_to_match
                    sell_qty -= qty_to_match
                    
                    if buy["remaining"] == 0:
                        buy_stack.pop(0)
        
        return self.trades
    
    # ==================== LIFO METHOD ====================
    
    def match_lifo(self) -> List[MatchedTransaction]:
        """
        Match using LIFO (Last In, First Out)
        Each sell is matched with most recent buys
        
        Returns:
            List of matched transaction pairs
        """
        self.trades = []
        buy_stack: List[Dict] = []
        
        for txn in self.transactions:
            if txn["type"] == "buy":
                buy_stack.append({
                    **txn,
                    "remaining": Decimal(str(txn["quantity"]))
                })
            
            elif txn["type"] == "sell":
                sell_date = txn["date"]
                sell_price = Decimal(str(txn["price"]))
                sell_qty = Decimal(str(txn["quantity"]))
                sell_id = txn["id"]
                
                while sell_qty > 0 and buy_stack:
                    buy = buy_stack[-1]  # Get most recent buy
                    
                    qty_to_match = min(sell_qty, buy["remaining"])
                    buy_price = Decimal(str(buy["price"]))
                    buy_date = buy["date"]
                    
                    cost_basis = qty_to_match * buy_price
                    proceeds = qty_to_match * sell_price
                    gain_loss = proceeds - cost_basis
                    
                    holding_days = (sell_date - buy_date).days
                    
                    matched = MatchedTransaction(
                        buy_id=buy["id"],
                        sell_id=sell_id,
                        buy_date=buy_date,
                        sell_date=sell_date,
                        buy_price=buy_price,
                        sell_price=sell_price,
                        quantity=qty_to_match,
                        cost_basis=cost_basis.quantize(Decimal("0.01")),
                        proceeds=proceeds.quantize(Decimal("0.01")),
                        gain_loss=gain_loss.quantize(Decimal("0.01")),
                        holding_days=holding_days
                    )
                    
                    self.trades.append(matched)
                    
                    buy["remaining"] -= qty_to_match
                    sell_qty -= qty_to_match
                    
                    if buy["remaining"] == 0:
                        buy_stack.pop()
        
        return self.trades
    
    # ==================== AVERAGE COST METHOD ====================
    
    def match_average_cost(self) -> List[MatchedTransaction]:
        """
        Match using Average Cost method
        Maintains running average cost of all holdings
        
        Returns:
            List of matched transaction pairs (with average cost assigned)
        """
        self.trades = []
        
        total_cost = Decimal("0")
        total_quantity = Decimal("0")
        average_price = Decimal("0")
        accumulated_buys: Dict[int, Decimal] = {}  # buy_id -> quantity held
        
        for txn in self.transactions:
            if txn["type"] == "buy":
                qty = Decimal(str(txn["quantity"]))
                price = Decimal(str(txn["price"]))
                
                total_cost += qty * price
                total_quantity += qty
                accumulated_buys[txn["id"]] = qty
                
                if total_quantity > 0:
                    average_price = total_cost / total_quantity
            
            elif txn["type"] == "sell":
                sell_date = txn["date"]
                sell_price = Decimal(str(txn["price"]))
                sell_qty = Decimal(str(txn["quantity"]))
                sell_id = txn["id"]
                
                # Use average cost for all sells
                cost_basis = sell_qty * average_price
                proceeds = sell_qty * sell_price
                gain_loss = proceeds - cost_basis
                
                # For FIFO buy reference, find earliest buy
                earliest_buy_id = min(accumulated_buys.keys()) if accumulated_buys else None
                earliest_buy_date = next(
                    (t["date"] for t in self.transactions if t["id"] == earliest_buy_id),
                    sell_date
                )
                
                holding_days = (sell_date - earliest_buy_date).days
                
                matched = MatchedTransaction(
                    buy_id=earliest_buy_id or sell_id,
                    sell_id=sell_id,
                    buy_date=earliest_buy_date,
                    sell_date=sell_date,
                    buy_price=average_price,
                    sell_price=sell_price,
                    quantity=sell_qty,
                    cost_basis=cost_basis.quantize(Decimal("0.01")),
                    proceeds=proceeds.quantize(Decimal("0.01")),
                    gain_loss=gain_loss.quantize(Decimal("0.01")),
                    holding_days=holding_days
                )
                
                self.trades.append(matched)
                
                # Reduce total cost and quantity
                total_cost -= cost_basis
                total_quantity -= sell_qty
                
                # Update accumulated buys
                remaining_to_reduce = sell_qty
                for buy_id in sorted(accumulated_buys.keys()):
                    if remaining_to_reduce == 0:
                        break
                    qty_to_reduce = min(remaining_to_reduce, accumulated_buys[buy_id])
                    accumulated_buys[buy_id] -= qty_to_reduce
                    remaining_to_reduce -= qty_to_reduce
                    
                    if accumulated_buys[buy_id] == 0:
                        del accumulated_buys[buy_id]
        
        return self.trades
    
    # ==================== ANALYSIS METHODS ====================
    
    def get_summary(self) -> Dict:
        """Get summary statistics of all matched trades"""
        if not self.trades:
            return {
                "total_trades": 0,
                "total_quantity": Decimal("0"),
                "total_cost": Decimal("0"),
                "total_proceeds": Decimal("0"),
                "total_gain_loss": Decimal("0"),
                "short_term_trades": 0,
                "long_term_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0
            }
        
        total_quantity = sum(t.quantity for t in self.trades)
        total_cost = sum(t.cost_basis for t in self.trades)
        total_proceeds = sum(t.proceeds for t in self.trades)
        total_gain_loss = sum(t.gain_loss for t in self.trades)
        
        short_term = sum(1 for t in self.trades if t.holding_days < 365)
        long_term = sum(1 for t in self.trades if t.holding_days >= 365)
        
        winning = sum(1 for t in self.trades if t.gain_loss > 0)
        losing = sum(1 for t in self.trades if t.gain_loss < 0)
        
        return {
            "total_trades": len(self.trades),
            "total_quantity": total_quantity.quantize(Decimal("0.01")),
            "total_cost": total_cost,
            "total_proceeds": total_proceeds,
            "total_gain_loss": total_gain_loss,
            "average_gain_loss": (total_gain_loss / len(self.trades)).quantize(Decimal("0.01")) if self.trades else Decimal("0"),
            "short_term_trades": short_term,
            "long_term_trades": long_term,
            "winning_trades": winning,
            "losing_trades": losing,
            "win_rate": f"{(winning / len(self.trades) * 100):.1f}%" if self.trades else "0%"
        }
    
    def get_unmatched_quantity(self) -> Dict[str, Decimal]:
        """
        Get quantity of unmatched (holding) positions by date range
        
        Returns:
            Dictionary of unmatched quantities
        """
        total_bought = sum(
            Decimal(str(t["quantity"])) 
            for t in self.transactions 
            if t["type"] == "buy"
        )
        
        total_sold = sum(
            Decimal(str(t["quantity"])) 
            for t in self.transactions 
            if t["type"] == "sell"
        )
        
        return {
            "total_bought": total_bought,
            "total_sold": total_sold,
            "unmatched_holding": total_bought - total_sold
        }
    
    def export_to_csv(self) -> str:
        """Export matched trades to CSV format"""
        if not self.trades:
            return "No trades to export\n"
        
        lines = [
            "Buy Date,Sell Date,Quantity,Buy Price,Sell Price,Cost Basis,Proceeds,Gain/Loss,Holding Days,Gain/Loss %"
        ]
        
        for trade in self.trades:
            line = f"{trade.buy_date.date()},{trade.sell_date.date()},{trade.quantity},{trade.buy_price},{trade.sell_price},{trade.cost_basis},{trade.proceeds},{trade.gain_loss},{trade.holding_days},{trade.gain_loss_percentage}%"
            lines.append(line)
        
        return "\n".join(lines)
