"""
TLH Executor - Order Execution Layer
Handles dry-run simulations and actual exchange execution
"""

from typing import Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Order execution states"""
    RECOMMENDED = "recommended"      # Just a recommendation
    DRY_RUN_PENDING = "dry_run_pending"
    DRY_RUN_COMPLETED = "dry_run_completed"
    DRY_RUN_FAILED = "dry_run_failed"
    PENDING = "pending"              # Ready to execute
    EXECUTING = "executing"
    EXECUTED = "executed"
    PARTIALLY_EXECUTED = "partially_executed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class ExecutionResult:
    """Result of order execution"""
    
    def __init__(self, success: bool, **kwargs):
        self.success = success
        self.timestamp = datetime.now()
        self.order_id = kwargs.get('order_id')
        self.quantity_executed = kwargs.get('quantity_executed')
        self.average_price = kwargs.get('average_price')
        self.fees_paid = kwargs.get('fees_paid')
        self.message = kwargs.get('message', '')
        self.error = kwargs.get('error')
        self.exchange_response = kwargs.get('exchange_response', {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return {
            'success': self.success,
            'timestamp': self.timestamp.isoformat(),
            'order_id': self.order_id,
            'quantity_executed': float(self.quantity_executed) if self.quantity_executed else 0,
            'average_price': float(self.average_price) if self.average_price else 0,
            'fees_paid': float(self.fees_paid) if self.fees_paid else 0,
            'message': self.message,
            'error': self.error,
        }


class TLHExecutor:
    """
    Executes tax-loss harvesting orders on exchange
    Supports dry-run simulations before real execution
    """
    
    def __init__(self, exchange_adapter=None):
        """
        Args:
            exchange_adapter: CCXT adapter or mock for testing
        """
        self.exchange = exchange_adapter
        self.execution_history = []
    
    def dry_run(
        self,
        asset: str,
        quantity: Decimal,
        current_price: Decimal,
        exchange_fee_pct: float = 0.1,
        slippage_pct: float = 0.1,
    ) -> ExecutionResult:
        """
        Simulate order execution without actually submitting
        
        Args:
            asset: What to sell (BTC, ETH, etc.)
            quantity: How much to sell
            current_price: Market price
            exchange_fee_pct: Fee percentage
            slippage_pct: Expected slippage
        
        Returns:
            ExecutionResult with simulated outcome
        """
        logger.info(f"[TLH Executor] DRY RUN: {quantity} {asset} @ ${current_price}")
        
        try:
            # Simulate market impact (slippage)
            actual_price = current_price * (1 - Decimal(str(slippage_pct)) / 100)
            
            # Calculate fees
            sale_value = quantity * actual_price
            fees = sale_value * (Decimal(str(exchange_fee_pct)) / 100)
            
            # Net proceeds
            net_proceeds = sale_value - fees
            
            result = ExecutionResult(
                success=True,
                order_id=f"DRY_RUN_{asset}_{datetime.now().timestamp()}",
                quantity_executed=quantity,
                average_price=actual_price,
                fees_paid=fees,
                message=f"DRY RUN: Would sell {quantity} {asset} for ${net_proceeds:.2f} (after ${fees:.2f} fees)"
            )
            
            logger.info(f"[TLH Executor] DRY RUN SUCCESS: {result.message}")
            self.execution_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error(f"[TLH Executor] DRY RUN FAILED: {str(e)}")
            result = ExecutionResult(
                success=False,
                error=str(e),
                message=f"Dry run failed: {str(e)}"
            )
            self.execution_history.append(result)
            return result
    
    def execute_order(
        self,
        asset: str,
        quantity: Decimal,
        current_price: Decimal,
        exchange_id: Optional[int] = None,
        dry_run_first: bool = True,
    ) -> ExecutionResult:
        """
        Execute actual order on exchange
        
        Args:
            asset: What to sell
            quantity: How much
            current_price: Current market price
            exchange_id: Which exchange (for multi-exchange support)
            dry_run_first: Run simulation first
        
        Returns:
            ExecutionResult
        """
        logger.info(f"[TLH Executor] EXECUTE ORDER: {quantity} {asset}")
        
        # Step 1: Dry run first
        if dry_run_first:
            dry_run_result = self.dry_run(asset, quantity, current_price)
            if not dry_run_result.success:
                logger.warning(f"[TLH Executor] Dry run failed, aborting execution")
                return dry_run_result
        
        # Step 2: Execute on exchange
        try:
            if not self.exchange:
                # Mock execution for testing
                logger.warning("[TLH Executor] No exchange adapter - using mock execution")
                return self._mock_execution(asset, quantity, current_price)
            
            # Real exchange execution
            order_result = self.exchange.sell_market(
                symbol=f"{asset}/USD",
                quantity=float(quantity)
            )
            
            logger.info(f"[TLH Executor] ORDER SUBMITTED: {order_result.get('id')}")
            
            result = ExecutionResult(
                success=True,
                order_id=order_result.get('id'),
                quantity_executed=order_result.get('filled'),
                average_price=order_result.get('average', current_price),
                fees_paid=order_result.get('fee', {}).get('cost', 0),
                exchange_response=order_result
            )
            
            self.execution_history.append(result)
            return result
            
        except Exception as e:
            logger.error(f"[TLH Executor] EXECUTION FAILED: {str(e)}")
            result = ExecutionResult(
                success=False,
                error=str(e),
                message=f"Order failed: {str(e)}"
            )
            self.execution_history.append(result)
            return result
    
    def _mock_execution(
        self,
        asset: str,
        quantity: Decimal,
        price: Decimal,
    ) -> ExecutionResult:
        """Mock execution for testing"""
        sale_value = quantity * price
        fees = sale_value * Decimal("0.001")  # 0.1% fee
        
        return ExecutionResult(
            success=True,
            order_id=f"MOCK_{asset}_{datetime.now().timestamp()}",
            quantity_executed=quantity,
            average_price=price,
            fees_paid=fees,
            message=f"MOCK ORDER: Sold {quantity} {asset} for ${sale_value:.2f}"
        )
    
    def verify_execution(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Verify order status on exchange"""
        if not self.exchange:
            logger.warning("[TLH Executor] No exchange adapter - cannot verify")
            return None
        
        try:
            order = self.exchange.fetch_order(order_id)
            return {
                'id': order.get('id'),
                'status': order.get('status'),  # open, closed, cancelled
                'filled': order.get('filled'),
                'remaining': order.get('remaining'),
                'average_price': order.get('average'),
            }
        except Exception as e:
            logger.error(f"[TLH Executor] Verify failed: {str(e)}")
            return None
    
    def get_execution_history(self) -> list:
        """Get all execution attempts"""
        return [r.to_dict() for r in self.execution_history]


