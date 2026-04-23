from __future__ import annotations

from typing import Any

import pandas as pd
import requests


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


def _mk_token_transfer_row(
    *,
    ts_seconds: int,
    asset: str,
    amount: float,
    from_addr: str,
    to_addr: str,
    tx_hash: str,
    network: str,
    contract_address: str | None = None,
    log_index: str | None = None,
) -> dict[str, Any]:
    identifier = f"{tx_hash}:{log_index or '0'}"
    return _mk_transfer_row(
        ts_seconds=ts_seconds,
        asset=asset,
        amount=amount,
        from_addr=from_addr,
        to_addr=to_addr,
        tx_hash=identifier,
        network=network,
        extra={
            "type": "TOKEN_TRANSFER",
            "contract_address": contract_address or "",
            "log_index": log_index or "0",
        },
    )


def _mk_nft_transfer_row(
    *,
    ts_seconds: int,
    asset: str,
    from_addr: str,
    to_addr: str,
    tx_hash: str,
    network: str,
    token_id: str,
    contract_address: str | None = None,
    log_index: str | None = None,
) -> dict[str, Any]:
    identifier = f"{tx_hash}:{token_id}:{log_index or '0'}"
    row = _mk_transfer_row(
        ts_seconds=ts_seconds,
        asset=asset,
        amount=1.0,
        from_addr=from_addr,
        to_addr=to_addr,
        tx_hash=identifier,
        network=network,
        extra={
            "type": "NFT_TRANSFER",
            "contract_address": contract_address or "",
            "token_id": token_id,
            "log_index": log_index or "0",
        },
    )
    return row


def _fetch_etherscan_api(base: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(base, params=params, timeout=15, headers={"accept": "application/json"})
    response.raise_for_status()
    return response.json()


def _parse_erc20_transfers(
    result: list[dict[str, Any]],
    address: str,
    network: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    address_norm = address.lower()
    for tx in result or []:
        try:
            from_addr = str(tx.get("from", "")).lower()
            to_addr = str(tx.get("to", "")).lower()
            if from_addr != address_norm and to_addr != address_norm:
                continue
            value = int(tx.get("value", 0))
            decimals = int(tx.get("tokenDecimal") or 0)
            amount = float(value) / (10**decimals) if decimals else float(value or 0)
            asset = str(tx.get("tokenSymbol") or tx.get("tokenName") or "UNKNOWN").upper() or "UNKNOWN"
            ts = int(tx.get("timeStamp", 0))
            tx_hash = str(tx.get("hash", ""))
            log_index = str(tx.get("logIndex") or tx.get("transactionIndex") or "0")
            contract_address = str(tx.get("contractAddress") or "").lower()
            rows.append(
                _mk_token_transfer_row(
                    ts_seconds=ts,
                    asset=asset,
                    amount=amount,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    tx_hash=tx_hash,
                    network=network,
                    contract_address=contract_address,
                    log_index=log_index,
                )
            )
        except Exception:
            continue
    return rows


def _parse_nft_transfers(
    result: list[dict[str, Any]],
    address: str,
    network: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    address_norm = address.lower()
    for tx in result or []:
        try:
            from_addr = str(tx.get("from", "")).lower()
            to_addr = str(tx.get("to", "")).lower()
            if from_addr != address_norm and to_addr != address_norm:
                continue
            ts = int(tx.get("timeStamp", 0))
            asset = str(tx.get("tokenSymbol") or tx.get("tokenName") or "NFT").upper() or "NFT"
            tx_hash = str(tx.get("hash", ""))
            token_id = str(tx.get("tokenID") or tx.get("tokenId") or "")
            log_index = str(tx.get("logIndex") or tx.get("transactionIndex") or "0")
            contract_address = str(tx.get("contractAddress") or "").lower()
            rows.append(
                _mk_nft_transfer_row(
                    ts_seconds=ts,
                    asset=asset,
                    from_addr=from_addr,
                    to_addr=to_addr,
                    tx_hash=tx_hash,
                    network=network,
                    token_id=token_id,
                    contract_address=contract_address,
                    log_index=log_index,
                )
            )
        except Exception:
            continue
    return rows


def fetch_evm_transfers(address: str, chain: str, api_key: str | None = None) -> pd.DataFrame:
    chain_norm = chain.lower().strip()
    if chain_norm == "polygon":
        base = "https://api.polygonscan.com/api"
        native_asset = "MATIC"
    else:
        base = "https://api.etherscan.io/api"
        native_asset = "ETH"

    rows: list[dict[str, Any]] = []
    address_norm = address.lower()
    common_params = {
        "module": "account",
        "address": address_norm,
        "startblock": 0,
        "endblock": 99999999,
        "sort": "asc",
    }
    if api_key:
        common_params["apikey"] = api_key

    try:
        tx_list = _fetch_etherscan_api(base, {**common_params, "action": "txlist"})
        for tx in tx_list.get("result", []) or []:
            try:
                ts = int(tx.get("timeStamp", 0))
                value_wei = int(tx.get("value", 0))
                value = value_wei / (10**18)
                from_addr = str(tx.get("from", "")).lower()
                to_addr = str(tx.get("to", "")).lower()
                tx_hash = str(tx.get("hash", ""))
                if from_addr == address_norm or to_addr == address_norm:
                    rows.append(
                        _mk_transfer_row(
                            ts_seconds=ts,
                            asset=native_asset,
                            amount=value,
                            from_addr=from_addr,
                            to_addr=to_addr,
                            tx_hash=tx_hash,
                            network=chain_norm,
                        )
                    )
            except Exception:
                continue
    except Exception:
        pass

    try:
        token_list = _fetch_etherscan_api(base, {**common_params, "action": "tokentx"})
        rows.extend(_parse_erc20_transfers(token_list.get("result", []), address_norm, chain_norm))
    except Exception:
        pass

    try:
        nft_list = _fetch_etherscan_api(base, {**common_params, "action": "tokennfttx"})
        rows.extend(_parse_nft_transfers(nft_list.get("result", []), address_norm, chain_norm))
    except Exception:
        pass

    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "asset",
                "type",
                "amount",
                "fee",
                "fee_asset",
                "from_wallet",
                "to_wallet",
                "network",
                "price",
                "total_value",
                "external_id",
            ]
        )

    out = pd.DataFrame(rows)
    return out.sort_values("timestamp").reset_index(drop=True)


def fetch_solana_transfers(address: str) -> pd.DataFrame:
    address_norm = address.lower()
    rows: list[dict[str, Any]] = []

    try:
        url = f"https://public-api.solscan.io/account/solTransfers?account={address_norm}&limit=50&offset=0"
        r = requests.get(url, timeout=15, headers={"accept": "application/json"})
        r.raise_for_status()
        payload = r.json()
        for tx in payload or []:
            try:
                ts = int(tx.get("blockTime", 0))
                lamports = int(tx.get("lamport", 0))
                amount = abs(lamports) / (10**9)
                from_addr = str(tx.get("src", "")).lower()
                to_addr = str(tx.get("dst", "")).lower()
                tx_hash = str(tx.get("txHash", ""))
                rows.append(
                    _mk_transfer_row(
                        ts_seconds=ts,
                        asset="SOL",
                        amount=amount,
                        from_addr=from_addr,
                        to_addr=to_addr,
                        tx_hash=tx_hash,
                        network="solana",
                    )
                )
            except Exception:
                continue
    except Exception:
        pass

    try:
        url = f"https://public-api.solscan.io/account/splTransfers?account={address_norm}&limit=50&offset=0"
        r = requests.get(url, timeout=15, headers={"accept": "application/json"})
        r.raise_for_status()
        payload = r.json()
        for tx in payload or []:
            try:
                ts = int(tx.get("blocktime", 0) or tx.get("blockTime", 0) or 0)
                amount = float(tx.get("amount", 0) or 0)
                decimals = int(tx.get("decimals", 0) or 0)
                if decimals:
                    amount = amount / (10**decimals)
                from_addr = str(tx.get("owner", "")).lower()
                to_addr = str(tx.get("toOwner", "")).lower()
                token_symbol = str(tx.get("tokenSymbol") or tx.get("tokenName") or "SPL").upper()
                tx_hash = str(tx.get("txHash") or tx.get("transactionHash") or "")
                if from_addr == address_norm or to_addr == address_norm:
                    rows.append(
                        _mk_token_transfer_row(
                            ts_seconds=ts,
                            asset=token_symbol,
                            amount=amount,
                            from_addr=from_addr,
                            to_addr=to_addr,
                            tx_hash=tx_hash,
                            network="solana",
                            contract_address=str(tx.get("tokenAddress") or "").lower(),
                            log_index=str(tx.get("logIndex") or "0"),
                        )
                    )
            except Exception:
                continue
    except Exception:
        pass

    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "asset",
                "type",
                "amount",
                "fee",
                "fee_asset",
                "from_wallet",
                "to_wallet",
                "network",
                "price",
                "total_value",
                "external_id",
            ]
        )

    out = pd.DataFrame(rows)
    return out.sort_values("timestamp").reset_index(drop=True)


