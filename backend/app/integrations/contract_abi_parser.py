"""
Contract ABI Parser & Signature Decoder for DeFi Transaction Detection.

Decodes smart contract interactions by parsing function signatures from transaction calldata.
Helps identify specific protocol interactions (Uniswap swap, Aave borrow, etc.).
"""

from __future__ import annotations

import hashlib
from typing import Any, Optional

# Common DeFi function signatures (function_selector: function_info)
FUNCTION_SIGNATURES = {
    # Uniswap V2 Router
    "0x7ff36ab5": {
        "name": "swapExactETHForTokens",
        "protocol": "uniswap_v2",
        "category": "swap",
    },
    "0x18cbafe5": {
        "name": "swapExactTokensForETH",
        "protocol": "uniswap_v2",
        "category": "swap",
    },
    "0x38ed1739": {
        "name": "swapExactTokensForTokens",
        "protocol": "uniswap_v2",
        "category": "swap",
    },
    "0x8803dbee": {
        "name": "swapTokensForExactETH",
        "protocol": "uniswap_v2",
        "category": "swap",
    },
    "0x4a25d94a": {
        "name": "swapTokensForExactTokens",
        "protocol": "uniswap_v2",
        "category": "swap",
    },

    # Uniswap V3 SwapRouter
    "0x414bf389": {
        "name": "exactInputSingle",
        "protocol": "uniswap_v3",
        "category": "swap",
    },
    "0x41e78e06": {
        "name": "exactOutputSingle",
        "protocol": "uniswap_v3",
        "category": "swap",
    },
    "0x7c025200": {
        "name": "exactInputMultihop",
        "protocol": "uniswap_v3",
        "category": "swap",
    },

    # Aave V2 LendingPool
    "0x617ba037": {
        "name": "deposit",
        "protocol": "aave",
        "category": "lending_deposit",
    },
    "0x69328dec": {
        "name": "withdraw",
        "protocol": "aave",
        "category": "lending_withdraw",
    },
    "0xc6e41e67": {
        "name": "borrow",
        "protocol": "aave",
        "category": "lending_borrow",
    },
    "0x573ade81": {
        "name": "repay",
        "protocol": "aave",
        "category": "lending_repay",
    },

    # Aave V3 Pool
    "0xe8eda9df": {
        "name": "supply",
        "protocol": "aave",
        "category": "lending_deposit",
    },
    "0x3b6b2d57": {
        "name": "withdraw",
        "protocol": "aave",
        "category": "lending_withdraw",
    },
    "0x59ce432b": {
        "name": "borrow",
        "protocol": "aave",
        "category": "lending_borrow",
    },
    "0xd5eed868": {
        "name": "repay",
        "protocol": "aave",
        "category": "lending_repay",
    },

    # Curve Exchange
    "0x3df02124": {
        "name": "exchange",
        "protocol": "curve",
        "category": "swap",
    },
    "0xa6417ed6": {
        "name": "add_liquidity",
        "protocol": "curve",
        "category": "lp_add",
    },
    "0x0b86991c": {
        "name": "remove_liquidity",
        "protocol": "curve",
        "category": "lp_remove",
    },

    # ERC20 Approve & Transfer
    "0x095ea7b3": {
        "name": "approve",
        "protocol": "erc20",
        "category": "approval",
    },
    "0xa9059cbb": {
        "name": "transfer",
        "protocol": "erc20",
        "category": "transfer",
    },
    "0x23b872dd": {
        "name": "transferFrom",
        "protocol": "erc20",
        "category": "transfer",
    },

    # Staking
    "0x1e9140b6": {
        "name": "stake",
        "protocol": "staking",
        "category": "staking_deposit",
    },
    "0x2e1a7d4d": {
        "name": "withdraw",
        "protocol": "staking",
        "category": "staking_withdraw",
    },
    "0xc00007b0": {
        "name": "claimReward",
        "protocol": "staking",
        "category": "staking_reward",
    },

    # Liquidity Mining
    "0x4cd88b76": {
        "name": "addLiquidity",
        "protocol": "liquidity_mining",
        "category": "lp_add",
    },
    "0xbaa2abde": {
        "name": "removeLiquidity",
        "protocol": "liquidity_mining",
        "category": "lp_remove",
    },

    # Flash Loans
    "0xab9c4b5d": {
        "name": "flashLoan",
        "protocol": "flash_loan",
        "category": "flash_loan",
    },
}

