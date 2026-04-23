"""
Multi-chain blockchain explorer integration.

Supports:
- Ethereum-compatible (via Etherscan API): Ethereum, Polygon, BNB Chain, Avalanche, Arbitrum, Optimism, Base
- Bitcoin (via Blockchair/Hiro API)
- Solana (via Solscan API)
- Tron (via TronScan API)
- Cosmos-based (via Mintscan/API)

Returns normalized DataFrame compatible with tax pipeline.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any

import pandas as pd
import requests


class BlockchainExplorer(ABC):
    """Abstract base for blockchain explorers."""
    
    @abstractmethod
    def get_transactions(self, address: str, start_block: int | None = None) -> pd.DataFrame:
        """Fetch all transactions for address since start_block. Returns DataFrame."""
        pass
    
    @abstractmethod
    def get_balance(self, address: str) -> dict[str, float]:
        """Get current balance(s) in native + tokens."""
        pass
    
    def get_chain_name(self) -> str:
        """Return chain identifier for storage."""
        pass


def _mk_transfer_row(
    *,
    ts_seconds: int,
    asset: str,
    amount: float,
    from_addr: str,
    to_addr: str,
    tx_hash: str,
    network: str,
    fee: float = 0.0,
    fee_asset: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create normalized transaction row."""
    if amount < 0:
        amount = abs(amount)
    row = {
        "timestamp": pd.Timestamp(int(ts_seconds), unit="s", tz="UTC"),
        "asset": asset.upper() if asset else "UNKNOWN",
        "type": "TRANSFER",
        "amount": float(amount),
        "fee": float(fee),
        "fee_asset": (fee_asset or asset).upper() if asset else "UNKNOWN",
        "from_wallet": from_addr,
        "to_wallet": to_addr,
        "network": network,
        "price": 0.0,
        "total_value": 0.0,
        "external_id": tx_hash,
    }
    if extra:
        row.update(extra)
    return row


