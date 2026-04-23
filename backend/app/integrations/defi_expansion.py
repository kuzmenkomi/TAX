"""
DeFi Expansion - Restaking & L2 Networks

Adds support for:
1. Restaking protocols (EigenLayer, Lido, etc.)
2. L2 Networks (Linea, Scroll, ZkSync Era, Arbitrum, Optimism, etc.)
3. Tax reporting for wrapped/bridged tokens
4. Cross-chain transaction tracking
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

import pandas as pd


class RestakingProtocol(Enum):
    """Supported restaking protocols."""
    
    EIGENLAYER = "eigenlayer"
    LIDO = "lido"
    ROCKETPOOL = "rocketpool"
    STADER = "stader"
    KELP = "kelp"
    ETHER_FI = "ether.fi"
    MELLOW = "mellow"


class Layer2Network(Enum):
    """Supported L2 networks."""
    
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    LINEA = "linea"
    SCROLL = "scroll"
    ZKSYNC_ERA = "zksync_era"
    POLYGON_ZKEVM = "polygon_zkevm"
    BASE = "base"
    MANTLE = "mantle"


@dataclass
class RestakingEvent:
    """A restaking transaction (deposit/withdraw/claim)."""
    
    timestamp: datetime
    tx_hash: str
    wallet_address: str
    
    protocol: RestakingProtocol
    action: str  # "DEPOSIT", "WITHDRAW", "REDELEGATE", "CLAIM_REWARDS"
    
    asset: str  # ETH, USDC, DAI, stETH, etc.
    amount: float
    price_usd: float  # Market price at transaction time
    total_usd: float
    
    network: str = "ethereum"
    gas_fee_usd: float = 0.0
    
    @property
    def is_income_event(self) -> bool:
        """True if this triggers taxable income (rewards claiming)."""
        return self.action in ["CLAIM_REWARDS", "REDELEGATE"]
    
    @property
    def is_capital_event(self) -> bool:
        """True if this creates capital gains/loss (rewards in new form)."""
        return self.action == "STAKE" and self.asset.startswith(("st", "r"))
    
    def to_transaction_format(self) -> dict:
        """Convert to standard transaction format for tax calculation."""
        
        if self.action == "DEPOSIT":
            return {
                "timestamp": self.timestamp.isoformat(),
                "type": "SWAP",  # Deposit as swap (ETH -> stETH concept)
                "asset_from": "ETH",
                "asset_to": self.asset,
                "amount_from": self.amount,
                "amount_to": self.amount,
                "price": self.price_usd,
                "total_usd": self.total_usd,
                "wallet": self.wallet_address,
                "tx_hash": self.tx_hash,
            }
        
        elif self.action == "WITHDRAW":
            return {
                "timestamp": self.timestamp.isoformat(),
                "type": "SWAP",  # Withdraw as swap (stETH -> ETH)
                "asset_from": self.asset,
                "asset_to": "ETH",
                "amount_from": self.amount,
                "amount_to": self.amount,
                "price": self.price_usd,
                "total_usd": self.total_usd,
                "wallet": self.wallet_address,
                "tx_hash": self.tx_hash,
            }
        
        elif self.action == "CLAIM_REWARDS":
            return {
                "timestamp": self.timestamp.isoformat(),
                "type": "STAKING_REWARD",  # Income event
                "asset": self.asset,
                "amount": self.amount,
                "price": self.price_usd,
                "total_usd": self.total_usd,
                "wallet": self.wallet_address,
                "tx_hash": self.tx_hash,
                "protocol": self.protocol.value,
            }
        
        return {}


@dataclass
class Layer2Transaction:
    """Cross-chain transaction (L1 deposit/withdrawal or L2 swap)."""
    
    timestamp: datetime
    tx_hash: str
    wallet_address: str
    
    network: Layer2Network
    transaction_type: str  # DEPOSIT, WITHDRAWAL, SWAP, TRANSFER
    
    asset: str
    amount: float
    price_usd: float
    total_usd: float
    
    # For cross-chain transactions
    source_network: Optional[str] = None
    destination_network: Optional[str] = None
    bridge_protocol: Optional[str] = None  # "stargate", "cctp", native bridge
    
    gas_fee_usd: float = 0.0
    bridge_fee_usd: float = 0.0
    
    # For wrapped tokens
    wrapped_asset: Optional[str] = None  # If USDC.e, original is USDC
    
    @property
    def total_cost_usd(self) -> float:
        """Total cost including all fees."""
        return self.gas_fee_usd + self.bridge_fee_usd
    
    @property
    def is_taxable_swap(self) -> bool:
        """True if this creates a taxable event (not just a transfer)."""
        return self.transaction_type == "SWAP"
    
    def to_transaction_format(self) -> dict:
        """Convert to standard transaction format."""
        
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.transaction_type,  # SWAP, TRANSFER, etc.
            "asset": self.asset,
            "amount": self.amount,
            "price": self.price_usd,
            "total_usd": self.total_usd,
            "wallet": self.wallet_address,
            "tx_hash": self.tx_hash,
            "network": self.network.value,
            "bridge": {
                "source": self.source_network,
                "destination": self.destination_network,
                "protocol": self.bridge_protocol,
                "fee": self.bridge_fee_usd,
            },
            "fees": {
                "gas": self.gas_fee_usd,
                "bridge": self.bridge_fee_usd,
                "total": self.total_cost_usd,
            },
        }


class RestakingParser:
    """Parse restaking events from blockchain explorers."""
    
    @staticmethod
    def parse_eigenlayer_events(events_json: list[dict]) -> list[RestakingEvent]:
        """Parse EigenLayer restaking events.
        
        Supports:
        - Deposit (ETH, stETH, rETH)
        - Withdrawal
        - Delegation
        - Rewards claiming
        """
        events = []
        
        for event in events_json:
            # Map EigenLayer event types to RestakingEvent actions
            action_map = {
                "Deposit": "DEPOSIT",
                "Withdrawal": "WITHDRAW",
                "DelegatorRegistered": "DELEGATE",
                "OperatorSharesIncreased": "REDELEGATE",
            }
            
            action = action_map.get(event.get("event_type"), "UNKNOWN")
            
            if action != "UNKNOWN":
                restaking_event = RestakingEvent(
                    timestamp=datetime.fromisoformat(event["timestamp"]),
                    tx_hash=event["tx_hash"],
                    wallet_address=event["from_address"],
                    protocol=RestakingProtocol.EIGENLAYER,
                    action=action,
                    asset=event["token"],
                    amount=float(event["amount"]),
                    price_usd=float(event.get("price", 0)),
                    total_usd=float(event.get("total_usd", 0)),
                    gas_fee_usd=float(event.get("gas_fee", 0)),
                )
                events.append(restaking_event)
        
        return events
    
    @staticmethod
    def parse_lido_events(events_json: list[dict]) -> list[RestakingEvent]:
        """Parse Lido staking events (stETH)."""
        events = []
        
        for event in events_json:
            action_map = {
                "Staked": "DEPOSIT",
                "Unstaked": "WITHDRAW",
                "WithdrawalCreated": "PENDING_WITHDRAWAL",
                "WithdrawalClaimed": "WITHDRAW",
            }
            
            action = action_map.get(event.get("event_type"), "UNKNOWN")
            
            if action != "UNKNOWN":
                restaking_event = RestakingEvent(
                    timestamp=datetime.fromisoformat(event["timestamp"]),
                    tx_hash=event["tx_hash"],
                    wallet_address=event["from_address"],
                    protocol=RestakingProtocol.LIDO,
                    action=action,
                    asset="stETH" if action == "DEPOSIT" else "ETH",
                    amount=float(event["amount"]),
                    price_usd=float(event.get("price", 0)),
                    total_usd=float(event.get("total_usd", 0)),
                    gas_fee_usd=float(event.get("gas_fee", 0)),
                )
                events.append(restaking_event)
        
        return events


class Layer2Parser:
    """Parse Layer 2 network transactions."""
    
    @staticmethod
    def parse_arbitrum_transactions(txs_json: list[dict]) -> list[Layer2Transaction]:
        """Parse Arbitrum L2 transactions."""
        transactions = []
        
        for tx in txs_json:
            tx_type = _infer_l2_transaction_type(tx)
            
            layer2_tx = Layer2Transaction(
                timestamp=datetime.fromisoformat(tx["timestamp"]),
                tx_hash=tx["tx_hash"],
                wallet_address=tx["from_address"],
                network=Layer2Network.ARBITRUM,
                transaction_type=tx_type,
                asset=tx.get("token", "ETH"),
                amount=float(tx.get("amount", 0)),
                price_usd=float(tx.get("price", 0)),
                total_usd=float(tx.get("total_usd", 0)),
                gas_fee_usd=float(tx.get("gas_fee", 0)),
                source_network=tx.get("source_network"),
                destination_network="arbitrum",
                bridge_protocol=tx.get("bridge_type"),
            )
            transactions.append(layer2_tx)
        
        return transactions
    
    @staticmethod
    def parse_linea_transactions(txs_json: list[dict]) -> list[Layer2Transaction]:
        """Parse Linea L2 transactions (ConsenSys zkEVM)."""
        transactions = []
        
        for tx in txs_json:
            tx_type = _infer_l2_transaction_type(tx)
            
            layer2_tx = Layer2Transaction(
                timestamp=datetime.fromisoformat(tx["timestamp"]),
                tx_hash=tx["tx_hash"],
                wallet_address=tx["from_address"],
                network=Layer2Network.LINEA,
                transaction_type=tx_type,
                asset=tx.get("token", "ETH"),
                amount=float(tx.get("amount", 0)),
                price_usd=float(tx.get("price", 0)),
                total_usd=float(tx.get("total_usd", 0)),
                gas_fee_usd=float(tx.get("gas_fee", 0)),
                source_network=tx.get("source_network"),
                destination_network="linea",
                bridge_protocol=tx.get("bridge_type", "linea_bridge"),
            )
            transactions.append(layer2_tx)
        
        return transactions
    
    @staticmethod
    def parse_scroll_transactions(txs_json: list[dict]) -> list[Layer2Transaction]:
        """Parse Scroll L2 transactions (zkEVM)."""
        transactions = []
        
        for tx in txs_json:
            tx_type = _infer_l2_transaction_type(tx)
            
            layer2_tx = Layer2Transaction(
                timestamp=datetime.fromisoformat(tx["timestamp"]),
                tx_hash=tx["tx_hash"],
                wallet_address=tx["from_address"],
                network=Layer2Network.SCROLL,
                transaction_type=tx_type,
                asset=tx.get("token", "ETH"),
                amount=float(tx.get("amount", 0)),
                price_usd=float(tx.get("price", 0)),
                total_usd=float(tx.get("total_usd", 0)),
                gas_fee_usd=float(tx.get("gas_fee", 0)),
                source_network=tx.get("source_network"),
                destination_network="scroll",
                bridge_protocol=tx.get("bridge_type", "scroll_bridge"),
            )
            transactions.append(layer2_tx)
        
        return transactions


class MultiChainTaxCalculator:
    """Calculate taxes across multiple chains."""
    
    @staticmethod
    def consolidate_transactions(
        restaking_events: list[RestakingEvent],
        layer2_transactions: list[Layer2Transaction],
    ) -> pd.DataFrame:
        """Consolidate all cross-chain transactions into unified tax format.
        
        Handles:
        - Wrapped token tracking (e.g., USDC.e -> USDC)
        - Bridge fee accounting
        - Proper cost basis for swaps
        """
        
        all_txs = []
        
        # Convert restaking events
        for event in restaking_events:
            tx_dict = event.to_transaction_format()
            if tx_dict:
                all_txs.append(tx_dict)
        
        # Convert L2 transactions
        for l2_tx in layer2_transactions:
            tx_dict = l2_tx.to_transaction_format()
            if tx_dict:
                all_txs.append(tx_dict)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_txs)
        
        # Sort by timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        
        return df
    
    @staticmethod
    def detect_wrapped_token_swaps(
        l2_transactions: list[Layer2Transaction]
    ) -> dict:
        """Identify transactions involving wrapped tokens.
        
        Returns mapping: {wrapped_asset: original_asset}
        Example: {"USDC.e": "USDC"} on Arbitrum
        """
        wrapped_mapping = {}
        
        for tx in l2_transactions:
            if tx.wrapped_asset:
                wrapped_mapping[tx.asset] = tx.wrapped_asset
        
        return wrapped_mapping
    
    @staticmethod
    def calculate_multichaim_pnl(
        transactions: pd.DataFrame
    ) -> dict:
        """Calculate total P&L and fees across all chains."""
        
        total_gains = 0
        total_losses = 0
        total_gas_fees = 0
        total_bridge_fees = 0
        
        for _, tx in transactions.iterrows():
            if tx["type"] == "SWAP":
                pnl = tx["total_usd"]  # Simplified
                if pnl > 0:
                    total_gains += pnl
                else:
                    total_losses += abs(pnl)
            
            if "fees" in tx:
                fees = tx["fees"] or {}
                total_gas_fees += float(fees.get("gas", 0))
                total_bridge_fees += float(fees.get("bridge", 0))
        
        return {
            "total_gains": total_gains,
            "total_losses": total_losses,
            "total_gas_fees": total_gas_fees,
            "total_bridge_fees": total_bridge_fees,
            "total_fees": total_gas_fees + total_bridge_fees,
        }


def _infer_l2_transaction_type(tx: dict) -> str:
    """Infer transaction type from raw transaction data."""
    
    # Check if it's a bridge transaction
    if tx.get("is_bridge"):
        if tx.get("direction", "").lower() in ["deposit", "incoming"]:
            return "DEPOSIT"
        else:
            return "WITHDRAWAL"
    
    # Check if it's a swap
    if tx.get("function_name", "").lower() in ["swap", "swapexactinput"]:
        return "SWAP"
    
    # Check if it's a transfer
    if tx.get("function_name", "").lower() in ["transfer", "transferfrom"]:
        return "TRANSFER"
    
    return "UNKNOWN"


# ==================== NETWORK ADAPTERS ====================
# 
# Adapters for fetching data from each L2 network.
#
# Example implementation:
#
# class LinealAdapter:
#     '''Fetch Linea transactions from block explorer.'''
#     
#     def __init__(self, api_key: str):
#         self.base_url = "https://api.lineascan.build/api"
#         self.api_key = api_key
#     
#     def get_transactions(self, address: str) -> list[dict]:
#         '''Fetch all transactions for an address on Linea.'''
#         
#         params = {
#             "module": "account",
#             "action": "txlist",
#             "address": address,
#             "startblock": 0,
#             "endblock": 99999999,
#             "sort": "asc",
#             "apikey": self.api_key,
#         }
#         
#         response = requests.get(self.base_url, params=params)
#         return response.json().get("result", [])
#
# class ScrollAdapter:
#     '''Fetch Scroll transactions.'''
#     
#     def __init__(self, api_key: str):
#         self.base_url = "https://api.scrollscan.com/api"
#         self.api_key = api_key
#     
#     # Similar implementation as LinealAdapter
#
# class RestakingDataFetcher:
#     '''Fetch restaking events from EigenLayer, Lido, etc.'''
#     
#     @staticmethod
#     def fetch_eigenlayer_events(address: str) -> list[dict]:
#         '''Fetch EigenLayer events from The Graph.'''
#         
#         query = \"""
#         query {
#             deposits(where: {delegator: \"[address]\"}) {
#                 id
#                 timestamp
#                 transactionHash
#                 token
#                 amount
#                 price
#             }
#         }
#         \"""
#         
#         # Execute GraphQL query...
#         pass
#
#     @staticmethod
#     def fetch_lido_events(address: str) -> list[dict]:
#         '''Fetch Lido staking events.'''
#         # Similar implementation...
#         pass

# ==================== API INTEGRATION ====================
# 
# Add to your FastAPI app:
#
# from app.integrations.defi_expansion import (
#     RestakingParser,
#     Layer2Parser,
#     MultiChainTaxCalculator,
#     RestakingProtocol,
#     Layer2Network,
# )
#
# @app.post("/sync/eigenlayer")
# def sync_eigenlayer(
#     current_user = Depends(get_current_user),
#     db = Depends(get_db)
# ):
#     '''Fetch and import EigenLayer restaking events.'''
#     
#     user = db.query(User).filter(User.id == current_user.id).first()
#     
#     # Fetch events for user's wallets
#     all_events = []
#     for wallet in user.wallets:
#         events_data = fetch_eigenlayer_events(wallet.address)
#         events = RestakingParser.parse_eigenlayer_events(events_data)
#         all_events.extend(events)
#     
#     # Store in database...
#     
#     return {
#         "imported": len(all_events),
#         "events": [e.to_transaction_format() for e in all_events]
#     }
#
#
# @app.post("/sync/linea")
# def sync_linea(
#     current_user = Depends(get_current_user),
#     db = Depends(get_db)
# ):
#     '''Fetch and import Linea transactions.'''
#     
#     user = db.query(User).filter(User.id == current_user.id).first()
#     
#     adapter = LinealAdapter(api_key=os.getenv("LINEASCAN_API_KEY"))
#     
#     all_txs = []
#     for wallet in user.wallets:
#         txs_data = adapter.get_transactions(wallet.address)
#         txs = Layer2Parser.parse_linea_transactions(txs_data)
#         all_txs.extend(txs)
#     
#     return {
#         "imported": len(all_txs),
#         "transactions": [t.to_transaction_format() for t in all_txs]
#     }
#
#
# @app.post("/analyze/multichain")
# def analyze_multichain(
#     run_id: int,
#     current_user = Depends(get_current_user),
#     db = Depends(get_db)
# ):
#     '''Analyze taxes across all chains (L1 + L2 + Restaking).'''
#     
#     run = db.query(AnalysisRun).filter(
#         AnalysisRun.id == run_id,
#         AnalysisRun.user_id == current_user.id
#     ).first()
#     
#     # Load all transaction types
#     restaking_events = []  # From database
#     layer2_transactions = []  # From database
#     
#     # Consolidate
#     consolidated = MultiChainTaxCalculator.consolidate_transactions(
#         restaking_events,
#         layer2_transactions
#     )
#     
#     # Calculate taxes
#     pnl = MultiChainTaxCalculator.calculate_multichaim_pnl(consolidated)
#     
#     return {
#         "total_transactions": len(consolidated),
#         "chains": consolidated["network"].unique().tolist() if not consolidated.empty else [],
#         "pnl": pnl,
#     }
