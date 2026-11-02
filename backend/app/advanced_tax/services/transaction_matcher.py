"""
Transaction Matching Engine - Crypto to Fiat
Links cryptocurrency withdrawals to bank deposits
Creates complete audit trail: Crypto → Exchange → Bank -> Fiat
"""

from typing import Any, List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MatchStatus(str, Enum):
    """Status of transaction match"""
    UNMATCHED = "unmatched"
    PENDING = "pending"
    MATCHED = "matched"
    PARTIAL_MATCH = "partial_match"
    FAILED = "failed"


@dataclass
class MatchingRule:
    """Rule for matching crypto withdrawal to bank deposit"""
    
    # Matching criteria
    amount_tolerance_pct: float = 1.0  # Allow 1% difference (fees)
    time_window_hours: int = 24  # Look for deposits within 24h
    counterparty_keywords: List[str] = field(default_factory=list)  # ['Binance', 'Kraken']
    
    # Exchange rates (for crypto↔fiat matching)
    exchange_rate_on_date: Optional[Decimal] = None
    
    def to_dict(self):
        return {
            'amount_tolerance_pct': self.amount_tolerance_pct,
            'time_window_hours': self.time_window_hours,
            'counterparty_keywords': self.counterparty_keywords,
        }


@dataclass
class TransactionMatch:
    """Match between crypto withdrawal and bank deposit"""
    
    crypto_withdrawal_id: str
    bank_deposit_id: str
    
    crypto_amount: Decimal  # In crypto (e.g., 1.5 BTC)
    crypto_currency: str    # BTC, ETH, USDC, etc.
    fiat_amount: Decimal    # In fiat (e.g., 45,000 BRL)
    fiat_currency: str      # BRL, ARS, MXN, etc.
    
    exchange_rate: Decimal  # 1 crypto unit = X fiat
    fees_paid: Decimal      # Transaction fees (in fiat)
    slippage: Decimal       # Price difference (in fiat)
    
    crypto_date: datetime   # When crypto withdrawal happened
    fiat_date: datetime     # When bank deposit arrived
    
    time_delta_hours: float = 0.0  # Hours between withdrawal and deposit
    confidence: float = 1.0         # Match confidence 0-1
    match_status: MatchStatus = MatchStatus.MATCHED
    notes: str = ""
    
    def to_dict(self):
        return {
            'crypto_withdrawal_id': self.crypto_withdrawal_id,
            'bank_deposit_id': self.bank_deposit_id,
            'crypto_amount': float(self.crypto_amount),
            'crypto_currency': self.crypto_currency,
            'fiat_amount': float(self.fiat_amount),
            'fiat_currency': self.fiat_currency,
            'exchange_rate': float(self.exchange_rate),
            'fees_paid': float(self.fees_paid),
            'slippage': float(self.slippage),
            'crypto_date': self.crypto_date.isoformat(),
            'fiat_date': self.fiat_date.isoformat(),
            'time_delta_hours': self.time_delta_hours,
            'confidence': self.confidence,
            'match_status': self.match_status.value,
            'notes': self.notes,
        }


@dataclass
class CryptoWithdrawal:
    """Cryptocurrency withdrawal from exchange"""
    
    id: str
    exchange: str           # 'binance', 'kraken', 'coinbase'
    asset: str              # 'BTC', 'ETH', 'USDC'
    amount: Decimal
    amount_in_usd: Decimal  # Amount converted to USD at withdrawal time
    date_time: datetime
    destination_address: str  # Wallet address
    tx_hash: str            # Blockchain transaction hash
    status: str = "completed"  # pending, completed, failed
    
    matched_bank_deposit_id: Optional[str] = None
    match_confidence: float = 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'exchange': self.exchange,
            'asset': self.asset,
            'amount': float(self.amount),
            'amount_in_usd': float(self.amount_in_usd),
            'date_time': self.date_time.isoformat(),
            'destination_address': self.destination_address,
            'tx_hash': self.tx_hash,
            'matched_bank_deposit_id': self.matched_bank_deposit_id,
            'match_confidence': self.match_confidence,
        }


