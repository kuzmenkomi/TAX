"""
TLH Event Listeners - Event-Driven Triggers
Automatically recalculate and execute TLH when price conditions are met
"""

from typing import Callable, Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PriceEventType(str, Enum):
    """Price event types that trigger TLH recalc"""
    PRICE_DROP = "price_drop"           # Price dropped X%
    LOSS_REALIZED = "loss_realized"     # Position now in loss
    LIQUIDITY_IMPROVED = "liquidity_improved"
    WASH_SALE_EXPIRED = "wash_sale_expired"
    OPPORTUNITY_EXPIRED = "opportunity_expired"  # Price recovered
    MANUAL_TRIGGER = "manual_trigger"


@dataclass
class PriceEvent:
    """Price event that may trigger TLH"""
    event_type: PriceEventType
    asset: str
    previous_price: Decimal
    current_price: Decimal
    timestamp: datetime
    metadata: Dict = None
    
    @property
    def price_change_pct(self) -> float:
        """Price change percentage"""
        if self.previous_price == 0:
            return 0
        change = (self.current_price - self.previous_price) / self.previous_price
        return float(change * 100)
    
    def to_dict(self):
        """Convert to dict"""
        return {
            'event_type': self.event_type.value,
            'asset': self.asset,
            'previous_price': float(self.previous_price),
            'current_price': float(self.current_price),
            'price_change_pct': self.price_change_pct,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata or {}
        }


class PriceThreshold:
    """Threshold for triggering price events"""
    
    def __init__(
        self,
        asset: str,
        drop_threshold_pct: float = 5.0,  # Trigger if drops X%
        min_loss_threshold: Decimal = Decimal("100"),  # Trigger if loss > $100
    ):
        self.asset = asset
        self.drop_threshold_pct = drop_threshold_pct
        self.min_loss_threshold = min_loss_threshold
        self.last_price: Optional[Decimal] = None
        self.purchase_price: Optional[Decimal] = None
        self.last_event_time: Optional[datetime] = None
        self.event_cooldown_seconds = 300  # Don't spam events < 5min apart
    
    def check_price_drop(self, current_price: Decimal) -> Optional[PriceEvent]:
        """Check if price drop exceeds threshold"""
        if self.last_price is None:
            self.last_price = current_price
            return None
        
        # Check cooldown (don't spam)
        if self.last_event_time:
            time_since_last = (datetime.now() - self.last_event_time).total_seconds()
            if time_since_last < self.event_cooldown_seconds:
                return None
        
        # Calculate % drop
        price_change = (current_price - self.last_price) / self.last_price
        price_change_pct = abs(price_change * 100)
        
        if price_change < 0 and price_change_pct >= self.drop_threshold_pct:
            logger.info(f"🔔 PRICE DROP EVENT: {self.asset} dropped {price_change_pct:.1f}%")
            
            event = PriceEvent(
                event_type=PriceEventType.PRICE_DROP,
                asset=self.asset,
                previous_price=self.last_price,
                current_price=current_price,
                timestamp=datetime.now(),
                metadata={'drop_pct': price_change_pct}
            )
            
            self.last_event_time = datetime.now()
            self.last_price = current_price
            return event
        
        self.last_price = current_price
        return None
    
    def check_loss_realized(
        self,
        current_price: Decimal,
        average_cost: Decimal
    ) -> Optional[PriceEvent]:
        """Check if position is now in loss"""
        if current_price >= average_cost:
            return None  # Not in loss
        
        loss = (average_cost - current_price) * Decimal("1.0")  # Simplified, assume 1 unit
        
        if loss >= self.min_loss_threshold:
            logger.info(f"🔔 LOSS REALIZED: {self.asset} loss of ${loss:.2f}")
            
            event = PriceEvent(
                event_type=PriceEventType.LOSS_REALIZED,
                asset=self.asset,
                previous_price=average_cost,
                current_price=current_price,
                timestamp=datetime.now(),
                metadata={'loss_amount': float(loss)}
            )
            
            self.last_event_time = datetime.now()
            return event
        
        return None


