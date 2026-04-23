from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class DeFiProtocolInfo(BaseModel):
    name: str
    description: str
    chains: list[str]
    events: list[str]


class DefiClassifyRequest(BaseModel):
    transactions: list[dict[str, Any]]


class DefiClassifyResponse(BaseModel):
    total_transactions: int
    defi_transactions: int
    classified_transactions: list[dict[str, Any]]
    summary_statistics: dict[str, Any]
    audit_report: dict[str, Any]
