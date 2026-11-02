from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ExchangeConnectRequest(BaseModel):
    exchange_name: str
    api_key: str
    api_secret: str
    passphrase: Optional[str] = None
    label: Optional[str] = None


class ExchangeRegisterRequest(BaseModel):
    provider: str
    label: Optional[str] = None


class ExchangeConnectionResponse(BaseModel):
    """Никогда не включает api_key / api_secret — только метаданные."""
    id: int
    exchange_name: str
    label: Optional[str]
    status: str
    last_synced: Optional[datetime]
    last_sync_at: Optional[datetime] = None   # alias for frontend compatibility
    transaction_count: int = 0
    balance: float = 0.0

    model_config = {"from_attributes": True}


class ExchangeListItem(BaseModel):
    id: str
    name: str
    tier: Optional[int] = None
    logo_url: Optional[str] = None
