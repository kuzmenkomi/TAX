from __future__ import annotations

from pydantic import BaseModel


class TaxScenarioRequest(BaseModel):
    price_targets: list[float] | None = None
    include_loss_harvest: bool = True


class IncomeOptimizationQuery(BaseModel):
    staking_income: float = 0
    airdrop_income: float = 0
    lending_income: float = 0


class AIQuestionRequest(BaseModel):
    question: str
    run_id: int


class RunIdRequest(BaseModel):
    run_id: int
