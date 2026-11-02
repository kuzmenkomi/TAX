from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    file_path: str
    config_path: str | None = None


class AnalysisRunOut(BaseModel):
    id: int
    status: str
    created_at: str
    summary: Optional[dict[str, Any]] = None

    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    status: str
    filename: str
    rows_processed: int
    matches_found: int
    dedup: dict[str, Any]
    pnl: dict[str, Any]
    issues: list[Any]
    analysis_run_id: Optional[int] = None
    quote_currency: str
    use_ptax: bool
    income_events: dict[str, Any] = {}
    loss_harvesting: dict[str, Any] = {}
    monthly_sales_brl: dict[str, Any] = {}
    isencao_threshold_brl: float = 35000.0
    darf: Optional[dict[str, Any]] = None
    offshore_onshore: dict[str, Any] = {}
    tax_savings_opportunities: list[Any] = []
    p2p_self_custody_count: int = 0
    # Audit Trail and UX
    lot_matches: list[dict[str, Any]] = []
    transfer_matches: list[dict[str, Any]] = []
    # Deduplication stats
    duplicate: bool = False          # True if this exact file was already imported
    tx_imported: int = 0             # rows actually saved to DB
    tx_skipped: int = 0              # rows skipped as duplicates


class MultiAnalysisResultResponse(AnalysisResultResponse):
    filename: str | list[str]