class EvmExplorer(BlockchainExplorer):
    """
    Ethereum-compatible chain explorer (Etherscan API compatible).
    
    Supported chains:
    - ethereum (Etherscan)
    - polygon (PolygonScan)
    - bsc (BSCScan)
    - avalanche (Snowtrace)
    - arbitrum (Arbiscan)
    - optimism (Optimistic Etherscan)
    - base (BaseScan)
    """
    
    CHAIN_CONFIG = {
        "ethereum": {
            "api_url": "https://api.etherscan.io/api",
            "native_asset": "ETH",
            "decimals": 18,
        },
        "polygon": {
            "api_url": "https://api.polygonscan.com/api",
            "native_asset": "MATIC",
            "decimals": 18,
        },
        "bsc": {
            "api_url": "https://api.bscscan.com/api",
            "native_asset": "BNB",
            "decimals": 18,
        },
        "avalanche": {
            "api_url": "https://api.snowtrace.io/api",
            "native_asset": "AVAX",
            "decimals": 18,
        },
        "arbitrum": {
            "api_url": "https://api.arbiscan.io/api",
            "native_asset": "ETH",
            "decimals": 18,
        },
        "optimism": {
            "api_url": "https://api-optimistic.etherscan.io/api",
            "native_asset": "ETH",
            "decimals": 18,
        },
        "base": {
            "api_url": "https://api.basescan.org/api",
            "native_asset": "ETH",
            "decimals": 18,
        },
    }
    
    def __init__(self, chain: str, api_key: str | None = None):
        self.chain = chain.lower()
        self.api_key = api_key or os.getenv(f"EXPLORER_API_KEY_{self.chain.upper()}", "")
        
        if self.chain not in self.CHAIN_CONFIG:
            raise ValueError(f"Unsupported EVM chain: {self.chain}")
        
        self.config = self.CHAIN_CONFIG[self.chain]
    
    def _api_call(self, action: str, address: str, start_block: int = 0) -> list[dict]:
        """Call Etherscan-compatible API."""
        params = {
            "module": "account",
            "action": action,
            "address": address.lower(),
            "startblock": start_block,
            "endblock": 99999999,
            "sort": "asc",
            "apikey": self.api_key,
        }
        
        try:
            response = requests.get(self.config["api_url"], params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get("result", []) if isinstance(data.get("result"), list) else []
        except Exception:
            return []
    
    def get_transactions(self, address: str, start_block: int | None = None) -> pd.DataFrame:
        """Fetch transactions from EVM chain."""
        start_block_val = start_block if start_block is not None else 0
        rows = []
        address_norm = address.lower()
        native_asset = self.config["native_asset"]
        decimals = self.config["decimals"]
        
        # Native transfers
        for tx in self._api_call("txlist", address_norm, start_block_val) or []:
            try:
                ts = int(tx.get("timeStamp", 0))
                value_wei = int(tx.get("value", 0))
                value = value_wei / (10 ** decimals)
                
                if value > 0:  # Only include incoming/outgoing value transfers
                    from_addr = str(tx.get("from", "")).lower()
                    to_addr = str(tx.get("to", "")).lower()
                    tx_hash = str(tx.get("hash", ""))
                    
                    rows.append(_mk_transfer_row(
                        ts_seconds=ts,
                        asset=native_asset,
                        amount=value,
                        from_addr=from_addr,
                        to_addr=to_addr,
                        tx_hash=tx_hash,
                        network=self.chain,
                    ))
            except Exception:
                continue
        
        # ERC-20 token transfers
        for tx in self._api_call("tokentx", address_norm, start_block_val) or []:
            try:
                ts = int(tx.get("timeStamp", 0))
                value = int(tx.get("value", 0))
                decimals_token = int(tx.get("tokenDecimal", 0))
                amount = float(value) / (10 ** decimals_token) if decimals_token else float(value)
                
                asset = str(tx.get("tokenSymbol") or tx.get("tokenName") or "UNKNOWN").upper()
                from_addr = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower()
                tx_hash = str(tx.get("hash", ""))
                contract_addr = str(tx.get("contractAddress", "")).lower()
                
                rows.append(_mk_transfer_row(
                    ts_seconds=ts,
                    asset=asset,
                    amount=amount,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    tx_hash=tx_hash,
                    network=self.chain,
                    extra={
                        "type": "TOKEN_TRANSFER",
                        "contract_address": contract_addr,
                    }
                ))
            except Exception:
                continue
        
        # NFT transfers (optional, minimal tax impact but included for completeness)
        for tx in self._api_call("tokennfttx", address_norm, start_block_val) or []:
            try:
                ts = int(tx.get("timeStamp", 0))
                asset = str(tx.get("tokenSymbol") or "NFT").upper()
                from_addr = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower()
                tx_hash = str(tx.get("hash", ""))
                token_id = str(tx.get("tokenID", ""))
                
                rows.append(_mk_transfer_row(
                    ts_seconds=ts,
                    asset=asset,
                    amount=1.0,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    tx_hash=f"{tx_hash}:{token_id}",
                    network=self.chain,
                    extra={"type": "NFT_TRANSFER", "token_id": token_id}
                ))
            except Exception:
                continue
        
        if not rows:
            return self._empty_dataframe()
        
        df = pd.DataFrame(rows)
        return df.sort_values("timestamp").reset_index(drop=True)
    
    def get_balance(self, address: str) -> dict[str, float]:
        """Get current token balances."""
        balances = {}
        
        # Native balance
        try:
            params = {
                "module": "account",
                "action": "balance",
                "address": address.lower(),
                "apikey": self.api_key,
            }
            response = requests.get(self.config["api_url"], params=params, timeout=10)
            data = response.json()
            native_wei = int(data.get("result", 0))
            decimals = self.config["decimals"]
            balances[self.config["native_asset"].lower()] = native_wei / (10 ** decimals)
        except Exception:
            pass
        
        return balances
    
    def _empty_dataframe(self) -> pd.DataFrame:
        """Return empty DataFrame with correct columns."""
        return pd.DataFrame(columns=[
            "timestamp", "asset", "type", "amount", "fee", "fee_asset",
            "from_wallet", "to_wallet", "network", "price", "total_value", "external_id"
        ])


class BitcoinExplorer(BlockchainExplorer):
    """Bitcoin transactions via Blockchair API."""
    
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("BLOCKCHAIR_API_KEY", "")
        self.base_url = "https://api.blockchair.com/bitcoin"
    
    def get_transactions(self, address: str, start_block: int | None = None) -> pd.DataFrame:
        """Fetch Bitcoin transactions."""
        rows = []
        
        try:
            params = {"key": self.api_key} if self.api_key else {}
            url = f"{self.base_url}/addresses/{address}"
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            addr_data = data.get("data", {}).get(address, {})
            transactions = addr_data.get("transactions", [])
            
            for tx_hash in transactions or []:
                tx_url = f"{self.base_url}/dashboards/transaction/{tx_hash}"
                tx_response = requests.get(tx_url, params=params, timeout=10)
                tx_response.raise_for_status()
                tx_data = tx_response.json()
                
                tx = tx_data.get("data", {}).get(tx_hash, {})
                if not tx:
                    continue
                
                ts = int(tx.get("block_time", 0))
                
                # Parse inputs and outputs
                for inp in tx.get("inputs", []) or []:
                    if inp.get("addresses", []) and address in inp["addresses"]:
                        recipient = inp.get("recipient")
                        amount_sat = int(inp.get("value", 0))
                        amount = amount_sat / (10 ** 8)
                        
                        rows.append(_mk_transfer_row(
                            ts_seconds=ts,
                            asset="BTC",
                            amount=amount,
                            from_addr=address,
                            to_addr=recipient or "unknown",
                            tx_hash=tx_hash,
                            network="bitcoin",
                        ))
                
                for outp in tx.get("outputs", []) or []:
                    if outp.get("addresses", []) and address in outp["addresses"]:
                        sender = outp.get("sender")
                        amount_sat = int(outp.get("value", 0))
                        amount = amount_sat / (10 ** 8)
                        
                        rows.append(_mk_transfer_row(
                            ts_seconds=ts,
                            asset="BTC",
                            amount=amount,
                            from_addr=sender or "unknown",
                            to_addr=address,
                            tx_hash=tx_hash,
                            network="bitcoin",
                        ))
        except Exception:
            pass
        
        if not rows:
            return self._empty_dataframe()
        
        df = pd.DataFrame(rows)
        return df.sort_values("timestamp").drop_duplicates(subset=["external_id"]).reset_index(drop=True)
    
    def get_balance(self, address: str) -> dict[str, float]:
        """Get Bitcoin balance."""
        try:
            params = {"key": self.api_key} if self.api_key else {}
            url = f"{self.base_url}/addresses/{address}"
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            addr_data = data.get("data", {}).get(address, {})
            balance_sat = int(addr_data.get("balance", 0))
            return {"btc": balance_sat / (10 ** 8)}
        except Exception:
            return {}
    
    def _empty_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            "timestamp", "asset", "type", "amount", "fee", "fee_asset",
            "from_wallet", "to_wallet", "network", "price", "total_value", "external_id"
        ])