class TransactionMatchingEngine:
    """
    Smart matching engine:
    1. Crypto withdrawal → Stable coin conversion (if needed)
    2. Stable coin withdrawal to fiat on-ramp
    3. Bank deposit arrives
    
    Tracks complete cycle for tax compliance
    """
    
    def __init__(self):
        self.matches: Dict[str, TransactionMatch] = {}
        self.unmatched_withdrawals: List[CryptoWithdrawal] = []
        self.matching_history: List[Dict] = []
    
    def match_withdrawal_to_deposit(
        self,
        withdrawal: CryptoWithdrawal,
        deposits: List,  # List of BankTransaction
        rules: MatchingRule = None
    ) -> Optional[TransactionMatch]:
        """
        Find matching bank deposit for crypto withdrawal
        
        Matching algorithm:
        1. Filter deposits by time window
        2. Calculate expected fiat amount (crypto → fiat conversion)
        3. Find deposits within amount tolerance
        4. Score by confidence
        """
        
        if rules is None:
            rules = MatchingRule()
        
        logger.info(f"🔍 Matching crypto withdrawal: {withdrawal.asset} ({withdrawal.amount})")
        
        # Get USD value of withdrawal
        withdrawal_usd = withdrawal.amount_in_usd
        
        # Find candidates within time window
        candidates = []
        
        for deposit in deposits:
            # Time window check
            time_delta = (deposit.date - withdrawal.date_time).total_seconds() / 3600
            if abs(time_delta) > rules.time_window_hours:
                continue
            
            # Only deposits (not withdrawals)
            if deposit.type.value != "deposit":
                continue
            
            # Convert fiat to USD equivalent for comparison
            fiat_to_usd = self._get_exchange_rate(
                deposit.currency,
                "USD",
                deposit.date
            )
            deposit_usd = deposit.amount * fiat_to_usd
            
            # Amount tolerance check (allow for fees/slippage)
            amount_diff_pct = abs(deposit_usd - withdrawal_usd) / withdrawal_usd * 100
            
            if amount_diff_pct <= rules.amount_tolerance_pct:
                # Counterparty check (is it from expected exchange?)
                counterparty_match = any(
                    keyword.lower() in deposit.counterparty.lower()
                    for keyword in rules.counterparty_keywords
                ) if rules.counterparty_keywords else True
                
                if counterparty_match:
                    # Calculate confidence
                    confidence = 1.0 - (amount_diff_pct / 100)
                    confidence *= (1.0 - abs(time_delta) / rules.time_window_hours)
                    
                    candidates.append({
                        'deposit': deposit,
                        'time_delta': time_delta,
                        'amount_diff_pct': amount_diff_pct,
                        'confidence': max(0, confidence),
                    })
        
        if not candidates:
            logger.warning(f"❌ No matching deposit found")
            self.unmatched_withdrawals.append(withdrawal)
            return None
        
        # Select best match (highest confidence)
        best = max(candidates, key=lambda c: c['confidence'])
        deposit = best['deposit']
        
        logger.info(f"✅ Found match: {deposit.amount} {deposit.currency}")
        logger.info(f"   Confidence: {best['confidence']:.1%}")
        logger.info(f"   Time delta: {best['time_delta']:.1f} hours")
        
        # Create match
        match = TransactionMatch(
            crypto_withdrawal_id=withdrawal.id,
            bank_deposit_id=deposit.id,
            crypto_amount=withdrawal.amount,
            crypto_currency=withdrawal.asset,
            fiat_amount=deposit.amount,
            fiat_currency=deposit.currency,
            exchange_rate=deposit.amount / withdrawal.amount_in_usd,
            fees_paid=Decimal("0"),  # Would calculate from actual vs expected
            slippage=deposit.amount - withdrawal_usd,
            crypto_date=withdrawal.date_time,
            fiat_date=deposit.date,
            time_delta_hours=best['time_delta'],
            confidence=best['confidence'],
            match_status=MatchStatus.MATCHED
        )
        
        self.matches[match.crypto_withdrawal_id] = match
        withdrawal.matched_bank_deposit_id = deposit.id
        withdrawal.match_confidence = best['confidence']
        
        return match
    
    def match_batch(
        self,
        withdrawals: List[CryptoWithdrawal],
        deposits: List,  # BankTransactions
        rules: MatchingRule = None
    ) -> Dict[str, Any]:
        """Match batch of withdrawals to deposits"""
        
        logger.info(f"📊 Running batch matching: {len(withdrawals)} withdrawals → {len(deposits)} deposits")
        
        results = {
            'total_withdrawals': len(withdrawals),
            'total_deposits': len(deposits),
            'matched': 0,
            'unmatched': 0,
            'matches': [],
            'unmatched_list': [],
        }
        
        for withdrawal in withdrawals:
            match = self.match_withdrawal_to_deposit(withdrawal, deposits, rules)
            
            if match:
                results['matched'] += 1
                results['matches'].append(match.to_dict())
            else:
                results['unmatched'] += 1
                results['unmatched_list'].append({
                    'withdrawal_id': withdrawal.id,
                    'asset': withdrawal.asset,
                    'amount': float(withdrawal.amount),
                    'date': withdrawal.date_time.isoformat(),
                })
        
        match_rate = (results['matched'] / len(withdrawals) * 100) if withdrawals else 0
        logger.info(f"✅ Batch complete: {results['matched']} matched ({match_rate:.1f}%)")
        
        return results
    
    def get_unmatched_withdrawals(self) -> List[Dict]:
        """Get withdrawals that couldn't be matched to deposits"""
        return [w.to_dict() for w in self.unmatched_withdrawals]
    
    def get_matches(self, asset: Optional[str] = None) -> List[Dict]:
        """Get all matches, optionally filtered by asset"""
        matches = list(self.matches.values())
        
        if asset:
            matches = [m for m in matches if m.crypto_currency == asset]
        
        return [m.to_dict() for m in matches]
    
    def get_total_converted(self) -> Dict[str, Decimal]:
        """Get total amount converted by currency"""
        totals = {}
        
        for match in self.matches.values():
            if match.fiat_currency not in totals:
                totals[match.fiat_currency] = Decimal("0")
            
            totals[match.fiat_currency] += match.fiat_amount
        
        return {k: float(v) for k, v in totals.items()}
    
    # Helper method
    def _get_exchange_rate(self, from_currency: str, to_currency: str, date: datetime) -> Decimal:
        """Get exchange rate for date (mocked)"""
        rates = {
            ('BRL', 'USD'): Decimal("0.20"),
            ('ARS', 'USD'): Decimal("0.003"),
            ('MXN', 'USD'): Decimal("0.06"),
            ('USD', 'BRL'): Decimal("5.0"),
            ('USD', 'ARS'): Decimal("350.0"),
            ('USD', 'MXN'): Decimal("17.0"),
        }
        
        key = (from_currency, to_currency)
        return rates.get(key, Decimal("1.0"))


