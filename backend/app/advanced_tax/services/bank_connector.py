"""
Open Banking Integration - Bank Account Connectors
Integrates with Nubank, Mercado Pago, Belo, Lemon (LATAM FinTech banks)
Enables full cycle crypto → fiat tracking for tax compliance
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BankType(str, Enum):
    """Supported LATAM FinTech banks"""
    NUBANK = "nubank"           # Brazil's largest digital bank
    MERCADO_PAGO = "mercado_pago"  # Argentina, Brazil, Mexico
    BELO = "belo"               # Argentina digital bank
    LEMON = "lemon"             # Mexico digital bank
    CUSTOM_API = "custom_api"   # Generic Open Banking API


class TransactionType(str, Enum):
    """Bank transaction types"""
    DEPOSIT = "deposit"         # Money in (from crypto withdrawal)
    WITHDRAWAL = "withdrawal"   # Money out
    TRANSFER = "transfer"       # P2P transfer
    FEE = "fee"                 # Bank fees
    INTEREST = "interest"       # Interest earned
    DIVIDEND = "dividend"       # Dividends


@dataclass
class BankTransaction:
    """Bank transaction record"""
    id: str                              # Unique transaction ID
    account_id: str                      # Bank account ID
    date: datetime                       # Transaction date
    type: TransactionType
    amount: Decimal                      # Transaction amount (always positive)
    currency: str                        # Currency (BRL, ARS, MXN, etc.)
    description: str                     # Transaction description
    counterparty: str                    # Who money from/to
    balance_after: Optional[Decimal] = None  # Account balance after transaction
    
    # Matching
    matched_crypto_transaction_id: Optional[str] = None  # Linked crypto withdrawal
    matched_confidence: float = 0.0      # Match confidence 0-1
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'date': self.date.isoformat(),
            'type': self.type.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'description': self.description,
            'counterparty': self.counterparty,
            'matched_crypto_transaction_id': self.matched_crypto_transaction_id,
            'matched_confidence': self.matched_confidence,
        }


@dataclass
class BankAccount:
    """Bank account record"""
    id: str
    user_id: str
    bank_type: BankType
    account_number: str
    account_name: str
    currency: str
    balance: Decimal
    
    # Credentials (encrypted in real impl)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    
    # Metadata
    connected_at: datetime = field(default_factory=datetime.now)
    last_sync: Optional[datetime] = None
    sync_status: str = "pending"  # pending, syncing, synced, error
    
    def to_dict(self):
        return {
            'id': self.id,
            'bank_type': self.bank_type.value,
            'account_number': self.account_number[-4:],  # Only last 4 digits!
            'account_name': self.account_name,
            'currency': self.currency,
            'balance': float(self.balance),
            'connected_at': self.connected_at.isoformat(),
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'sync_status': self.sync_status,
        }


class BankConnector(ABC):
    """
    Abstract base class for bank connectors
    Each bank implements its own OAuth + API
    """
    
    def __init__(self, bank_type: BankType):
        self.bank_type = bank_type
        logger.info(f"[Bank Connector] {bank_type.value.upper()} initialized")
    
    @abstractmethod
    def authenticate(self, credentials: Dict) -> bool:
        """
        Authenticate with bank (OAuth2 usually)
        
        Args:
            credentials: {
                'email': 'user@example.com',
                'password': '***',  # or auth_token
                'api_key': '...',
                'api_secret': '...'
            }
        
        Returns:
            True if successful
        """
        pass
    
    @abstractmethod
    def get_accounts(self) -> List[BankAccount]:
        """Get list of user's bank accounts"""
        pass
    
    @abstractmethod
    def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        """
        Get transactions for account in date range
        
        Most recent APIs require OAuth2 + Personal Data Access consent
        """
        pass
    
    @abstractmethod
    def sync_transactions(self, account: BankAccount) -> Tuple[int, bool]:
        """
        Sync all transactions for account
        
        Returns:
            (num_transactions_fetched, success)
        """
        pass
    
    def get_deposit_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        """Get only deposit transactions (money in)"""
        all_txns = self.get_transactions(account_id, start_date, end_date)
        return [t for t in all_txns if t.type == TransactionType.DEPOSIT]


