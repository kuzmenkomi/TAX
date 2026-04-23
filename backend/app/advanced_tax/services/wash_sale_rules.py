"""
Wash-Sale Rules by Country
Country-specific tax loss harvesting restrictions
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from decimal import Decimal


class WashSaleRules:
    """
    Manages country-specific wash-sale rules
    
    Wash Sale = Selling asset at loss + buying same/similar asset within restriction period
    Tax authority doesn't allow loss deduction if this happens
    """
    
    # Country-specific rules
    RULES = {
        # 🇺🇸 USA - IRS Wash Sale Rule
        "US": {
            "restriction_days": 30,  # 30 days before + 30 days after = 61-day window
            "rule_name": "IRS Wash Sale Rule",
            "description": "Cannot buy same/substantially identical security 30 days before or after sale",
            "similar_asset_check": True,  # Need to check for "substantially identical"
            "applies_to": "all_assets",
            "enforcement": "automatic",
        },
        
        # 🇩🇪 Germany - Einjährige Haltedauer
        "DE": {
            "restriction_days": 365,  # 1 year holding period for capital gains
            "rule_name": "Holding Period Tax",
            "description": "Capital gains are tax-free if held >1 year (no wash sale, but holding period)",
            "similar_asset_check": False,
            "applies_to": "all_assets",
            "enforcement": "tax_free_after_period",
        },
        
        # 🇧🇷 Brazil - 30-day restriction but different structure
        "BR": {
            "restriction_days": 30,  
            "rule_name": "Brazilian Wash Sale",
            "description": "Cannot buy same asset for 30 days. Day-trading exceptions exist.",
            "similar_asset_check": True,
            "applies_to": "all_assets",
            "applies_to_exchanges": ["spot"],  # May differ for derivatives
            "enforcement": "mandatory",
        },
        
        # 🇲🇽 Mexico - no official wash sale (but track for compliance)
        "MX": {
            "restriction_days": 0,  # No wash sale rule but monitor
            "rule_name": "No Wash Sale (Monitor Only)",
            "description": "Mexico has no official wash-sale rule, but track for international compliance",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
        
        # 🇦🇷 Argentina
        "AR": {
            "restriction_days": 0,
            "rule_name": "No Wash Sale (Argentine Tax)",
            "description": "Argentina tax code does not have wash-sale restrictions",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
        
        # 🇨🇴 Colombia
        "CO": {
            "restriction_days": 30,
            "rule_name": "Colombian Wash Sale",
            "description": "30-day restriction on repurchase of same asset",
            "similar_asset_check": True,
            "applies_to": "crypto",  # May not apply to crypto specifically
            "enforcement": "recommended",
        },
        
        # 🇵🇪 Peru
        "PE": {
            "restriction_days": 0,
            "rule_name": "No Wash Sale",
            "description": "Peru currently has no wash-sale restrictions",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
        
        # 🇨🇭 Switzerland
        "CH": {
            "restriction_days": 30,
            "rule_name": "Swiss Tax Loss Rule",
            "description": "30-day restriction for tax-loss harvesting",
            "similar_asset_check": True,
            "applies_to": "all_assets",
            "enforcement": "cantonal",  # Varies by canton
        },
        
        # 🇬🇧 UK - Bed & Breakfast Rule
        "UK": {
            "restriction_days": 0,  # Old rule abolished in 2024, now can rebuy same day
            "rule_name": "Bed & Breakfast (Abolished)",
            "description": "Previously 30-day rule, now abolished - can rebuy immediately",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
            "reformed": "2024",
        },
        
        # 🇸🇬 Singapore
        "SG": {
            "restriction_days": 0,
            "rule_name": "No Wash Sale",
            "description": "Singapore has no wash-sale restrictions",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
        
        # 🇭🇰 Hong Kong
        "HK": {
            "restriction_days": 0,
            "rule_name": "No Wash Sale",
            "description": "Hong Kong tax code has no wash-sale restrictions",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
        
        # 🇯🇵 Japan
        "JP": {
            "restriction_days": 0,
            "rule_name": "No Wash Sale",
            "description": "Japan has no wash-sale restrictions",
            "similar_asset_check": False,
            "applies_to": "none",
            "enforcement": "none",
        },
    }
    
    @classmethod
    def get_wash_sale_rule(cls, country: str) -> Dict:
        """Get wash-sale rule for country"""
        return cls.RULES.get(country.upper(), cls.RULES["US"])  # Default to USA
    
    @classmethod
    def check_wash_sale_violation(
        cls, 
        country: str, 
        last_sell_date: Optional[datetime],
        proposed_rebuy_date: datetime = None
    ) -> Tuple[bool, int, str]:
        """
        Check if rebuy would violate wash-sale rule
        
        Args:
            country: Country code (US, BR, MX, etc.)
            last_sell_date: Date of the loss-harvesting sell
            proposed_rebuy_date: When user wants to rebuy (default: today)
        
        Returns:
            (is_violation: bool, days_remaining: int, reason: str)
        """
        if proposed_rebuy_date is None:
            proposed_rebuy_date = datetime.now()
        
        rule = cls.get_wash_sale_rule(country)
        restriction_days = rule["restriction_days"]
        
        if restriction_days == 0:
            # No wash-sale rule in this country
            return False, 0, f"✓ {country} has no wash-sale restriction"
        
        if last_sell_date is None:
            return False, 0, "No previous sale found"
        
        days_since_sell = (proposed_rebuy_date - last_sell_date).days
        days_remaining = restriction_days - days_since_sell
        
        if days_remaining > 0:
            return True, days_remaining, (
                f"⚠️ {country} wash-sale rule: cannot rebuy for {days_remaining} more days "
                f"(rule: {rule['rule_name']}). Loss deduction at risk if violated."
            )
        
        return False, 0, f"✓ Can rebuy - {restriction_days}-day period elapsed"
    
    @classmethod
    def get_rebuy_date(cls, country: str, sell_date: datetime) -> datetime:
        """Calculate earliest date you can rebuy without violating wash-sale"""
        rule = cls.get_wash_sale_rule(country)
        restriction_days = rule["restriction_days"]
        return sell_date + timedelta(days=restriction_days + 1)
    
    @classmethod
    def get_similar_assets(cls, asset: str, country: str) -> list:
        """
        Get list of "substantially identical" assets (IRS definition)
        Different by country interpretation
        
        Args:
            asset: Asset code (BTC, ETH, etc.)
            country: Country code
        
        Returns:
            List of similar assets to avoid
        """
        # In crypto, usually just the same coin on different chains
        # BTC on Bitcoin = same as BTC on Ethereum (wrapped)?
        # This is gray area in USA - conservative approach treats as same
        
        similar_mappings = {
            "BTC": ["BTC", "WBTC", "BTCB"],  # Bitcoin, Wrapped BTC
            "ETH": ["ETH", "WETH"],  # Ethereum, Wrapped ETH
            "USDC": ["USDC", "USDC.e"],  # USDC on different chains
            "USDT": ["USDT", "USDT.e"],
        }
        
        return similar_mappings.get(asset.upper(), [asset])
    
    @classmethod
    def suggest_rebuy_asset(cls, harvested_asset: str, volatility_profile: str = "moderate") -> str:
        """
        Suggest alternative asset to rebuy (to maintain market exposure without wash-sale)
        
        Args:
            harvested_asset: What we just sold
            volatility_profile: "conservative", "moderate", "aggressive"
        
        Returns:
            Suggested asset to rebuy
        """
        alternatives = {
            "BTC": {
                "conservative": "GBTC",  # Bitcoin trust
                "moderate": "ETH",  # Ethereum for diversification
                "aggressive": "BCH",  # Bitcoin Cash for similar exposure
            },
            "ETH": {
                "conservative": "GETH",
                "moderate": "BTC",
                "aggressive": "SOL",
            },
            "ADA": {
                "conservative": "XRP",
                "moderate": "DOT",
                "aggressive": "DOGE",
            },
        }
        
        asset_upper = harvested_asset.upper()
        if asset_upper in alternatives:
            return alternatives[asset_upper].get(volatility_profile, asset_upper)
        
        # Default: suggest similar market cap asset
        return "ETH" if asset_upper != "ETH" else "BTC"


# Test the rules
if __name__ == "__main__":
    # Test USA
    sell_date = datetime.now() - timedelta(days=10)
    rebuy_date = datetime.now()
    is_violation, days_left, msg = WashSaleRules.check_wash_sale_violation("US", sell_date, rebuy_date)
    print(f"USA violation: {is_violation}, Days left: {days_left}")
    print(msg)
    
    # Test Mexico (no rule)
    is_violation, days_left, msg = WashSaleRules.check_wash_sale_violation("MX", sell_date, rebuy_date)
    print(f"\nMexico violation: {is_violation}, Days left: {days_left}")
    print(msg)
    
    # Test rebuy date
    rebuy = WashSaleRules.get_rebuy_date("US", sell_date)
    print(f"\nUS rebuy date: {rebuy.date()}")
