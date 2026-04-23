from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator
import re


class WalletConnectRequest(BaseModel):
    chain: str          # evm / solana / btc
    address: str = Field(..., max_length=100)
    label: Optional[str] = None

    @field_validator("address")
    @classmethod
    def validate_evm(cls, v: str, info) -> str:
        chain = info.data.get("chain", "").lower()
        if chain in ("ethereum", "polygon", "bsc", "arbitrum", "optimism", "base") or chain == "evm":
            if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
                raise ValueError("Invalid EVM address format")
        return v


class BlockchainImportRequest(BaseModel):
    chain: str
    address: str = Field(..., max_length=100)
    label: Optional[str] = None
    etherscan_api_key: Optional[str] = None
    polygonscan_api_key: Optional[str] = None

    @field_validator("address")
    @classmethod
    def validate_evm(cls, v: str, info) -> str:
        chain = info.data.get("chain", "").lower()
        if chain in ("ethereum", "polygon", "bsc", "arbitrum", "optimism", "base") or chain == "evm":
            if not re.match(r"^0x[a-fA-F0-9]{40}$", v):
                raise ValueError("Invalid EVM address format")
        return v


class WalletResponse(BaseModel):
    id: int
    chain: str
    address: str
    label: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}