class NubankConnector(BankConnector):
    """
    Nubank Open Banking Connector (Brazil)
    Most popular: 70+ million users
    
    API: Uses OAuth2 + Pix (instant payments)
    """
    
    API_BASE = "https://api.nubank.com.br"
    
    def __init__(self):
        super().__init__(BankType.NUBANK)
        self.access_token = None
        self.user_id = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """
        Nubank OAuth2 flow
        In real implementation: Use proper OAuth2 library
        """
        logger.info("[Nubank] Authenticating...")
        
        try:
            # Step 1: Login with email/password
            email = credentials.get('email')
            password = credentials.get('password')
            
            if not email or not password:
                logger.error("[Nubank] Missing email/password")
                return False
            
            # Step 2: Get access token (mocked)
            # In real: POST /oauth2/token with credentials
            self.access_token = f"nubank_token_{email[:4]}"  # Mocked
            self.user_id = f"nubank_user_{email[:4]}"
            
            logger.info(f"[Nubank] ✅ Authenticated: {email}")
            return True
        
        except Exception as e:
            logger.error(f"[Nubank] ❌ Auth failed: {str(e)}")
            return False
    
    def get_accounts(self) -> List[BankAccount]:
        """Get Nubank accounts"""
        logger.info("[Nubank] Fetching accounts...")
        
        if not self.access_token:
            logger.error("[Nubank] Not authenticated")
            return []
        
        try:
            # In real: GET /accounts with bearer token
            accounts = [
                BankAccount(
                    id=f"nubank_acc_{self.user_id}",
                    user_id=self.user_id,
                    bank_type=BankType.NUBANK,
                    account_number="12345678",
                    account_name="Nubank Checking",
                    currency="BRL",
                    balance=Decimal("50000.00"),
                    api_key=self.access_token
                )
            ]
            
            logger.info(f"[Nubank] ✅ Found {len(accounts)} accounts")
            return accounts
        
        except Exception as e:
            logger.error(f"[Nubank] ❌ Failed to fetch accounts: {str(e)}")
            return []
    
    def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        """Get Nubank transactions"""
        logger.info(f"[Nubank] Fetching {(end_date - start_date).days}d of transactions...")
        
        if not self.access_token:
            return []
        
        try:
            # In real: GET /accounts/{account_id}/transactions?start_date=...
            # With filters and pagination
            
            transactions = [
                BankTransaction(
                    id=f"nubank_txn_{self.user_id}_1",
                    account_id=account_id,
                    date=datetime.now() - timedelta(days=1),
                    type=TransactionType.DEPOSIT,
                    amount=Decimal("5000.00"),
                    currency="BRL",
                    description="Crypto withdrawal - Binance",
                    counterparty="Binance",
                    balance_after=Decimal("45000.00")
                ),
                BankTransaction(
                    id=f"nubank_txn_{self.user_id}_2",
                    account_id=account_id,
                    date=datetime.now() - timedelta(days=2),
                    type=TransactionType.FEE,
                    amount=Decimal("10.00"),
                    currency="BRL",
                    description="Transfer fee",
                    counterparty="Nubank",
                    balance_after=Decimal("40000.00")
                )
            ]
            
            logger.info(f"[Nubank] ✅ Found {len(transactions)} transactions")
            return transactions
        
        except Exception as e:
            logger.error(f"[Nubank] ❌ Failed to fetch transactions: {str(e)}")
            return []
    
    def sync_transactions(self, account: BankAccount) -> Tuple[int, bool]:
        """Sync all transactions"""
        end_date = datetime.now()
        start_date = account.last_sync or end_date - timedelta(days=90)
        
        try:
            txns = self.get_transactions(account.id, start_date, end_date)
            logger.info(f"[Nubank] ✅ Synced {len(txns)} transactions")
            return (len(txns), True)
        except Exception as e:
            logger.error(f"[Nubank] ❌ Sync failed: {str(e)}")
            return (0, False)


