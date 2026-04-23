"""
Advanced Tax Engine Configuration
Manages settings for all premium features
"""

import os
from typing import Optional

class BaseConfig:
    """Base configuration"""
    
    # Database
    DATABASE_URL: Optional[str] = os.getenv(
        "DATABASE_URL",
        "sqlite:///./app.advanced_tax.db"
    )
    
    # Feature Flags
    TAX_LOSS_HARVESTING_ENABLED = True
    SMART_RECONCILIATION_ENABLED = True
    AUDIT_TRAIL_ENABLED = True
    
    # Tax Rules
    WASH_SALE_DAYS = 30
    TAX_YEAR_LOOKBACK = 5  # How many years back to analyze
    
    # Harvest Execution
    MAX_HARVEST_PER_USER = 100
    AUTO_EXECUTE_ENABLED = False  # Manual execution by default
    
    # Reconciliation
    MAX_RECONCILIATION_GAPS = 1000
    AUTO_MATCH_CONFIDENCE_THRESHOLD = 0.85  # 85% confidence required
    
    # Audit Export
    AUDIT_EXPORT_MAX_TRANSACTIONS = 100000
    AUDIT_EXPORT_FORMATS = ["pdf", "json", "excel"]
    AUDIT_EXPORT_PATH = os.path.join(os.getcwd(), "audit_exports")
    
    # Country-specific settings
    COUNTRY_TAX_RATES = {
        'MX': {'top_rate': 0.35, 'capital_gains_rate': 0.20},
        'BR': {'top_rate': 0.27, 'capital_gains_rate': 0.15},
        'AR': {'top_rate': 0.35, 'capital_gains_rate': 0.20},
        'CO': {'top_rate': 0.37, 'capital_gains_rate': 0.20},
        'PE': {'top_rate': 0.27, 'capital_gains_rate': 0.17},
        'CL': {'top_rate': 0.40, 'capital_gains_rate': 0.20},
    }
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Caching
    CACHE_ENABLED = True
    CACHE_TTL_SECONDS = 3600  # 1 hour
    
    # API
    API_TIMEOUT = 30  # seconds
    MAX_PORTFOLIO_SIZE = 10000  # Max assets per user


class DevelopmentConfig(BaseConfig):
    """Development settings"""
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """Testing settings"""
    DEBUG = True
    TESTING = True
    DATABASE_URL = "sqlite:///:memory:"
    AUTO_EXECUTE_ENABLED = False


class ProductionConfig(BaseConfig):
    """Production settings"""
    DEBUG = False
    TESTING = False
    # In production, DATABASE_URL must be set via env var
    # to use PostgreSQL or other production database


def get_config() -> BaseConfig:
    """Get config based on environment"""
    env = os.getenv("ENV", "development")
    
    if env == "testing":
        return TestingConfig()
    elif env == "production":
        return ProductionConfig()
    else:
        return DevelopmentConfig()


# Export current config
Config = get_config()
