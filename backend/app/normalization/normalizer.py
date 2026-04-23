from __future__ import annotations

from typing import Iterable
import numpy as np
import pandas as pd

REQUIRED_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "asset",
    "type",
    "amount",
    "fee",
    "from_wallet",
    "to_wallet",
)

# ИСПРАВЛЕНО: добавлен "TRADE" — calculator.py его обрабатывает
# + Income types для tax recognition (STAKING_REWARD, AIRDROP, LENDING_INTEREST, etc.)
ALLOWED_TYPES: tuple[str, ...] = (
    "BUY",
    "SELL",
    "TRANSFER",
    "RECEIVE",
    "SWAP",
    "TRADE",
    # Legacy income types (aliases)
    "INTEREST",
    "STAKING",
    "AIRDROP",
    "LENDING",
    "MINING",
    # Standardized income types (primary)
    "STAKING_REWARD",
    "AIRDROP",
    "LENDING_INTEREST",
    "MINING_REWARD",
    "FARMING_REWARD",
    "REWARD",
    "INCOME",
    # Blockchain interaction types
    "BRIDGE",
    "APPROVE",
    "TOKEN_TRANSFER",
    "NFT_TRANSFER",
    "MINT",
    "NFT_MINT",
    "BURN",
    "WRAP",
    "UNWRAP",
    "FORK",
    # DeFi types
    "DEPOSIT",
    "WITHDRAWAL",
    "LP_ADD",
    "LP_REMOVE",
    "DEFI_LP_ADD",
    "DEFI_LP_REMOVE",
    "CLAIM",
    # Derivatives
    "LIQUIDATION",
    "FUTURES_PNL",
)

COLUMN_ALIASES: dict[str, str] = {
    "date": "timestamp",
    "time": "timestamp",
    "currency": "asset",
    "symbol": "asset",
    "token_symbol": "asset",
    "transaction_type": "type",
    "side": "type",
    "quantity": "amount",
    "size": "amount",
    "value": "amount",
    "commission": "fee",
    "gas_fee": "fee",
    "fee_amount": "fee",
    "from_address": "from_wallet",
    "to_address": "to_wallet",
    "tx_hash": "external_id",
    "transaction_hash": "external_id",
}

