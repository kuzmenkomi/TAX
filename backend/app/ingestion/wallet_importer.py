from __future__ import annotations

"""
wallet_importer.py
──────────────────
Killer feature: пользователь вставляет адрес кошелька →
система сама тянет транзакции и превращает их в наш формат.

Поддерживаемые сети:
  • Ethereum  (Etherscan API — бесплатный ключ)
  • BSC       (BscScan API)
  • Polygon   (PolygonScan API)
  • Solana    (Solscan public API, без ключа)

Добавить новую сеть: скопируй EVMImporter, поменяй base_url.
"""

import re
import time
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import requests

# ─── Детектор сети по адресу ────────────────────────────────────────────────

def detect_network(address: str) -> str:
    address = address.strip()
    if re.match(r"^0x[0-9a-fA-F]{40}$", address):
        return "evm"          # Ethereum / BSC / Polygon — определяем по выбору юзера
    if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
        return "solana"
    raise ValueError(
        f"Не удалось определить сеть по адресу '{address}'. "
        "Поддерживаются: EVM (0x...) и Solana (base58)."
    )


# ─── EVM-совместимые сети (ETH, BSC, Polygon) ───────────────────────────────

EVM_EXPLORERS: dict[str, dict] = {
    "ethereum": {
        "api_url":    "https://api.etherscan.io/api",
        "native":     "ETH",
        "chain_name": "Ethereum",
    },
    "bsc": {
        "api_url":    "https://api.bscscan.com/api",
        "native":     "BNB",
        "chain_name": "BSC",
    },
    "polygon": {
        "api_url":    "https://api.polygonscan.com/api",
        "native":     "MATIC",
        "chain_name": "Polygon",
    },
}


def _get_explorer_api_key(chain: str) -> str:
    """Get blockchain explorer API key from app config."""
    try:
        from app.core.config import get_settings
        settings = get_settings()
        key_map = {
            "ethereum": settings.ETHERSCAN_API_KEY,
            "bsc": settings.BSCSCAN_API_KEY,
            "polygon": settings.POLYGONSCAN_API_KEY,
        }
        return key_map.get(chain, "")
    except Exception:
        return ""


class EVMImporter:
    def __init__(self, chain: str = "ethereum", api_key: str = ""):
        cfg = EVM_EXPLORERS.get(chain)
        if not cfg:
            raise ValueError(f"Неизвестная EVM-цепь: {chain}. Доступны: {list(EVM_EXPLORERS)}")
        self.api_url    = cfg["api_url"]
        self.native     = cfg["native"]
        self.chain_name = cfg["chain_name"]
        self.api_key    = api_key or _get_explorer_api_key(chain)  # из .env конфига

    def fetch(self, address: str, start_block: int = 0) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []

        # 1. Нативные транзакции (ETH/BNB/MATIC)
        rows.extend(self._fetch_normal_txs(address, start_block))

        # 2. ERC-20 токены
        rows.extend(self._fetch_token_txs(address, start_block))

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    # ── Нативные транзакции ────────────────────────────────────────────────

    def _fetch_normal_txs(self, address: str, start_block: int) -> list[dict]:
        data = self._call_api(
            module="account", action="txlist",
            address=address, startblock=start_block,
            sort="asc",
        )
        rows = []
        for tx in data:
            val = int(tx.get("value", 0))
            if val == 0:
                continue  # пропускаем нулевые (чистые вызовы контрактов)

            amount_eth  = val / 1e18
            fee_wei     = int(tx.get("gasUsed", 0)) * int(tx.get("gasPrice", 0))
            fee_eth     = fee_wei / 1e18
            ts          = int(tx["timeStamp"])
            addr_lower  = address.lower()
            is_incoming = tx["to"].lower() == addr_lower

            rows.append({
                "timestamp":   datetime.fromtimestamp(ts, tz=timezone.utc),
                "type":        "RECEIVE" if is_incoming else "TRANSFER",
                "asset":       self.native,
                "amount":      amount_eth,
                "fee":         fee_eth if not is_incoming else 0.0,
                "fee_asset":   self.native,
                "from_wallet": tx["from"],
                "to_wallet":   tx["to"],
                "network":     self.chain_name,
                "external_id": tx["hash"],
                "price":       None,
                "total_value": None,
            })
        return rows

    # ── ERC-20 токены ──────────────────────────────────────────────────────

    def _fetch_token_txs(self, address: str, start_block: int) -> list[dict]:
        data = self._call_api(
            module="account", action="tokentx",
            address=address, startblock=start_block,
            sort="asc",
        )
        rows = []
        for tx in data:
            decimals   = int(tx.get("tokenDecimal", 18))
            raw_val    = int(tx.get("value", 0))
            amount     = raw_val / (10 ** decimals)
            if amount == 0:
                continue

            ts         = int(tx["timeStamp"])
            addr_lower = address.lower()
            is_incoming = tx["to"].lower() == addr_lower

            rows.append({
                "timestamp":   datetime.fromtimestamp(ts, tz=timezone.utc),
                "type":        "RECEIVE" if is_incoming else "TRANSFER",
                "asset":       tx.get("tokenSymbol", "UNKNOWN").upper(),
                "amount":      amount,
                "fee":         0.0,   # комиссия уже учтена в нативной tx
                "fee_asset":   self.native,
                "from_wallet": tx["from"],
                "to_wallet":   tx["to"],
                "network":     self.chain_name,
                "external_id": tx["hash"] + "_erc20",
                "price":       None,
                "total_value": None,
            })
        return rows

    # ── HTTP ──────────────────────────────────────────────────────────────

    def _call_api(self, **params) -> list[dict]:
        params["apikey"] = self.api_key
        try:
            r = requests.get(self.api_url, params=params, timeout=10)
            r.raise_for_status()
            body = r.json()
            if body.get("status") == "1":
                return body.get("result", [])
            # status=0 означает либо "No transactions" либо ошибку
            msg = body.get("message", "")
            if "No transactions" in msg or body.get("result") == []:
                return []
            print(f"⚠️  [EVMImporter] API ответил: {body.get('message')} — {body.get('result')}")
            return []
        except Exception as e:
            print(f"⚠️  [EVMImporter] Ошибка запроса: {e}")
            return []


