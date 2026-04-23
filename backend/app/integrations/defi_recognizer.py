"""
DeFi Protocol Recognition Engine.

Detects and classifies decentralized finance transactions from blockchain data:
- Uniswap V2/V3 (swaps, LP add/remove)
- Aave (lending, borrowing, liquidation)
- Curve (LP provision, swaps)
- Lido (ETH staking)
- Generic contract interactions

Returns enriched transaction DataFrame with DeFi metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

import pandas as pd

class DeFiProtocol(str, Enum):
    """Supported DeFi protocols."""
    UNISWAP_V2 = "uniswap_v2"
    UNISWAP_V3 = "uniswap_v3"
    AAVE = "aave"
    CURVE = "curve"
    LIDO = "lido"
    COMPOUND = "compound"
    MAKER = "maker"
    YIELD_FARMING = "yield_farming"
    LIQUIDITY_MINING = "liquidity_mining"
    GENERIC_SWAP = "generic_swap"
    GENERIC_POOL = "generic_pool"


class DeFiEventType(str, Enum):
    """Tax-relevant DeFi event types."""
    SWAP = "defi_swap"  # Subject to capital gains
    LP_ADD = "defi_lp_add"  # Creates position (no taxable event yet)
    LP_REMOVE = "defi_lp_remove"  # Subject to capital gains
    LENDING_DEPOSIT = "defi_lending_deposit"  # No tax event
    LENDING_WITHDRAW = "defi_lending_withdraw"  # May have gains/losses
    LENDING_REPAY = "defi_lending_repay"  # Might be tax-deductible
    LENDING_BORROW = "defi_lending_borrow"  # No tax event (liability)
    STAKING_DEPOSIT = "defi_staking_deposit"  # No tax event
    STAKING_REWARD = "defi_staking_reward"  # Ordinary income
    STAKING_UNSTAKE = "defi_staking_unstake"  # May have gains/losses
    FARMING_DEPOSIT = "defi_farming_deposit"  # No tax event
    FARMING_REWARD = "defi_farming_reward"  # Ordinary income
    FLASH_LOAN = "defi_flash_loan"  # Usually not taxable
    LIQUIDATION = "defi_liquidation"  # Capital loss/gain
    GOVERNANCE_CLAIM = "defi_governance_claim"  # Ordinary income


@dataclass
class DeFiMetadata:
    """Metadata for DeFi event."""
    protocol: DeFiProtocol
    event_type: DeFiEventType
    tx_hash: str
    timestamp: pd.Timestamp
    tokens_in: dict[str, float]  # {symbol: amount}
    tokens_out: dict[str, float]
    prices: dict[str, float]  # {symbol: usd_price}
    fee_usd: float = 0.0
    slippage: Optional[float] = None  # For swaps
    yield_earned: Optional[float] = None  # For staking/farming (in USD)
    position_id: Optional[str] = None  # For LP positions
    extra_data: dict[str, Any] = None

    def __post_init__(self):
        if self.extra_data is None:
            self.extra_data = {}


# ============================================================================
# KNOWN PROTOCOL ADDRESSES & ABIs
# ============================================================================

KNOWN_ADDRESSES = {
    # Uniswap V2
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": {
        "name": "Uniswap V2 Router",
        "protocol": DeFiProtocol.UNISWAP_V2,
    },
    "0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f": {
        "name": "Uniswap V2 Factory",
        "protocol": DeFiProtocol.UNISWAP_V2,
    },

    # Uniswap V3
    "0xe592427a0aece92de3edee1f18e0157c05861564": {
        "name": "Uniswap V3 SwapRouter",
        "protocol": DeFiProtocol.UNISWAP_V3,
    },
    "0x1f98431c8ad98523631ae4a59f267346ea3113fa": {
        "name": "Uniswap V3 Factory",
        "protocol": DeFiProtocol.UNISWAP_V3,
    },

    # Aave V2
    "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9": {
        "name": "Aave V2 LendingPool",
        "protocol": DeFiProtocol.AAVE,
    },
    "0x398ec7346dcd622edc5ae82352f02be94c62d119": {
        "name": "Aave V2 LendingPoolCore",
        "protocol": DeFiProtocol.AAVE,
    },

    # Aave V3
    "0x87870bca3f3fd6335c3f4ce8392d69350b4de4b9": {
        "name": "Aave V3 Pool",
        "protocol": DeFiProtocol.AAVE,
    },

    # Curve
    "0x87870bca3f3fd6335c3f4ce8392d69350b4de4b9": {
        "name": "Curve Registry (generic)",
        "protocol": DeFiProtocol.CURVE,
    },

    # Lido
    "0xae7ab96520de3a18e5e111b5eacc267359e7f9d0": {
        "name": "Lido stETH",
        "protocol": DeFiProtocol.LIDO,
    },
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": {
        "name": "WETH9",
        "protocol": None,
    },

    # Compound V2
    "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b": {
        "name": "Compound Comptroller",
        "protocol": DeFiProtocol.COMPOUND,
    },

    # MakerDAO
    "0x8daeba2d91b9c04cb667aff7765e51bb74ffe9c6": {
        "name": "MakerDAO PSM (USDC)",
        "protocol": DeFiProtocol.MAKER,
    },
}

# Known token symbols for quick lookup
KNOWN_TOKENS = {
    "0xa0b869991c6734a2142316683c1fbfa7eb670fce": "CAPO",
    "0xdac17f958d2ee523a2206206994597c13d831ec7": "USDT",
    "0x6b175474e89094c44da98b954eedeac495271d0f": "DAI",
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48": "USDC",
    "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2": "WETH",
    "0x2260fac5e5542a773aa44fbcff022f5f3544ed4e": "WBTC",
    "0x7f39c581f595b53c5cb19bd0b3f8da6c935e2ca0": "stETH",
    "0xae7ab96520de3a18e5e111b5eacc267359e7f9d0": "stETH",
}

# ============================================================================
# TRANSACTION PATTERN DETECTION
# ============================================================================


def _normalize_addr(addr: str) -> str:
    """Normalize ethereum address to lowercase."""
    if not addr or not isinstance(addr, str):
        return ""
    return addr.lower().replace("0x", "").strip()


def _get_token_symbol(address: str, fallback: str = "UNKNOWN") -> str:
    """Get token symbol from known addresses."""
    addr_norm = _normalize_addr(address)
    return KNOWN_TOKENS.get(f"0x{addr_norm}", fallback)


def _detect_uniswap_swap(df_row: dict[str, Any], next_rows: list[dict]) -> Optional[DeFiMetadata]:
    """
    Detect Uniswap swap pattern:
    - User calls router contract
    - Router transfers token A from user
    - Router receives token B to user
    """
    # Check if interaction is with Uniswap router
    to_addr = _normalize_addr(df_row.get("to_wallet", ""))
    known_addrs = {_normalize_addr(k): v for k, v in KNOWN_ADDRESSES.items()}

    if to_addr not in known_addrs:
        return None

    info = known_addrs[to_addr]
    if info["protocol"] not in [DeFiProtocol.UNISWAP_V2, DeFiProtocol.UNISWAP_V3]:
        return None

    # Look for swap pattern: input token transfer + output token transfer
    tx_hash = df_row.get("external_id", "")
    timestamp = df_row.get("timestamp", pd.Timestamp.now())

    # For now, simple heuristic: swaps have 2 related token transfers
    if df_row.get("type") == "SWAP":
        token_in = df_row.get("asset", "UNKNOWN")
        amount_in = df_row.get("amount", 0.0)

        # Try to find corresponding output in next rows
        for next_row in next_rows[:2]:  # Look in next 2 rows
            if (next_row.get("external_id") == tx_hash
                    and next_row.get("type") == "SWAP"
                    and next_row.get("asset") != token_in):
                token_out = next_row.get("asset", "UNKNOWN")
                amount_out = next_row.get("amount", 0.0)

                return DeFiMetadata(
                    protocol=info["protocol"],
                    event_type=DeFiEventType.SWAP,
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                    tokens_in={token_in: amount_in},
                    tokens_out={token_out: amount_out},
                    prices={
                        token_in: df_row.get("price", 0.0),
                        token_out: next_row.get("price", 0.0),
                    },
                    fee_usd=df_row.get("fee", 0.0) * df_row.get("price", 0.0),
                )

    return None


def _detect_uniswap_lp(df_row: dict[str, Any], next_rows: list[dict]) -> Optional[DeFiMetadata]:
    """
    Detect Uniswap V2 LP provision/removal:
    - LP Add: Send 2 tokens, receive 1 LP token
    - LP Remove: Send 1 LP token, receive 2 tokens
    """
    tx_hash = df_row.get("external_id", "")
    timestamp = df_row.get("timestamp", pd.Timestamp.now())
    tx_type = df_row.get("type", "").upper()

    # Heuristic for LP Add
    if tx_type == "TRANSFER":
        # Look for a corresponding transfer of another token in the same TX
        # and a receipt of an LP token
        related_txs = [df_row] + [r for r in next_rows if r.get("external_id") == tx_hash]
        if len(related_txs) >= 3:
            transfers = [t for t in related_txs if t.get("type") == "TRANSFER"]
            receives = [t for t in related_txs if t.get("type") == "RECEIVE"]
            
            if len(transfers) >= 2 and len(receives) >= 1:
                # Check if it's a known router or pool
                tokens_in = {t["asset"]: t["amount"] for t in transfers}
                tokens_out = {t["asset"]: t["amount"] for t in receives}
                
                return DeFiMetadata(
                    protocol=DeFiProtocol.UNISWAP_V2,
                    event_type=DeFiEventType.LP_ADD,
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    prices={} 
                )

    # Heuristic for LP Remove
    if tx_type == "RECEIVE":
        related_txs = [df_row] + [r for r in next_rows if r.get("external_id") == tx_hash]
        if len(related_txs) >= 3:
            transfers = [t for t in related_txs if t.get("type") == "TRANSFER"]
            receives = [t for t in related_txs if t.get("type") == "RECEIVE"]
            
            if len(receives) >= 2 and len(transfers) >= 1:
                tokens_in = {t["asset"]: t["amount"] for t in transfers}
                tokens_out = {t["asset"]: t["amount"] for t in receives}
                
                return DeFiMetadata(
                    protocol=DeFiProtocol.UNISWAP_V2,
                    event_type=DeFiEventType.LP_REMOVE,
                    tx_hash=tx_hash,
                    timestamp=timestamp,
                    tokens_in=tokens_in,
                    tokens_out=tokens_out,
                    prices={} 
                )

    return None


def _detect_aave_interaction(df_row: dict[str, Any]) -> Optional[DeFiMetadata]:
    """
    Detect Aave lending/borrowing:
    - Deposit: Transfer USDC/DAI/USDT to Aave, receive aUSDC/aDAI/aUSDT
    - Withdraw: Burn aToken, receive underlying asset
    - Borrow: aToken holder gets new liability
    """
    to_addr = _normalize_addr(df_row.get("to_wallet", ""))
    known_addrs = {_normalize_addr(k): v for k, v in KNOWN_ADDRESSES.items()}

    if to_addr not in known_addrs:
        return None

    info = known_addrs[to_addr]
    if info["protocol"] != DeFiProtocol.AAVE:
        return None

    asset = df_row.get("asset", "")
    tx_type = df_row.get("type", "")
    timestamp = df_row.get("timestamp", pd.Timestamp.now())
    tx_hash = df_row.get("external_id", "")

    # Detect based on asset type
    if asset.startswith("a"):  # aToken (like aUSDC, aDAI)
        # Could be deposit (receive aToken) or withdraw (burn aToken)
        if tx_type == "RECEIVE":
            return DeFiMetadata(
                protocol=DeFiProtocol.AAVE,
                event_type=DeFiEventType.LENDING_DEPOSIT,
                tx_hash=tx_hash,
                timestamp=timestamp,
                tokens_in={asset[1:]: df_row.get("amount", 0.0)},
                tokens_out={asset: df_row.get("amount", 0.0)},
                prices={asset: df_row.get("price", 0.0)},
            )
        elif tx_type == "TRANSFER":
            return DeFiMetadata(
                protocol=DeFiProtocol.AAVE,
                event_type=DeFiEventType.LENDING_WITHDRAW,
                tx_hash=tx_hash,
                timestamp=timestamp,
                tokens_in={asset: df_row.get("amount", 0.0)},
                tokens_out={asset[1:]: df_row.get("amount", 0.0)},
                prices={asset: df_row.get("price", 0.0)},
            )

    return None


def _detect_lido_staking(df_row: dict[str, Any]) -> Optional[DeFiMetadata]:
    """
    Detect Lido staking:
    - User sends ETH to Lido contract
    - Receives stETH in return
    """
    asset = df_row.get("asset", "").upper()
    tx_type = df_row.get("type", "")
    timestamp = df_row.get("timestamp", pd.Timestamp.now())
    tx_hash = df_row.get("external_id", "")

    # Simple heuristic: ETH transfer to Lido address or stETH receipt
    if asset in ["ETH", "stETH"]:
        to_addr = _normalize_addr(df_row.get("to_wallet", ""))
        known_addrs = {_normalize_addr(k): v for k, v in KNOWN_ADDRESSES.items()}

        if to_addr in known_addrs:
            info = known_addrs[to_addr]
            if info["protocol"] == DeFiProtocol.LIDO:
                if asset == "stETH" and tx_type == "RECEIVE":
                    return DeFiMetadata(
                        protocol=DeFiProtocol.LIDO,
                        event_type=DeFiEventType.STAKING_DEPOSIT,
                        tx_hash=tx_hash,
                        timestamp=timestamp,
                        tokens_in={"ETH": df_row.get("amount", 0.0)},
                        tokens_out={"stETH": df_row.get("amount", 0.0)},
                        prices={"stETH": df_row.get("price", 0.0)},
                    )

    return None


def _detect_generic_swap(df_row: dict[str, Any]) -> Optional[DeFiMetadata]:
    """
    Detect generic swap from transaction type.
    """
    if df_row.get("type") != "SWAP":
        return None

    return DeFiMetadata(
        protocol=DeFiProtocol.GENERIC_SWAP,
        event_type=DeFiEventType.SWAP,
        tx_hash=df_row.get("external_id", ""),
        timestamp=df_row.get("timestamp", pd.Timestamp.now()),
        tokens_in={df_row.get("asset", "UNKNOWN"): df_row.get("amount", 0.0)},
        tokens_out={},  # Would need output data from blockchain
        prices={df_row.get("asset", "UNKNOWN"): df_row.get("price", 0.0)},
        fee_usd=df_row.get("fee", 0.0),
    )


def _detect_staking_reward(df_row: dict[str, Any]) -> Optional[DeFiMetadata]:
    """
    Detect staking rewards (INTEREST, STAKING transaction types).
    """
    tx_type = df_row.get("type", "")
    if tx_type not in ["INTEREST", "STAKING"]:
        return None

    return DeFiMetadata(
        protocol=DeFiProtocol.LIDO if df_row.get("asset", "").upper() == "stETH" else DeFiProtocol.YIELD_FARMING,
        event_type=DeFiEventType.STAKING_REWARD if tx_type == "STAKING" else DeFiEventType.FARMING_REWARD,
        tx_hash=df_row.get("external_id", ""),
        timestamp=df_row.get("timestamp", pd.Timestamp.now()),
        tokens_in={},
        tokens_out={df_row.get("asset", "UNKNOWN"): df_row.get("amount", 0.0)},
        prices={df_row.get("asset", "UNKNOWN"): df_row.get("price", 0.0)},
        yield_earned=df_row.get("amount", 0.0) * df_row.get("price", 1.0),
    )


# ============================================================================
# MAIN RECOGNITION ENGINE
# ============================================================================


def recognize_defi_events(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recognize DeFi events in blockchain transaction data.

    Args:
        df: DataFrame with normalized transaction columns
            (timestamp, asset, type, amount, fee, from_wallet, to_wallet, external_id, etc.)

    Returns:
        DataFrame with added columns:
        - defi_protocol: DeFiProtocol enum or None
        - defi_event_type: DeFiEventType enum or None
        - defi_tokens_in: JSON dict of input tokens
        - defi_tokens_out: JSON dict of output tokens
    """
    if df.empty:
        df["defi_protocol"] = None
        df["defi_event_type"] = None
        df["defi_tokens_in"] = None
        df["defi_tokens_out"] = None
        df["defi_yield_earned_usd"] = 0.0
        return df

    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    results = {
        "defi_protocol": [],
        "defi_event_type": [],
        "defi_tokens_in": [],
        "defi_tokens_out": [],
        "defi_yield_earned_usd": [],
    }

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        next_rows = [df.iloc[j].to_dict() for j in range(idx + 1, min(idx + 5, len(df)))]

        metadata = None

        # Try each detector in order
        detectors = [
            _detect_uniswap_swap,
            _detect_uniswap_lp,
            _detect_aave_interaction,
            _detect_lido_staking,
            _detect_staking_reward,
            _detect_generic_swap,
        ]

        for detector in detectors:
            try:
                if detector.__name__.startswith("_detect_uniswap"):
                    metadata = detector(row_dict, next_rows)
                else:
                    metadata = detector(row_dict)

                if metadata:
                    break
            except Exception as e:
                # Silently skip errors in detection
                pass

        # Try plugins if no built-in detector matched
        if not metadata:
            from app.integrations.plugins.plugin_registry import registry
            for plugin in registry.get_all():
                try:
                    metadata = plugin.detect(row_dict, next_rows)
                    if metadata:
                        break
                except Exception:
                    pass

        if metadata:
            results["defi_protocol"].append(metadata.protocol.value)
            results["defi_event_type"].append(metadata.event_type.value)
            results["defi_tokens_in"].append(metadata.tokens_in)
            results["defi_tokens_out"].append(metadata.tokens_out)
            results["defi_yield_earned_usd"].append(metadata.yield_earned or 0.0)
        else:
            results["defi_protocol"].append(None)
            results["defi_event_type"].append(None)
            results["defi_tokens_in"].append(None)
            results["defi_tokens_out"].append(None)
            results["defi_yield_earned_usd"].append(0.0)

    for col, values in results.items():
        df[col] = values

    return df


