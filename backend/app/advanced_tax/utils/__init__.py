"""
Advanced Tax Engine - Utils & Exceptions
Custom exceptions and utilities shared across modules
"""

from typing import Dict, Any
from enum import Enum


# =====================
# CUSTOM EXCEPTIONS
# =====================

class AdvancedTaxEngineException(Exception):
    """Base exception for Advanced Tax Engine"""
    pass


class ServiceException(AdvancedTaxEngineException):
    """Exception in service layer"""
    pass


class ValidationException(AdvancedTaxEngineException):
    """Input validation failed"""
    pass


class ReconciliationException(AdvancedTaxEngineException):
    """Reconciliation engine error"""
    pass


class AuditException(AdvancedTaxEngineException):
    """Audit generation error"""
    pass


class HarvestException(AdvancedTaxEngineException):
    """Tax-loss harvest error"""
    pass


class DatabaseException(AdvancedTaxEngineException):
    """Database access error"""
    pass


# =====================
# ENUMS
# =====================

class HarvestStatus(str, Enum):
    """Tax-loss harvest status"""
    IDENTIFIED = "identified"      # Opportunity found
    RECOMMENDED = "recommended"    # Shown to user
    EXECUTING = "executing"        # Being executed
    EXECUTED = "executed"          # Sold
    COMPLETED = "completed"        # Rebuy done, locked in
    CANCELLED = "cancelled"        # User cancelled


class ReconciliationStatus(str, Enum):
    """Reconciliation status"""
    PENDING = "pending"            # Awaiting action
    MATCHED = "matched"            # Auto-matched
    MANUAL_ENTRY = "manual_entry"  # User set manually
    VERIFIED = "verified"          # Verified by user
    DISMISSED = "dismissed"        # User dismissed


class AuditStatus(str, Enum):
    """Audit package status"""
    GENERATING = "generating"
    READY = "ready"
    REVIEWING = "reviewing"
    VERIFIED = "verified"
    APPROVED = "approved"
    EXPORTED = "exported"


class RiskLevel(str, Enum):
    """Asset risk assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TransactionType(str, Enum):
    """Tax transaction types"""
    BUY = "BUY"
    SELL = "SELL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    RECEIVE = "RECEIVE"
    SEND = "SEND"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    AIRDROP = "AIRDROP"
    MINING = "MINING"
    STAKING = "STAKING"


# =====================
# CONSTANTS
# =====================

DEFAULT_ASSET_DECIMALS = {
    'BTC': 8,
    'ETH': 18,
    'USDT': 6,
    'USDC': 6,
    'DAI': 18,
    'WETH': 18,
}

SUPPORTED_COUNTRIES = [
    'MX', 'BR', 'AR', 'CO', 'PE', 'CL',
    'GT', 'EC', 'UY', 'CR', 'HN', 'BO'
]

TAX_FORMS_BY_COUNTRY = {
    'MX': ['SAT-ISR', 'SAT-IVA', 'CEDULAR'],
    'BR': ['IRPF', 'DARF', 'ECF'],
    'AR': ['AFIP-GANANCIAS', 'AFIP-IVA'],
    'CO': ['DIAN-1010', 'DIAN-2650'],
    'PE': ['SUNAT-UIT', 'SUNAT-3'],
    'CL': ['SII-F22', 'SII-F29'],
}


# =====================
# HELPER FUNCTIONS
# =====================

def normalize_asset(asset: str) -> str:
    """Normalize asset symbol to uppercase"""
    return asset.upper().strip()


def format_currency(value: float, country: str = 'MX') -> str:
    """Format value as currency string"""
    currency_symbols = {
        'MX': 'MXN',
        'BR': 'BRL',
        'AR': 'ARS',
        'CO': 'COP',
        'PE': 'PEN',
        'CL': 'CLP',
    }
    symbol = currency_symbols.get(country, 'USD')
    return f"{value:,.2f} {symbol}"


def validate_user_id(user_id: int) -> bool:
    """Validate user_id is positive integer"""
    return isinstance(user_id, int) and user_id > 0


def validate_asset_symbol(asset: str) -> bool:
    """Validate asset symbol format"""
    asset = asset.upper()
    return len(asset) >= 2 and len(asset) <= 12 and asset.isalnum()


def validate_country(country: str) -> bool:
    """Validate country code"""
    return country.upper() in SUPPORTED_COUNTRIES


def calculate_percentage_change(start: float, end: float) -> float:
    """Calculate percentage change from start to end"""
    if start == 0:
        return 0
    return ((end - start) / start) * 100


class Logger:
    """Structured logging for Advanced Tax Engine"""
    
    @staticmethod
    def log_event(event_type: str, data: Dict[str, Any]) -> None:
        """Log structured event"""
        # In production, this would send to monitoring system
        event = {
            'type': f"ADVANCED_TAX_ENGINE_{event_type}",
            'data': data,
        }
        print(f"[EVENT] {event}")