def fetch_bitcoin_transfers(address: str) -> pd.DataFrame:
    # Use blockchain.com API for Bitcoin transactions
    url = f"https://blockchain.info/rawaddr/{address}?limit=50"
    rows: list[dict[str, Any]] = []
    try:
        r = requests.get(url, timeout=15, headers={"accept": "application/json"})
        r.raise_for_status()
        payload = r.json()
        for tx in payload.get("txs", []) or []:
            try:
                ts = int(tx.get("time", 0))
                tx_hash = str(tx.get("hash", ""))
                for inp in tx.get("inputs", []):
                    if inp.get("prev_out", {}).get("addr") == address:
                        amount = float(inp.get("prev_out", {}).get("value", 0)) / (10**8)  # Satoshi to BTC
                        from_addr = str(inp.get("prev_out", {}).get("addr", "")).lower()
                        to_addr = address.lower()
                        rows.append(
                            _mk_transfer_row(
                                ts_seconds=ts,
                                asset="BTC",
                                amount=amount,
                                from_addr=from_addr,
                                to_addr=to_addr,
                                tx_hash=tx_hash,
                                network="bitcoin",
                            )
                        )
                for out in tx.get("out", []):
                    if out.get("addr") == address:
                        amount = float(out.get("value", 0)) / (10**8)
                        from_addr = address.lower()
                        to_addr = str(out.get("addr", "")).lower()
                        rows.append(
                            _mk_transfer_row(
                                ts_seconds=ts,
                                asset="BTC",
                                amount=amount,
                                from_addr=from_addr,
                                to_addr=to_addr,
                                tx_hash=tx_hash,
                                network="bitcoin",
                            )
                        )
            except Exception:
                continue
    except Exception:
        pass

    if not rows:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "asset",
                "type",
                "amount",
                "fee",
                "fee_asset",
                "from_wallet",
                "to_wallet",
                "network",
                "price",
                "total_value",
                "external_id",
            ]
        )

    out = pd.DataFrame(rows)
    return out.sort_values("timestamp").reset_index(drop=True)

