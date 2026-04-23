"""
Liquidity Checker
Evaluate if an asset can be sold without major slippage/impact
"""

from typing import Dict, Tuple, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class LiquidityChecker:
    """
    Assess liquidity of crypto assets
    Prevents recommending sales of illiquid/dead assets
    """
    
    # Liquidity tiers by market cap / 24h volume
    LIQUIDITY_TIERS = {
        "ultra_liquid": {
            "min_24h_volume": Decimal("10000000000"),  # $10B+
            "min_market_cap": Decimal("100000000000"),  # $100B+
            "score": 100,
            "description": "Ultra-liquid (BTC, ETH, USDT, USDC)",
            "slippage_for_sale": Decimal("0.05"),  # 0.05% slippage
        },
        "highly_liquid": {
            "min_24h_volume": Decimal("1000000000"),  # $1B+
            "min_market_cap": Decimal("10000000000"),  # $10B+
            "score": 85,
            "description": "Highly liquid (major alts)",
            "slippage_for_sale": Decimal("0.1"),
        },
        "liquid": {
            "min_24h_volume": Decimal("100000000"),  # $100M+
            "min_market_cap": Decimal("1000000000"),  # $1B+
            "score": 70,
            "description": "Liquid (mid-cap)",
            "slippage_for_sale": Decimal("0.2"),
        },
        "medium_liquid": {
            "min_24h_volume": Decimal("10000000"),  # $10M+
            "min_market_cap": Decimal("100000000"),  # $100M+
            "score": 50,
            "description": "Medium liquidity (small-cap)",
            "slippage_for_sale": Decimal("0.5"),
        },
        "low_liquid": {
            "min_24h_volume": Decimal("1000000"),  # $1M+
            "min_market_cap": Decimal("10000000"),  # $10M+
            "score": 25,
            "description": "Low liquidity (micro-cap)",
            "slippage_for_sale": Decimal("1.0"),
        },
        "illiquid": {
            "min_24h_volume": Decimal("0"),  # Anything
            "min_market_cap": Decimal("0"),
            "score": 5,
            "description": "Illiquid / dead (not recommended)",
            "slippage_for_sale": Decimal("5.0"),
        },
    }
    
    # Known illiquid/meme/scam coins (growing list)
    KNOWN_ILLIQUID = {
        "DOGE": False,  # DOGE is actually liquid
        "SHIB": False,  # Shiba surprisingly has volume now
        "PEPE": True,   # Meme coin, avoid
        "FLOKI": True,  # Meme coin
        "ELON": True,   # Scam coin
        "ELONN": True,  # Fake Elon
        "INU": True,    # Generic inu meme
    }
    
    @classmethod
    def assess_liquidity(
        cls,
        asset: str,
        market_cap: Optional[Decimal] = None,
        volume_24h: Optional[Decimal] = None
    ) -> Tuple[int, str, Decimal]:
        """
        Assess liquidity of an asset
        
        Args:
            asset: Asset code (BTC, ETH, etc.)
            market_cap: Market cap in USD (optional)
            volume_24h: 24h trading volume in USD (optional)
        
        Returns:
            (liquidity_score: 0-100, description: str, estimated_slippage: Decimal)
        """
        
        # Check against known illiquid coins
        if asset.upper() in cls.KNOWN_ILLIQUID:
            if cls.KNOWN_ILLIQUID[asset.upper()]:
                return 5, f"❌ {asset} is known to be illiquid/meme coin", Decimal("5.0")
        
        # No data provided - use heuristics
        if market_cap is None or volume_24h is None:
            return cls._assess_by_asset_name(asset)
        
        # Compare against tiers
        for tier_name, tier_config in cls.LIQUIDITY_TIERS.items():
            if (volume_24h >= tier_config["min_24h_volume"] and 
                market_cap >= tier_config["min_market_cap"]):
                return (
                    tier_config["score"],
                    f"✓ {tier_config['description']}",
                    tier_config["slippage_for_sale"]
                )
        
        # Fallback to illiquid
        return (
            5,
            "❌ Illiquid / Below minimum thresholds",
            Decimal("5.0")
        )
    
    @classmethod
    def _assess_by_asset_name(cls, asset: str) -> Tuple[int, str, Decimal]:
        """
        Heuristic assessment based on asset name
        When real market data not available
        """
        asset_upper = asset.upper()
        
        # Top liquid assets
        ultra_liquid = {"BTC", "ETH", "USDT", "USDC", "BUSD", "DAI", "WBTC"}
        if asset_upper in ultra_liquid:
            return 100, "💎 Ultra-liquid (major stablecoin/top 2)", Decimal("0.05")
        
        # Highly liquid altcoins
        highly_liquid = {"BNB", "XRP", "ADA", "SOL", "DOGE", "LINK", "AVAX", "MATIC", "OP", "ARB"}
        if asset_upper in highly_liquid:
            return 85, "✓ Highly liquid (major altcoin)", Decimal("0.1")
        
        # Liquid mid-caps
        liquid = {"CRV", "UNI", "AAVE", "SUSHI", "MKR", "LDO", "GMX"}
        if asset_upper in liquid:
            return 70, "✓ Liquid (DeFi protocol token)", Decimal("0.2")
        
        # Check for meme/scam patterns
        if any(x in asset_upper for x in ["INU", "PEPE", "FLOKI", "SHIB", "DOGE"]):
            if asset_upper not in {"DOGE", "SHIB"}:  # DOGE & SHIB are exceptions
                return 25, f"⚠️ Likely low liquidity (meme coin pattern)", Decimal("1.0")
        
        # Default: medium liquidity (unknown asset)
        return 50, "❓ Unknown asset - treating as medium liquidity", Decimal("0.5")
    
    @classmethod
    def can_sell_without_slippage(
        cls,
        asset: str,
        quantity_to_sell: Decimal,
        market_cap: Optional[Decimal] = None,
        volume_24h: Optional[Decimal] = None,
        max_slippage_pct: Decimal = Decimal("1.0")
    ) -> Tuple[bool, str]:
        """
        Check if selling a quantity won't cause excessive slippage
        
        Args:
            asset: Asset code
            quantity_to_sell: Amount to sell
            market_cap: Market cap (optional)
            volume_24h: 24h volume (optional)
            max_slippage_pct: Max acceptable slippage % (default 1%)
        
        Returns:
            (can_sell: bool, reason: str)
        """
        liquidity_score, description, est_slippage = cls.assess_liquidity(asset, market_cap, volume_24h)
        
        # Heuristic: check if quantity is too large relative to 24h volume
        if volume_24h and volume_24h > 0:
            quantity_as_pct_of_volume = (quantity_to_sell / volume_24h) * 100
            
            if quantity_as_pct_of_volume > Decimal("5"):  # >5% of 24h volume = problem
                return False, f"⚠️ Selling {quantity_as_pct_of_volume:.1f}% of 24h volume - too large order"
        
        if est_slippage > max_slippage_pct:
            return False, f"❌ Expected slippage {est_slippage}% exceeds max {max_slippage_pct}%"
        
        if liquidity_score < 30:
            return False, f"❌ Liquidity score too low ({liquidity_score}/100) - risky sale"
        
        return True, f"✓ Can sell - {description}, estimated slippage {est_slippage}%"
    
    @classmethod
    def estimate_slippage_impact(
        cls,
        quantity_to_sell: Decimal,
        price: Decimal,
        volume_24h: Optional[Decimal] = None
    ) -> Tuple[Decimal, Decimal]:
        """
        Estimate slippage impact on sale
        
        Args:
            quantity_to_sell: Amount to sell
            price: Current market price
            volume_24h: 24h volume (optional)
        
        Returns:
            (slippage_amount_usd, slippage_percentage)
        """
        # Simple model: slippage increases with order size relative to volume
        if volume_24h and volume_24h > 0:
            # Slippage % = (order_size / volume) ^ 2
            order_size_usd = quantity_to_sell * price
            size_ratio = order_size_usd / volume_24h
            slippage_pct = (size_ratio ** 2) * 100  # Exponential increase
        else:
            # No volume data - assume 0.5% base slippage
            slippage_pct = Decimal("0.5")
        
        slippage_pct = min(slippage_pct, Decimal("10"))  # Cap at 10%
        slippage_usd = order_size_usd * (slippage_pct / 100) if volume_24h else Decimal("0")
        
        return slippage_usd, slippage_pct
    
    @classmethod
    def suggest_sell_amount(
        cls,
        asset: str,
        total_quantity: Decimal,
        price: Decimal,
        volume_24h: Optional[Decimal] = None,
        max_order_pct_of_volume: Decimal = Decimal("2")
    ) -> Tuple[Decimal, str]:
        """
        Suggest maximum amount to sell without excessive slippage
        
        Args:
            asset: Asset code
            total_quantity: Total quantity held
            price: Current price
            volume_24h: 24h trading volume
            max_order_pct_of_volume: Max order as % of 24h volume (default 2%)
        
        Returns:
            (suggested_quantity: Decimal, reason: str)
        """
        if not volume_24h or volume_24h <= 0:
            # No volume data - conservative: suggest 10% of holdings
            suggested_qty = total_quantity * Decimal("0.1")
            return suggested_qty, "⚠️ No volume data - conservative 10% of holding"
        
        # Calculate max quantity based on volume
        max_value = volume_24h * (max_order_pct_of_volume / 100)
        suggested_qty = min(max_value / price, total_quantity)
        
        return suggested_qty, f"✓ Can sell up to {suggested_qty} without excess slippage (based on {max_order_pct_of_volume}% of 24h volume)"


# Example usage
if __name__ == "__main__":
    # Test BTC (very liquid)
    score, desc, slippage = LiquidityChecker.assess_liquidity(
        "BTC",
        market_cap=Decimal("1000000000000"),  # $1T
        volume_24h=Decimal("30000000000")  # $30B
    )
    print(f"BTC: {score}/100 - {desc} - {slippage}% slippage")
    
    # Test unknown small coin
    score, desc, slippage = LiquidityChecker.assess_liquidity(
        "XYZ",
        market_cap=Decimal("10000000"),  # $10M
        volume_24h=Decimal("500000")  # $500k
    )
    print(f"XYZ: {score}/100 - {desc} - {slippage}% slippage")
    
    # Test sell feasibility
    can_sell, reason = LiquidityChecker.can_sell_without_slippage(
        "BTC",
        Decimal("100"),  # Selling 100 BTC
        volume_24h=Decimal("30000000000")
    )
    print(f"Can sell 100 BTC: {can_sell} - {reason}")