class TLHEventListener:
    """
    Listen to price events and trigger TLH recalculation
    """
    
    def __init__(self):
        self.thresholds: Dict[str, PriceThreshold] = {}
        self.subscribers: List[Callable] = []  # Observers waiting for events
        self.event_history: List[PriceEvent] = []
        self.max_history_size = 1000
    
    def register_asset(
        self,
        asset: str,
        drop_threshold_pct: float = 5.0,
        purchase_price: Decimal = None,
    ):
        """Register an asset for monitoring"""
        threshold = PriceThreshold(asset, drop_threshold_pct)
        threshold.purchase_price = purchase_price
        self.thresholds[asset] = threshold
        logger.info(f"[Event Listener] Registered {asset} with {drop_threshold_pct}% drop threshold")
    
    def unregister_asset(self, asset: str):
        """Stop monitoring an asset"""
        if asset in self.thresholds:
            del self.thresholds[asset]
            logger.info(f"[Event Listener] Unregistered {asset}")
    
    def on_price_update(self, asset: str, new_price: Decimal) -> Optional[PriceEvent]:
        """
        Handle price update
        
        Returns:
            PriceEvent if threshold crossed, None otherwise
        """
        if asset not in self.thresholds:
            logger.debug(f"[Event Listener] {asset} not registered")
            return None
        
        threshold = self.thresholds[asset]
        event = threshold.check_price_drop(new_price)
        
        if event:
            self.emit_event(event)
        
        return event
    
    def on_loss_realized(
        self,
        asset: str,
        current_price: Decimal,
        average_cost: Decimal
    ) -> Optional[PriceEvent]:
        """Trigger when position enters loss"""
        if asset not in self.thresholds:
            return None
        
        threshold = self.thresholds[asset]
        event = threshold.check_loss_realized(current_price, average_cost)
        
        if event:
            self.emit_event(event)
        
        return event
    
    def emit_event(self, event: PriceEvent):
        """Broadcast event to all subscribers"""
        logger.info(f"[Event Listener] EMIT: {event.event_type.value} for {event.asset}")
        
        # Store in history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size:]
        
        # Notify subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(event)
            except Exception as e:
                logger.error(f"[Event Listener] Subscriber failed: {str(e)}")
    
    def subscribe(self, callback: Callable):
        """Subscribe to events"""
        self.subscribers.append(callback)
        logger.info(f"[Event Listener] Subscriber registered ({len(self.subscribers)} total)")
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from events"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_event_history(self, asset: Optional[str] = None) -> List[Dict]:
        """Get event history"""
        events = self.event_history
        if asset:
            events = [e for e in events if e.asset == asset]
        return [e.to_dict() for e in events]


class TLHEventReactor:
    """
    React to events and trigger TLH recalculation
    """
    
    def __init__(self, optimizer_service):
        """
        Args:
            optimizer_service: TaxLossOptimizer instance
        """
        self.optimizer = optimizer_service
        self.listener = TLHEventListener()
        self.listener.subscribe(self.on_event)
        self.reaction_rules: Dict[PriceEventType, Callable] = {}
    
    def on_event(self, event: PriceEvent):
        """React to price event"""
        logger.info(f"🎯 REACT: Processing {event.event_type.value} for {event.asset}")
        
        rule = self.reaction_rules.get(event.event_type)
        if rule:
            try:
                result = rule(event)
                logger.info(f"✅ Reaction completed: {result}")
            except Exception as e:
                logger.error(f"❌ Reaction failed: {str(e)}")
        else:
            logger.warning(f"⚠️ No reaction rule for {event.event_type.value}")
    
    def register_reaction(self, event_type: PriceEventType, handler: Callable):
        """Register reaction to event type"""
        self.reaction_rules[event_type] = handler
        logger.info(f"[TLH Reactor] Registered reaction for {event_type.value}")
    
    def set_default_reactions(self):
        """Set up default reactions"""
        
        # React to price drop: recalculate TLH
        def on_price_drop(event: PriceEvent):
            logger.info(f"🔄 RECALC TLH: {event.asset} price dropped {event.price_change_pct:.1f}%")
            # Trigger full portfolio rescan
            # opportunities = self.optimizer.scan_portfolio()
            return f"Rescanned {event.asset}"
        
        # React to wash-sale expiration: now can harvest
        def on_wash_sale_expired(event: PriceEvent):
            logger.info(f"✅ WASH-SALE EXPIRED: Can now harvest {event.asset}!")
            # Find recommendations for this asset
            return f"Wash-sale expired for {event.asset}"
        
        # React to loss realization: might be harvestable
        def on_loss_realized(event: PriceEvent):
            logger.info(f"💰 LOSS REALIZED: {event.asset} is now in loss!")
            loss = event.metadata.get('loss_amount', 0)
            logger.info(f"   Loss amount: ${loss:.2f}")
            return f"Loss realized: ${loss:.2f}"
        
        self.register_reaction(PriceEventType.PRICE_DROP, on_price_drop)
        self.register_reaction(PriceEventType.WASH_SALE_EXPIRED, on_wash_sale_expired)
        self.register_reaction(PriceEventType.LOSS_REALIZED, on_loss_realized)


# Example: Integration with price feed
class PriceFeedListener:
    """Simulate price feed and emit events"""
    
    def __init__(self, event_listener: TLHEventListener):
        self.listener = event_listener
    
    def update_price(self, asset: str, price: Decimal):
        """Called when new price arrives from exchange"""
        event = self.listener.on_price_update(asset, price)
        
        if event:
            logger.info(f"📊 Price update triggered event: {event.event_type.value}")
        
        return event


# Example usage
if __name__ == "__main__":
    from decimal import Decimal
    from datetime import datetime
    
    # Create listener
    listener = TLHEventListener()
    listener.register_asset("BTC", drop_threshold_pct=5.0)
    
    # Create reactor
    reactor = TLHEventReactor(None)
    reactor.set_default_reactions()
    
    # Simulate price updates
    prices = [
        Decimal("30000"),  # Initial
        Decimal("29800"),  # -0.7% (no event)
        Decimal("28500"),  # -4.3% (no event yet)
        Decimal("27900"),  # -5.8% (EVENT!)
    ]
    
    price_feed = PriceFeedListener(listener)
    
    print("📈 Simulating price feed updates...\n")
    for price in prices:
        print(f"Price update: BTC = ${price}")
        event = price_feed.update_price("BTC", price)
        if event:
            print(f"   ✨ EVENT TRIGGERED: {event.event_type.value}")
        print()
    
    # Get history
    print(f"\n📋 Event history:\n{listener.get_event_history()}")
