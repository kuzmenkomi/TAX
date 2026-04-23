from __future__ import annotations

from typing import Any

import pandas as pd
import pytest

from app.integrations import explorer_fetch


class DummyResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._payload


def _fake_requests_get(url: str, params: dict[str, Any] | None = None, timeout: int = 0, headers: dict[str, Any] | None = None):
    if params is None:
        raise ValueError("missing params")
    action = params.get("action")
    if action == "txlist":
        return DummyResponse({
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "timeStamp": "1700000000",
                    "value": "1000000000000000000",
                    "from": "0xabc",
                    "to": "0xdef",
                    "hash": "0xethtx",
                }
            ],
        })
    if action == "tokentx":
        return DummyResponse({
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "timeStamp": "1700000001",
                    "value": "500000000000000000",
                    "tokenSymbol": "USDT",
                    "tokenDecimal": "6",
                    "from": "0xabc",
                    "to": "0xdef",
                    "hash": "0xertx",
                    "logIndex": "1",
                    "contractAddress": "0xcontract",
                }
            ],
        })
    if action == "tokennfttx":
        return DummyResponse({
            "status": "1",
            "message": "OK",
            "result": [
                {
                    "timeStamp": "1700000002",
                    "tokenSymbol": "COOL",
                    "tokenID": "1234",
                    "from": "0xabc",
                    "to": "0xdef",
                    "hash": "0xnfttx",
                    "logIndex": "2",
                    "contractAddress": "0xnftcontract",
                }
            ],
        })
    raise ValueError(f"unexpected action {action}")


def test_fetch_evm_transfers_includes_erc20_and_nft(monkeypatch):
    monkeypatch.setattr(explorer_fetch.requests, "get", _fake_requests_get)
    df = explorer_fetch.fetch_evm_transfers("0xabc", "ethereum", api_key="dummy")

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert set(df["type"].tolist()) == {"TRANSFER", "TOKEN_TRANSFER", "NFT_TRANSFER"}
    assert "contract_address" in df.columns
    assert "token_id" in df.columns
    assert df.loc[df["type"] == "NFT_TRANSFER", "asset"].iloc[0] == "COOL"


def test_fetch_solana_transfers_handles_spl_token(monkeypatch):
    expected_payload = [
        {
            "blocktime": 1700000003,
            "amount": 1000000,
            "decimals": 6,
            "owner": "0xabc",
            "toOwner": "0xdef",
            "tokenSymbol": "USDC",
            "txHash": "0xsoltx",
            "tokenAddress": "0xsplcontract",
            "logIndex": "0",
        }
    ]

    def fake_get(url: str, timeout: int = 0, headers: dict[str, Any] | None = None):
        if "splTransfers" in url:
            return DummyResponse(expected_payload)
        return DummyResponse([])

    monkeypatch.setattr(explorer_fetch.requests, "get", fake_get)
    df = explorer_fetch.fetch_solana_transfers("0xabc")

    assert len(df) == 1
    assert df.loc[0, "asset"] == "USDC"
    assert df.loc[0, "type"] == "TOKEN_TRANSFER"
    assert df.loc[0, "network"] == "solana"