class MercadoPagoConnector(BankConnector):
    """
    Mercado Pago Open Banking Connector
    Available in: Argentina, Brazil, Mexico, Colombia
    """
    
    API_BASE = "https://api.mercadopago.com"
    
    def __init__(self):
        super().__init__(BankType.MERCADO_PAGO)
        self.access_token = None
    
    def authenticate(self, credentials: Dict) -> bool:
        """Mercado Pago OAuth2"""
        logger.info("[Mercado Pago] Authenticating...")
        
        try:
            api_token = credentials.get('api_token')
            if not api_token:
                logger.error("[Mercado Pago] Missing api_token")
                return False
            
            self.access_token = api_token
            logger.info("[Mercado Pago] ✅ Authenticated")
            return True
        
        except Exception as e:
            logger.error(f"[Mercado Pago] ❌ Auth failed: {str(e)}")
            return False
    
    def get_accounts(self) -> List[BankAccount]:
        """Get Mercado Pago accounts"""
        if not self.access_token:
            return []
        
        logger.info("[Mercado Pago] Fetching accounts...")
        
        accounts = [
            BankAccount(
                id="mp_acc_1",
                user_id="mp_user_1",
                bank_type=BankType.MERCADO_PAGO,
                account_number="87654321",
                account_name="Mercado Pago Wallet",
                currency="ARS",
                balance=Decimal("150000.00"),
                api_key=self.access_token
            )
        ]
        
        return accounts
    
    def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        """Get Mercado Pago transactions"""
        if not self.access_token:
            return []
        
        transactions = [
            BankTransaction(
                id="mp_txn_1",
                account_id=account_id,
                date=datetime.now(),
                type=TransactionType.DEPOSIT,
                amount=Decimal("10000.00"),
                currency="ARS",
                description="Crypto sale proceeds",
                counterparty="Lemon - Argentina"
            )
        ]
        
        return transactions
    
    def sync_transactions(self, account: BankAccount) -> Tuple[int, bool]:
        """Sync Mercado Pago transactions"""
        end_date = datetime.now()
        start_date = account.last_sync or end_date - timedelta(days=90)
        
        try:
            txns = self.get_transactions(account.id, start_date, end_date)
            logger.info(f"[Mercado Pago] ✅ Synced {len(txns)} transactions")
            return (len(txns), True)
        except Exception as e:
            logger.error(f"[Mercado Pago] ❌ Sync failed: {str(e)}")
            return (0, False)


class LemonConnector(BankConnector):
    """
    Lemon Open Banking Connector (Mexico)
    Fast-growing fintech
    """
    
    API_BASE = "https://api.lemon.mx"
    
    def __init__(self):
        super().__init__(BankType.LEMON)
        self.access_token = None
    
    def authenticate(self, credentials: Dict) -> bool:
        logger.info("[Lemon] Authenticating...")
        
        try:
            api_key = credentials.get('api_key')
            if not api_key:
                return False
            
            self.access_token = api_key
            logger.info("[Lemon] ✅ Authenticated")
            return True
        except Exception as e:
            logger.error(f"[Lemon] ❌ Auth failed: {str(e)}")
            return False
    
    def get_accounts(self) -> List[BankAccount]:
        if not self.access_token:
            return []
        
        accounts = [
            BankAccount(
                id="lemon_acc_1",
                user_id="lemon_user_1",
                bank_type=BankType.LEMON,
                account_number="99887766",
                account_name="Lemon Checking",
                currency="MXN",
                balance=Decimal("200000.00"),
                api_key=self.access_token
            )
        ]
        
        return accounts
    
    def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[BankTransaction]:
        if not self.access_token:
            return []
        
        transactions = [
            BankTransaction(
                id="lemon_txn_1",
                account_id=account_id,
                date=datetime.now(),
                type=TransactionType.DEPOSIT,
                amount=Decimal("25000.00"),
                currency="MXN",
                description="Binance withdrawal - MXN",
                counterparty="Binance"
            )
        ]
        
        return transactions
    
    def sync_transactions(self, account: BankAccount) -> Tuple[int, bool]:
        end_date = datetime.now()
        start_date = account.last_sync or end_date - timedelta(days=90)
        
        try:
            txns = self.get_transactions(account.id, start_date, end_date)
            logger.info(f"[Lemon] ✅ Synced {len(txns)} transactions")
            return (len(txns), True)
        except Exception as e:
            logger.error(f"[Lemon] ❌ Sync failed: {str(e)}")
            return (0, False)


class BankConnectorFactory:
    """Factory for creating bank connectors"""
    
    _connectors = {
        BankType.NUBANK: NubankConnector,
        BankType.MERCADO_PAGO: MercadoPagoConnector,
        BankType.LEMON: LemonConnector,
        # BankType.BELO: BeloConnector,  # Can add later
    }
    
    @classmethod
    def create(cls, bank_type: BankType) -> Optional[BankConnector]:
        """Create connector for bank type"""
        connector_class = cls._connectors.get(bank_type)
        
        if not connector_class:
            logger.error(f"❌ Unsupported bank type: {bank_type}")
            return None
        
        return connector_class()
    
    @classmethod
    def register(cls, bank_type: BankType, connector_class):
        """Register new bank connector"""
        cls._connectors[bank_type] = connector_class
        logger.info(f"✅ Registered {bank_type.value}")