class CryptoToFiatAuditTrail:
    """
    Complete audit trail for crypto to fiat conversion
    
    Documents:
    1. Original crypto purchase (cost basis)
    2. Exchange login + API connection
    3. Withdrawal from exchange
    4. Blockchain confirmation
    5. Fiat on-ramp (e.g., Mercado Pago)
    6. Bank deposit
    7. Tax evidence ready
    """
    
    @dataclass
    class Event:
        timestamp: datetime
        event_type: str  # purchase, withdrawal, blockchain_confirm, bank_deposit
        description: str
        amount: Decimal
        currency: str
    
    def __init__(self, transaction_id: str):
        self.transaction_id = transaction_id
        self.events: List[self.Event] = []
    
    def add_event(self, event_type: str, description: str, amount: Decimal, currency: str):
        """Add event to audit trail"""
        event = self.Event(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            amount=amount,
            currency=currency
        )
        
        self.events.append(event)
        logger.info(f"📝 Audit trail: {event_type.upper()} - {description}")
    
    def get_full_trail(self) -> List[Dict]:
        """Get complete audit trail"""
        return [
            {
                'timestamp': e.timestamp.isoformat(),
                'event_type': e.event_type,
                'description': e.description,
                'amount': float(e.amount),
                'currency': e.currency,
            }
            for e in self.events
        ]
    
    def generate_tax_evidence_pdf(self) -> Dict:
        """Generate PDF report suitable for tax authorities"""
        return {
            'transaction_id': self.transaction_id,
            'summary': f"Complete crypto-to-fiat conversion trail with {len(self.events)} verification points",
            'events': self.get_full_trail(),
            'generated_at': datetime.now().isoformat(),
            'suitable_for': ['tax_filing', 'audit', 'compliance'],
        }