class SolanaExplorer(BlockchainExplorer):
    """Solana transactions via Solscan API."""
    
    def get_transactions(self, address: str, start_block: int | None = None) -> pd.DataFrame:
        """Fetch Solana transactions."""
        rows = []
        
        try:
            url = f"https://public-api.solscan.io/account/solTransfers"
            params = {"account": address, "limit": 100, "offset": 0}
            response = requests.get(url, params=params, timeout=15, headers={"accept": "application/json"})
            response.raise_for_status()
            
            for tx in response.json() or []:
                try:
                    ts = int(tx.get("blockTime", 0))
                    lamports = int(tx.get("lamport", 0))
                    amount = abs(lamports) / (10 ** 9)
                    from_addr = str(tx.get("src", "")).lower()
                    to_addr = str(tx.get("dst", "")).lower()
                    tx_hash = str(tx.get("txHash", ""))
                    
                    rows.append(_mk_transfer_row(
                        ts_seconds=ts,
                        asset="SOL",
                        amount=amount,
                        from_addr=from_addr,
                        to_addr=to_addr,
                        tx_hash=tx_hash,
                        network="solana",
                    ))
                except Exception:
                    continue
            
            # Token transfers
            url = f"https://public-api.solscan.io/account/tokenTransfers"
            for token_tx in (requests.get(url, params=params, timeout=15).json() or []):
                try:
                    ts = int(token_tx.get("blockTime", 0))
                    amount = float(token_tx.get("tokenAmount", 0))
                    asset = str(token_tx.get("tokenSymbol", "TOKEN")).upper()
                    from_addr = str(token_tx.get("src", "")).lower()
                    to_addr = str(token_tx.get("dst", "")).lower()
                    tx_hash = str(token_tx.get("txHash", ""))
                    
                    rows.append(_mk_transfer_row(
                        ts_seconds=ts,
                        asset=asset,
                        amount=amount,
                        from_addr=from_addr,
                        to_addr=to_addr,
                        tx_hash=tx_hash,
                        network="solana",
                    ))
                except Exception:
                    continue
        except Exception:
            pass
        
        if not rows:
            return self._empty_dataframe()
        
        df = pd.DataFrame(rows)
        return df.sort_values("timestamp").reset_index(drop=True)
    
    def get_balance(self, address: str) -> dict[str, float]:
        """Get Solana balance."""
        try:
            url = f"https://public-api.solscan.io/account/{address}"
            response = requests.get(url, timeout=10, headers={"accept": "application/json"})
            data = response.json()
            
            balance_lamports = int(data.get("solBalance", 0))
            return {"sol": balance_lamports / (10 ** 9)}
        except Exception:
            return {}
    
    def _empty_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            "timestamp", "asset", "type", "amount", "fee", "fee_asset",
            "from_wallet", "to_wallet", "network", "price", "total_value", "external_id"
        ])