def get_supported_protocols() -> dict[str, dict[str, Any]]:
    """Return supported DeFi protocols with metadata."""
    protocols = {
        "uniswap_v2": {
            "name": "Uniswap V2",
            "description": "Decentralized exchange with AMM",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism"],
            "events": ["swap", "lp_add", "lp_remove"],
        },
        "uniswap_v3": {
            "name": "Uniswap V3",
            "description": "Decentralized exchange with concentrated liquidity",
            "chains": ["ethereum", "polygon", "arbitrum", "optimism"],
            "events": ["swap", "lp_add", "lp_remove"],
        },
        "aave": {
            "name": "Aave",
            "description": "Lending protocol",
            "chains": ["ethereum", "polygon", "avalanche", "arbitrum"],
            "events": ["lending_deposit", "lending_withdraw", "lending_borrow", "lending_repay"],
        },
        "curve": {
            "name": "Curve",
            "description": "Stablecoin-focused AMM",
            "chains": ["ethereum", "polygon", "arbitrum"],
            "events": ["swap", "lp_add", "lp_remove"],
        },
        "lido": {
            "name": "Lido",
            "description": "Ethereum staking",
            "chains": ["ethereum"],
            "events": ["staking_deposit", "staking_reward", "staking_unstake"],
        },
        "compound": {
            "name": "Compound",
            "description": "Lending protocol",
            "chains": ["ethereum"],
            "events": ["lending_deposit", "lending_withdraw", "lending_borrow"],
        },
    }

    # Add plugins
    from app.integrations.plugins.plugin_registry import registry
    for plugin in registry.get_all():
        protocols[plugin.name.lower()] = {
            "name": plugin.name,
            "description": f"{plugin.name} Plugin (v{plugin.version})",
            "chains": plugin.supported_chains,
            "events": plugin.supported_events,
            "is_plugin": True,
        }
    
    return protocols


def classify_for_tax(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add tax classification to DeFi events.

    Returns DataFrame with added column:
    - tax_event_type: One of 'income', 'capital_gain', 'capital_loss', 'expense', 'non_taxable'
    """
    df = df.copy()

    def _classify_single(row) -> str:
        event_type = row.get("defi_event_type")

        # Income events
        if event_type in ["defi_staking_reward", "defi_farming_reward", "defi_governance_claim"]:
            return "income"

        # Capital gain/loss events (need comparison with cost basis)
        if event_type in ["defi_swap", "defi_lp_remove", "defi_lending_withdraw", "defi_staking_unstake"]:
            return "capital_gain"

        # Non-taxable events (position entry)
        if event_type in ["defi_lp_add", "defi_lending_deposit", "defi_staking_deposit", "defi_farming_deposit"]:
            return "non_taxable"

        # Expenses (may be deductible)
        if event_type in ["defi_lending_repay"]:
            return "expense"

        # Default for unknown
        return "non_taxable"

    df["tax_event_type"] = df.apply(_classify_single, axis=1)
    return df