# Event signatures (topic0 hash: event_info)
EVENT_SIGNATURES = {
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": {
        "name": "Transfer",
        "params": ["from", "to", "value"],
    },
    "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": {
        "name": "Approval",
        "params": ["owner", "spender", "value"],
    },
    "0xd78ad95fa46ab8d7b860cb9fba9c09764d52c75247f21ba0ea41d8980424476fb": {
        "name": "Swap",
        "params": ["sender", "amount0In", "amount1Out", "to"],
    },
    "0xe1fffcc4923d04b559f4d29a8bfc6cda04eb5b0d3c460751c2402c5c5cc9109c": {
        "name": "Deposit",
        "params": ["dst", "wad"],
    },
    "0x7fcf532c15f0a6db0bd6d0e038bea71d30d808c7d98cb3bf7268a95bf5081b65": {
        "name": "Withdrawal",
        "params": ["src", "wad"],
    },
}


def decode_function_call(calldata: str) -> Optional[dict[str, Any]]:
    """
    Decode transaction calldata to identify function being called.

    Args:
        calldata: Transaction input data (hex string starting with 0x)

    Returns:
        Dict with function info or None if not recognized
    """
    if not calldata or not isinstance(calldata, str):
        return None

    # Extract first 4 bytes (function selector)
    if calldata.startswith("0x"):
        calldata = calldata[2:]

    if len(calldata) < 8:
        return None

    selector = "0x" + calldata[:8]

    if selector in FUNCTION_SIGNATURES:
        return FUNCTION_SIGNATURES[selector]

    return None


def decode_event_log(topic0: str) -> Optional[dict[str, Any]]:
    """
    Decode transaction log to identify event emitted.

    Args:
        topic0: First topic from transaction log (event signature hash)

    Returns:
        Dict with event info or None if not recognized
    """
    if not topic0:
        return None

    # Normalize to 0x format
    if not topic0.startswith("0x"):
        topic0 = "0x" + topic0

    if topic0 in EVENT_SIGNATURES:
        return EVENT_SIGNATURES[topic0]

    return None


def compute_function_selector(signature: str) -> str:
    """
    Compute function selector (first 4 bytes of keccak256 hash of signature).

    Example:
        >>> compute_function_selector("transfer(address,uint256)")
        '0xa9059cbb'
    """
    keccak = hashlib.sha3_256()
    keccak.update(signature.encode())
    hash_bytes = keccak.digest()
    return "0x" + hash_bytes[:4].hex()


def compute_event_signature(signature: str) -> str:
    """
    Compute event signature (first 4 bytes of keccak256 hash).

    Example:
        >>> compute_event_signature("Transfer(address,address,uint256)")
        '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
    """
    keccak = hashlib.sha3_256()
    keccak.update(signature.encode())
    hash_bytes = keccak.digest()
    return "0x" + hash_bytes[:4].hex()


def extract_calldata_params(calldata: str, num_params: int = 4) -> list[str]:
    """
    Extract parameter data from calldata.

    Args:
        calldata: Full transaction input data (starting with function selector)
        num_params: Number of 32-byte parameters to extract

    Returns:
        List of hex-encoded parameter values
    """
    if not calldata or len(calldata) < 10:
        return []

    # Skip first 10 chars (0x + 8 hex chars for selector)
    params_data = calldata[10:]

    params = []
    for i in range(num_params):
        start = i * 64
        end = start + 64
        if end <= len(params_data):
            params.append("0x" + params_data[start:end])

    return params


def extract_amounts_from_calldata(calldata: str) -> dict[str, int]:
    """
    Attempt to extract token amounts from transaction calldata.

    Returns dict with 'inAmount', 'outAmount', etc. if detectable
    """
    params = extract_calldata_params(calldata, num_params=4)

    if len(params) < 2:
        return {}

    amounts = {}

    # First parameter often amount
    try:
        amounts["amount0"] = int(params[0], 16)
    except (ValueError, IndexError):
        pass

    # Second parameter sometimes min/max amount
    try:
        amounts["amount1"] = int(params[1], 16)
    except (ValueError, IndexError):
        pass

    return amounts


def get_protocol_from_calldata(calldata: str) -> Optional[str]:
    """Get protocol name from transaction calldata."""
    func_info = decode_function_call(calldata)
    if func_info:
        return func_info.get("protocol")
    return None


def get_transaction_category(calldata: str) -> Optional[str]:
    """Get transaction category (swap, lending, etc.) from calldata."""
    func_info = decode_function_call(calldata)
    if func_info:
        return func_info.get("category")
    return None


def is_defi_interaction(calldata: str) -> bool:
    """Check if transaction is a DeFi interaction."""
    func_info = decode_function_call(calldata)
    if not func_info:
        return False

    protocol = func_info.get("protocol")
    # Exclude pure ERC20 transfers (not DeFi protocol)
    return protocol not in [None, "erc20"]


def get_known_defi_signatures() -> dict[str, dict[str, Any]]:
    """Return all known function signatures for reference."""
    return FUNCTION_SIGNATURES.copy()


def get_known_event_signatures() -> dict[str, dict[str, Any]]:
    """Return all known event signatures for reference."""
    return EVENT_SIGNATURES.copy()