# ─── Solana ──────────────────────────────────────────────────────────────────

class SolanaImporter:
    """
    Использует публичный Solscan API (без ключа).
    Возвращает SOL-транзакции. SPL-токены — TODO.
    """

    BASE = "https://public-api.solscan.io"

    def fetch(self, address: str) -> pd.DataFrame:
        rows: list[dict] = []
        offset = 0
        limit  = 50

        while True:
            try:
                r = requests.get(
                    f"{self.BASE}/account/transactions",
                    params={"account": address, "limit": limit, "offset": offset},
                    headers={"accept": "application/json"},
                    timeout=10,
                )
                r.raise_for_status()
                txs = r.json()
            except Exception as e:
                print(f"⚠️  [SolanaImporter] {e}")
                break

            if not txs:
                break

            for tx in txs:
                # Solscan возвращает изменение баланса в lamports
                change = tx.get("changeAmount", {}).get(address, 0)
                if change == 0:
                    continue
                amount = abs(change) / 1e9
                fee_lamports = tx.get("fee", 0)
                ts = tx.get("blockTime", 0)

                rows.append({
                    "timestamp":   datetime.fromtimestamp(ts, tz=timezone.utc),
                    "type":        "RECEIVE" if change > 0 else "TRANSFER",
                    "asset":       "SOL",
                    "amount":      amount,
                    "fee":         fee_lamports / 1e9,
                    "fee_asset":   "SOL",
                    "from_wallet": "",
                    "to_wallet":   address if change > 0 else "",
                    "network":     "Solana",
                    "external_id": tx.get("txHash", ""),
                    "price":       None,
                    "total_value": None,
                })

            if len(txs) < limit:
                break
            offset += limit
            time.sleep(0.5)

        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)


# ─── Фасад ───────────────────────────────────────────────────────────────────

def import_wallet(
    address: str,
    chain: str = "ethereum",
    etherscan_api_key: str = "",
) -> pd.DataFrame:
    """
    Главная функция. Определяет тип адреса, тянет транзакции.

    Возвращает DataFrame в нашем нормализованном формате
    (совместим с normalizer.normalize).

    chain — нужен только для EVM адресов: "ethereum", "bsc", "polygon"
    """
    network = detect_network(address)

    if network == "solana":
        importer = SolanaImporter()
        df = importer.fetch(address)
    else:
        importer = EVMImporter(chain=chain, api_key=etherscan_api_key)
        df = importer.fetch(address)

    if df.empty:
        return df

    # Гарантируем нужные колонки для normalizer
    for col in ["from_wallet", "to_wallet", "network", "fee_asset", "external_id", "price", "total_value"]:
        if col not in df.columns:
            df[col] = ""

    return df