"""DeFi summaries preserve event classes and signal ambiguous transactions."""
import pandas as pd

from app.pipeline import defi_pipeline as defi


def test_empty_defi_pipeline_returns_stable_schema():
    frame = defi.enrich_transactions_with_defi(pd.DataFrame())
    assert "defi_classification_confidence" in frame.columns
    assert defi.get_defi_summary_statistics(frame)["total_defi_transactions"] == 0
    assert defi.generate_defi_audit_report(frame)["total_transactions"] == 0
    assert defi.get_defi_events_by_protocol(frame, "aave").empty
    assert defi.get_tax_classified_transactions(frame, "income").empty


def test_defi_summary_filters_protocols_and_aggregates_rewards():
    frame = pd.DataFrame([
        {"defi_protocol": "aave", "defi_event_type": "defi_staking_reward", "tax_event_type": "income", "amount": 20,
         "defi_yield_earned_usd": 20, "fee": 1, "calldata": None},
        {"defi_protocol": "uniswap", "defi_event_type": "defi_lp_add", "tax_event_type": "capital_gain", "amount": 1000,
         "defi_yield_earned_usd": 0, "fee": 1, "calldata": None},
        {"defi_protocol": "uniswap", "defi_event_type": "defi_lp_remove", "tax_event_type": "capital_gain", "amount": 800,
         "defi_yield_earned_usd": 0, "fee": 1, "calldata": None},
        {"defi_protocol": None, "defi_event_type": None, "tax_event_type": None, "amount": 10,
         "defi_yield_earned_usd": 0, "fee": 0, "calldata": None},
    ])
    scored = defi._score_classification_confidence(frame)
    assert scored.iloc[0]["defi_classification_confidence"] == 1
    assert scored.iloc[3]["defi_classification_confidence"] == 0
    summary = defi.get_defi_summary_statistics(scored)
    assert summary["total_defi_transactions"] == 3
    assert summary["total_yield_earned_usd"] == 20
    assert summary["lp_positions_opened"] == summary["lp_positions_closed"] == 1
    assert len(defi.get_defi_events_by_protocol(scored, "aave")) == 1
    assert len(defi.get_defi_events_by_type(scored, "defi_lp_remove")) == 1
    assert len(defi.get_tax_classified_transactions(scored, "income")) == 1
    report = defi.generate_defi_audit_report(scored)
    assert report["lp_metrics"]["total_lp_value_added"] == 1000
    assert report["farming_metrics"]["total_rewards_earned_usd"] == 20
    assert report["confidence_metrics"]["high_confidence_percentage"] == 100