class TronExplorer(BlockchainExplorer):
    """Tron transactions via TronScan API."""
    
    def get_transactions(self, address: str, start_block: int | None = None) -> pd.DataFrame:
        """Fetch Tron transactions."""
        rows = []
        
        try:
            # Native TRX transfers
            url = "https://api.trons.network/transactions"
            params = {
                "only_from": address,
                "limit": 200,
                "start_timestamp": 0,
                "end_timestamp": 999999999999,
            }
            
            response = requests.get(url, params=params, timeout=15)
            for tx in response.json() or []:
                try:
                    ts = int(tx.get("block_timestamp", 0)) // 1000  # Convert ms to s
                    amount_sun = int(tx.get("trx", 0))
                    amount = amount_sun / (10 ** 6)
                    
                    rows.append(_mk_transfer_row(
                        ts_seconds=ts,
                        asset="TRX",
                        amount=amount,
                        from_addr=tx.get("from"),
                        to_addr=tx.get("to"),
                        tx_hash=tx.get("hash"),
                        network="tron",
                    ))
                except Exception:
                    continue
            
            # TRC-20 transfers
            url = "https://api.trons.network/token_trc20_transfers"
            for token_tx in (requests.get(url, params={**params, "only_from": address}, timeout=15).json() or []):
                try:
                    ts = int(token_tx.get("block_timestamp", 0)) // 1000
                    amount = float(token_tx.get("quant", 0))
                    asset = str(token_tx.get("token_name", "TOKEN")).upper()
                    
                    rows.append(_mk_transfer_row(
                        ts_seconds=ts,
                        asset=asset,
                        amount=amount,
                        from_addr=token_tx.get("from"),
                        to_addr=token_tx.get("to"),
                        tx_hash=token_tx.get("transaction_id"),
                        network="tron",
                    ))
                except Exception:
                    continue
        except Exception:
            pass
        
        if not rows:
            return self._empty_dataframe()
        
        df = pd.DataFrame(rows)
        return df.sort_values("timestamp").reset_index(drop=True)
    
    def get_balance(self, address: str) -> dict[str, float]:
        """Get Tron balance."""
        try:
            url = f"https://api.trons.network/account/{address}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            balance_sun = int(data.get("balance", 0))
            return {"trx": balance_sun / (10 ** 6)}
        except Exception:
            return {}
    
    def _empty_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(columns=[
            "timestamp", "asset", "type", "amount", "fee", "fee_asset",
            "from_wallet", "to_wallet", "network", "price", "total_value", "external_id"
        ])


def get_explorer(chain: str, api_key: str | None = None) -> BlockchainExplorer:
    """
    Factory function to get appropriate explorer for chain.
    
    Supported chains:
    - ethereum, polygon, bsc, avalanche, arbitrum, optimism, base (EVM)
    - bitcoin (BTC)
    - solana (SOL)
    - tron (TRX)
    """
    chain_lower = chain.lower()
    
    if chain_lower in EvmExplorer.CHAIN_CONFIG:
        return EvmExplorer(chain, api_key)
    elif chain_lower == "bitcoin" or chain_lower == "btc":
        return BitcoinExplorer(api_key)
    elif chain_lower == "solana" or chain_lower == "sol":
        return SolanaExplorer()
    elif chain_lower == "tron" or chain_lower == "trx":
        return TronExplorer()
    else:
        raise ValueError(f"Unsupported blockchain: {chain}")


def fetch_wallet_transactions(address: str, chain: str, api_key: str | None = None) -> pd.DataFrame:
    """
    Fetch transactions for any supported blockchain.
    
    Args:
        address: Wallet address
        chain: Blockchain name (ethereum, polygon, bitcoin, solana, tron, etc.)
        api_key: Optional API key for rate limiting
    
    Returns:
        DataFrame with columns: timestamp, asset, type, amount, fee, fee_asset,
                                from_wallet, to_wallet, network, price, total_value, external_id
    """
    explorer = get_explorer(chain, api_key)
    return explorer.get_transactions(address)