# Example usage
if __name__ == "__main__":
    from bank_connector import BankTransaction, TransactionType
    
    print("\n" + "="*70)
    print("TRANSACTION MATCHING ENGINE DEMO")
    print("="*70 + "\n")
    
    # Setup
    engine = TransactionMatchingEngine()
    audit_trail = CryptoToFiatAuditTrail("TX_BTC_2024_001")
    
    # Example: Sell 1.5 BTC for $45,000
    
    # Step 1: Bitcoin purchase (historical cost basis)
    print("1️⃣ COST BASIS - Purchased in 2022")
    audit_trail.add_event("purchase", "Bought 1.5 BTC @ $20,000/BTC", Decimal("1.5"), "BTC")
    print()
    
    # Step 2: Withdrawal from exchange
    print("2️⃣ EXCHANGE WITHDRAWAL")
    withdrawal = CryptoWithdrawal(
        id="withdrawal_binance_001",
        exchange="binance",
        asset="USDC",  # Converted to stablecoin
        amount=Decimal("45000.00"),
        amount_in_usd=Decimal("45000.00"),
        date_time=datetime.now() - timedelta(hours=12),
        destination_address="0x1234...5678",
        tx_hash="0xabcd...efgh"
    )
    audit_trail.add_event("withdrawal", f"Withdrew {withdrawal.amount} {withdrawal.asset}", withdrawal.amount, withdrawal.asset)
    print(f"   Withdrawn: {withdrawal.amount} {withdrawal.asset}")
    print(f"   Date: {withdrawal.date_time}")
    print()
    
    # Step 3: Blockchain confirmation
    print("3️⃣ BLOCKCHAIN CONFIRMATION")
    audit_trail.add_event("blockchain_confirm", f"Tx confirmed: {withdrawal.tx_hash}", withdrawal.amount, withdrawal.asset)
    print(f"   TX Hash: {withdrawal.tx_hash}")
    print()
    
    # Step 4: Bank deposit arrives
    print("4️⃣ BANK DEPOSIT (Nubank - Brazil)")
    deposit = BankTransaction(
        id="nubank_deposit_001",
        account_id="nubank_acc_123",
        date=datetime.now() - timedelta(hours=6),
        type=TransactionType.DEPOSIT,
        amount=Decimal("225000.00"),  # 45,000 USD × 5 BRL/USD
        currency="BRL",
        description="USDC → BRL conversion via Mercado Pago",
        counterparty="Mercado Pago"
    )
    audit_trail.add_event("bank_deposit", f"Received {deposit.amount} {deposit.currency}", deposit.amount, deposit.currency)
    print(f"   Received: {deposit.amount} {deposit.currency}")
    print(f"   From: {deposit.counterparty}")
    print()
    
    # Step 5: Match transactions
    print("5️⃣ MATCHING WITHDRAWAL → DEPOSIT")
    rules = MatchingRule(
        amount_tolerance_pct=2.0,
        time_window_hours=24,
        counterparty_keywords=['Mercado', 'Exchange']
    )
    
    match = engine.match_withdrawal_to_deposit(withdrawal, [deposit], rules)
    
    if match:
        print(f"   ✅ MATCHED!")
        print(f"   Exchange rate: 1 USDC = {match.exchange_rate:.2f} BRL")
        print(f"   Confidence: {match.confidence:.1%}")
        print()
    
    # Step 6: Tax evidence
    print("6️⃣ TAX EVIDENCE GENERATION")
    evidence = audit_trail.generate_tax_evidence_pdf()
    print(f"   Generated report: {len(evidence['events'])} events")
    print(f"   Suitable for: {', '.join(evidence['suitable_for'])}")
    print()
    
    # Step 7: Summary
    print("7️⃣ COMPLETE AUDIT TRAIL")
    print("\n   Timeline:")
    for event in evidence['events']:
        print(f"     {event['timestamp']}: {event['event_type'].upper()}")
        print(f"     → {event['description']}")
    
    print("\n" + "="*70)
    print("✅ MATCHING ENGINE DEMO COMPLETE")
    print("   Ready for tax filing!")
    print("="*70 + "\n")