def normalize(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()
    
    normalized["timestamp"] = pd.to_datetime(normalized["timestamp"], errors="coerce")
    if normalized["timestamp"].isna().any():
        raise ValueError("Some timestamps cannot be parsed. Check CSV format.")

    normalized["asset"] = normalized["asset"].astype(str).str.strip().str.upper()
    normalized["type"] = normalized["type"].astype(str).str.strip().str.upper()
    
    invalid_types = sorted(set(normalized["type"]) - set(ALLOWED_TYPES))
    if invalid_types:
        raise ValueError(f"Unknown transaction types: {invalid_types}")

    normalized["amount"] = pd.to_numeric(normalized["amount"], errors="coerce").astype("float64")
    normalized["fee"] = pd.to_numeric(normalized["fee"], errors="coerce").fillna(0.0).astype("float64")
    
    if normalized["amount"].isna().any():
        raise ValueError("Some amounts cannot be parsed as numbers.")

    normalized["from_wallet"] = normalized["from_wallet"].fillna("").astype(str).str.strip()
    normalized["to_wallet"] = normalized["to_wallet"].fillna("").astype(str).str.strip()
    
    if "network" not in normalized.columns:
        normalized["network"] = "unknown"

    # ==================== ИСПРАВЛЕНИЕ FEE_ASSET ====================
    if "fee_asset" not in normalized.columns:
        normalized["fee_asset"] = normalized.apply(_guess_fee_asset, axis=1)
    else:
        normalized["fee_asset"] = normalized["fee_asset"].astype(str).str.strip().str.upper()
    # ============================================================

    if "price" in normalized.columns:
        normalized["price"] = pd.to_numeric(normalized["price"], errors="coerce").astype("float64")
    else:
        normalized["price"] = pd.Series([np.nan] * len(normalized), dtype="float64")
        
    if "total_value" in normalized.columns:
        normalized["total_value"] = pd.to_numeric(normalized["total_value"], errors="coerce").astype("float64")
    else:
        normalized["total_value"] = pd.Series([np.nan] * len(normalized), dtype="float64")

    price_missing = normalized["price"].isna() & normalized["total_value"].notna() & (normalized["amount"] != 0)
    normalized.loc[price_missing, "price"] = normalized.loc[price_missing, "total_value"] / normalized.loc[price_missing, "amount"]
    
    if "external_id" not in normalized.columns:
        normalized["external_id"] = ""
    
    return normalized


def _guess_fee_asset(row) -> str:
    """Умная догадка fee_asset когда колонки нет в CSV"""
    tx_type = row["type"]
    asset = row["asset"]
    
    if tx_type in ["TRANSFER", "RECEIVE"]:
        return asset  # обычно комиссия платится тем же активом (или native)
    
    if tx_type in ["BUY", "SELL", "SWAP", "TRADE"]:
        # Для биржевых операций комиссия чаще всего в native токене
        if asset in ["ETH", "BNB", "MATIC", "AVAX", "SOL", "BTC"]:
            return asset
        # fallback — считаем, что это централизованная биржа (Binance и т.п.)
        return "ETH"   # или "BNB", если знаешь, что у тебя Binance
    
    return "ETH"  # самый безопасный дефолт

def group_swaps(df: pd.DataFrame, max_time_diff_sec: int = 2) -> pd.DataFrame:
    if df.empty:
        return df
        
    df = df.sort_values("timestamp").reset_index(drop=True)
    processed_indices = set()
    new_rows = []
    stables = ["USD", "USDT", "USDC", "DAI", "BUSD", "PYUSD"]

    for i in range(len(df)):
        if i in processed_indices:
            continue
            
        current_tx = df.iloc[i]
        match_found = False

        for j in range(i + 1, len(df)):
            if j in processed_indices:
                continue
                
            next_tx = df.iloc[j]
            time_diff = (next_tx["timestamp"] - current_tx["timestamp"]).total_seconds()
            
            if time_diff > max_time_diff_sec:
                break
            
            is_opposite = (
                (current_tx["type"] in ["TRANSFER", "SELL"] and next_tx["type"] in ["RECEIVE", "BUY"]) or
                (current_tx["type"] in ["RECEIVE", "BUY"] and next_tx["type"] in ["TRANSFER", "SELL"])
            )
            same_network = current_tx.get("network") == next_tx.get("network")
            is_via_stable = current_tx["asset"] in stables or next_tx["asset"] in stables

            if is_opposite and same_network and not is_via_stable:
                out_tx = current_tx if current_tx["type"] in ["TRANSFER", "SELL"] else next_tx
                in_tx = next_tx if out_tx is current_tx else current_tx
                
                swap_row = {
                    "timestamp": out_tx["timestamp"],
                    "type": "SWAP",
                    "asset": "SWAP",
                    "asset_out": out_tx["asset"],
                    "amount_out": out_tx["amount"],
                    "asset_in": in_tx["asset"],
                    "amount_in": in_tx["amount"],
                    "fee": float(out_tx.get("fee", 0) or 0) + float(in_tx.get("fee", 0) or 0),
                    "fee_asset": str(out_tx.get("fee_asset", "ETH")),
                    "network": out_tx["network"],
                    "from_wallet": out_tx["from_wallet"],
                    "to_wallet": in_tx["to_wallet"]
                }
                new_rows.append(swap_row)
                processed_indices.add(i)
                processed_indices.add(j)
                match_found = True
                break
        
        if not match_found:
            new_rows.append(current_tx.to_dict())

    return pd.DataFrame(new_rows)

def apply_column_aliases(df: pd.DataFrame) -> pd.DataFrame:
    rename_map: dict[str, str] = {}
    for column in df.columns:
        normalized_name = str(column).strip().lower()
        if normalized_name in COLUMN_ALIASES:
            rename_map[column] = COLUMN_ALIASES[normalized_name]
    return df.rename(columns=rename_map) if rename_map else df

def validate_required_columns(columns: Iterable[str]) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")