class BankManager:
    """Manages multiple bank accounts"""
    
    def __init__(self):
        self.accounts: Dict[str, BankAccount] = {}
        self.connectors: Dict[BankType, BankConnector] = {}
    
    def connect_bank(
        self,
        bank_type: BankType,
        credentials: Dict
    ) -> Optional[BankAccount]:
        """Connect to a bank"""
        
        logger.info(f"🔌 Connecting to {bank_type.value}...")
        
        # Get or create connector
        if bank_type not in self.connectors:
            connector = BankConnectorFactory.create(bank_type)
            if not connector:
                return None
            self.connectors[bank_type] = connector
        else:
            connector = self.connectors[bank_type]
        
        # Authenticate
        if not connector.authenticate(credentials):
            logger.error(f"❌ Failed to authenticate with {bank_type.value}")
            return None
        
        # Get accounts
        accounts = connector.get_accounts()
        if not accounts:
            logger.error(f"❌ No accounts found for {bank_type.value}")
            return None
        
        # Store first account
        account = accounts[0]
        self.accounts[account.id] = account
        
        logger.info(f"✅ Connected: {account.account_name} ({account.currency})")
        return account
    
    def sync_all(self) -> Dict[str, Tuple[int, bool]]:
        """Sync all connected accounts"""
        results = {}
        
        for account_id, account in self.accounts.items():
            connector = self.connectors.get(account.bank_type)
            if not connector:
                results[account_id] = (0, False)
                continue
            
            num_txns, success = connector.sync_transactions(account)
            results[account_id] = (num_txns, success)
            
            if success:
                account.last_sync = datetime.now()
                account.sync_status = "synced"
            else:
                account.sync_status = "error"
        
        return results
    
    def get_deposit_transactions(
        self,
        days: int = 90
    ) -> List[BankTransaction]:
        """Get all deposits from all connected accounts"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        all_deposits = []
        
        for account in self.accounts.values():
            connector = self.connectors.get(account.bank_type)
            if not connector:
                continue
            
            txns = connector.get_deposit_transactions(
                account.id,
                start_date,
                end_date
            )
            all_deposits.extend(txns)
        
        return all_deposits
    
    def get_connected_banks(self) -> List[Dict]:
        """Get list of connected banks"""
        return [account.to_dict() for account in self.accounts.values()]


# Example usage
if __name__ == "__main__":
    print("\n" + "="*60)
    print("OPEN BANKING INTEGRATION DEMO")
    print("="*60 + "\n")
    
    # Create manager
    bank_manager = BankManager()
    
    # Connect to Nubank (Brazil)
    print("1️⃣ CONNECTING TO NUBANK (Brazil)")
    nubank_account = bank_manager.connect_bank(
        BankType.NUBANK,
        {'email': 'user@example.com', 'password': 'secret'}
    )
    print()
    
    # Connect to Mercado Pago (Argentina)
    print("2️⃣ CONNECTING TO MERCADO PAGO (Argentina)")
    mp_account = bank_manager.connect_bank(
        BankType.MERCADO_PAGO,
        {'api_token': 'mp_token_123'}
    )
    print()
    
    # Connect to Lemon (Mexico)
    print("3️⃣ CONNECTING TO LEMON (Mexico)")
    lemon_account = bank_manager.connect_bank(
        BankType.LEMON,
        {'api_key': 'lemon_key_456'}
    )
    print()
    
    # Sync all
    print("4️⃣ SYNCING ALL ACCOUNTS")
    results = bank_manager.sync_all()
    for acc_id, (num_txns, success) in results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {acc_id}: {num_txns} transactions")
    print()
    
    # Get all deposits
    print("5️⃣ DEPOSITS FROM ALL BANKS (Last 90 days)")
    deposits = bank_manager.get_deposit_transactions(days=90)
    for dep in deposits:
        print(f"   {dep.date.strftime('%Y-%m-%d')}: {dep.amount} {dep.currency} from {dep.counterparty}")
    print()
    
    # Connected banks summary
    print("6️⃣ CONNECTED BANKS SUMMARY")
    banks = bank_manager.get_connected_banks()
    for bank in banks:
        print(f"   {bank['bank_type'].upper()}: {bank['account_name']} ({bank['currency']})")
        print(f"     Balance: {bank['balance']} {bank['currency']}")
    
    print("\n" + "="*60)
    print("✅ OPEN BANKING DEMO COMPLETE")
    print("="*60 + "\n")