class TLHExecutionStrategy:
    """
    Strategy pattern for different execution approaches
    """
    
    def execute(self, **kwargs) -> ExecutionResult:
        """Execute based on strategy"""
        raise NotImplementedError


class ImmediateExecutionStrategy(TLHExecutionStrategy):
    """Execute immediately at current price"""
    
    def __init__(self, executor: TLHExecutor):
        self.executor = executor
    
    def execute(
        self,
        asset: str,
        quantity: Decimal,
        current_price: Decimal,
        **kwargs
    ) -> ExecutionResult:
        """Execute now"""
        logger.info(f"[ImmediateStrategy] Executing {quantity} {asset} NOW")
        return self.executor.execute_order(
            asset=asset,
            quantity=quantity,
            current_price=current_price,
            dry_run_first=True
        )


class LimitPriceStrategy(TLHExecutionStrategy):
    """Execute only if price drops below threshold"""
    
    def __init__(self, executor: TLHExecutor, limit_price_drop_pct: float = 2.0):
        self.executor = executor
        self.limit_price_drop_pct = limit_price_drop_pct
    
    def execute(
        self,
        asset: str,
        quantity: Decimal,
        current_price: Decimal,
        purchase_price: Decimal,
        **kwargs
    ) -> ExecutionResult:
        """Execute only if we can get better price"""
        # Limit price = current price + acceptable drop
        limit_price = current_price * (1 - Decimal(str(self.limit_price_drop_pct)) / 100)
        
        if current_price > limit_price:
            # Current price is better than limit, execute
            logger.info(f"[LimitStrategy] Price acceptable ({current_price} > {limit_price}), executing")
            return self.executor.execute_order(
                asset=asset,
                quantity=quantity,
                current_price=current_price,
                dry_run_first=True
            )
        else:
            logger.info(f"[LimitStrategy] Waiting for limit price. Current: {current_price}, Limit: {limit_price}")
            return ExecutionResult(
                success=False,
                message=f"Limit price not reached. Current: ${current_price}, Limit: ${limit_price}"
            )


class ScheduledExecutionStrategy(TLHExecutionStrategy):
    """Execute at specific time"""
    
    def __init__(self, executor: TLHExecutor, execution_time: datetime):
        self.executor = executor
        self.execution_time = execution_time
    
    def execute(
        self,
        asset: str,
        quantity: Decimal,
        current_price: Decimal,
        **kwargs
    ) -> ExecutionResult:
        """Check if time to execute"""
        now = datetime.now()
        
        if now >= self.execution_time:
            logger.info(f"[ScheduledStrategy] Execution time reached, executing")
            return self.executor.execute_order(
                asset=asset,
                quantity=quantity,
                current_price=current_price,
                dry_run_first=True
            )
        else:
            remaining = (self.execution_time - now).total_seconds() / 60
            logger.info(f"[ScheduledStrategy] Waiting for scheduled time ({remaining:.0f} minutes remaining)")
            return ExecutionResult(
                success=False,
                message=f"Waiting for scheduled execution in {remaining:.0f} minutes"
            )


# Example usage
if __name__ == "__main__":
    from decimal import Decimal
    
    # Create executor
    executor = TLHExecutor()
    
    # Dry run
    dry_result = executor.dry_run(
        asset="BTC",
        quantity=Decimal("1.5"),
        current_price=Decimal("30000"),
        exchange_fee_pct=0.1,
        slippage_pct=0.2
    )
    
    print(f"Dry run result: {dry_result.to_dict()}")
    
    # Immediate execution strategy
    strategy = ImmediateExecutionStrategy(executor)
    exec_result = strategy.execute(
        asset="BTC",
        quantity=Decimal("1.5"),
        current_price=Decimal("30000")
    )
    
    print(f"Execution result: {exec_result.to_dict()}")
    
    # Execution history
    print(f"\nExecution history:\n{executor.get_execution_history()}")
