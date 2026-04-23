from __future__ import annotations

from pydantic import BaseModel


class BrSyncIn(BaseModel):
    connection_type: str
    connection_id: int


class BrBinanceSyncIn(BaseModel):
    provider: str = "binance"
    api_key: str
    api_secret: str
    symbols: list[str] | None = None
    accounting_method: str = "FIFO"
    quote_currency: str = "BRL"
    country: str = "br"
    max_amount_diff: float = 0.01
    max_time_diff_seconds: int = 3600
    limit_per_symbol: int = 200
    use_ptax: bool = False


class BrWalletOnchainIn(BaseModel):
    chain: str
    address: str
    accounting_method: str = "AVCO"
    quote_currency: str = "BRL"
    country: str = "br"
    use_ptax: bool = True
    etherscan_api_key: str | None = None
    polygonscan_api_key: str | None = None


class SyncExchangeIn(BaseModel):
    provider: str
    api_key: str
    api_secret: str
    symbols: list[str] | None = None
    accounting_method: str = "FIFO"
    quote_currency: str = "BRL"
    country: str = "br"
    use_ptax: bool = False
    limit_per_symbol: int = 200


class SyncWalletIn(BaseModel):
    chain: str
    address: str
    accounting_method: str = "AVCO"
    quote_currency: str = "BRL"
    country: str = "br"
    use_ptax: bool = True
    etherscan_api_key: str | None = None
    polygonscan_api_key: str | None = None


# Sync Status Response Schemas
class SyncJobInfo(BaseModel):
    """Individual scheduled job info."""
    id: str
    name: str
    next_run_time: str | None


class SyncStatusResponse(BaseModel):
    """Response from /br/sync/status endpoint."""
    scheduler_running: bool
    jobs: list[SyncJobInfo]


class SyncEnqueueResponse(BaseModel):
    """Response from /br/sync/enqueue endpoint."""
    job_id: int
    status: str
