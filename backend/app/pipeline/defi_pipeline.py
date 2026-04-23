"""
DeFi Pipeline Integration - Integrates DeFi recognition into the main transaction processing flow.

This module:
1. Enriches blockchain transactions with DeFi protocol metadata
2. Classifies transactions for tax purposes
3. Calculates relevant metrics (yield, impermanent loss, etc.)
4. Provides aggregated DeFi statistics
"""

from __future__ import annotations

from typing import Any, Optional
import json

import pandas as pd

from app.integrations.defi_recognizer import (
    DeFiEventType,
    DeFiProtocol,
    classify_for_tax,
    recognize_defi_events,
    get_supported_protocols,
)
from app.integrations.contract_abi_parser import (
    decode_function_call,
    get_protocol_from_calldata,
    get_transaction_category,
    is_defi_interaction,
)


def enrich_transactions_with_defi(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point for DeFi enrichment.

    Takes normalized transaction DataFrame and adds DeFi metadata.

    Args:
        df: DataFrame with columns (timestamp, asset, type, amount, fee, from_wallet, to_wallet, external_id, price, etc.)

    Returns:
        Enhanced DataFrame with DeFi columns:
        - defi_protocol: str (protocol name or None)
        - defi_event_type: str (event type or None)
        - defi_tokens_in: dict (input tokens and amounts)
        - defi_tokens_out: dict (output tokens and amounts)
        - defi_yield_earned_usd: float (for staking/farming rewards)
        - tax_event_type: str (income, capital_gain, non_taxable, etc.)
        - defi_classification_confidence: float (0.0-1.0)
    """
    if df.empty:
        _add_defi_columns(df)
        return df

    # Step 1: Initial DeFi event recognition
    df = recognize_defi_events(df)

    # Step 2: Tax classification
    df = classify_for_tax(df)

    # Step 3: Confidence scoring
    df = _score_classification_confidence(df)

    # Step 4: Add calldata analysis if available
    if "calldata" in df.columns:
        df = _enrich_with_calldata_analysis(df)

    return df


def _add_defi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add empty DeFi columns to DataFrame."""
    if df.empty:
        df["defi_protocol"] = []
        df["defi_event_type"] = []
        df["defi_tokens_in"] = []
        df["defi_tokens_out"] = []
        df["defi_yield_earned_usd"] = []
        df["tax_event_type"] = []
        df["defi_classification_confidence"] = []
    return df


def _score_classification_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Score confidence of DeFi classification (0.0-1.0)."""
    df = df.copy()

    def _score_row(row) -> float:
        # If no DeFi found, confidence = 0
        if pd.isna(row.get("defi_protocol")) or row.get("defi_protocol") is None:
            return 0.0

        # High confidence if:
        # - Protocol identified (not generic)
        # - Matching token types
        # - Non-zero fee (indicates contract interaction)
        # - Timestamps within expected range

        confidence = 0.6  # Base score

        protocol = row.get("defi_protocol")

        # Bonus for specific protocol vs generic
        if protocol and protocol not in ["generic_swap", "generic_pool"]:
            confidence += 0.2

        # Bonus for fee indication
        if row.get("fee", 0) > 0:
            confidence += 0.15

        # Bonus for proper tax classification
        tax_type = row.get("tax_event_type")
        if tax_type in ["income", "capital_gain"]:
            confidence += 0.05

        return min(confidence, 1.0)

    df["defi_classification_confidence"] = df.apply(_score_row, axis=1)
    return df


def _enrich_with_calldata_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Enhance DeFi classification using transaction calldata if available."""
    df = df.copy()

    def _analyze_calldata(row) -> dict[str, Any]:
        calldata = row.get("calldata")
        if not calldata:
            return {}

        result = {}

        # Decode function call
        func_info = decode_function_call(calldata)
        if func_info:
            result["function"] = func_info.get("name")
            result["calldata_protocol"] = func_info.get("protocol")
            result["calldata_category"] = func_info.get("category")

        return result

    # Apply calldata analysis
    calldata_analysis = df.apply(_analyze_calldata, axis=1)

    # Update protocol if calldata provides better info
    for idx, row in df.iterrows():
        analysis = calldata_analysis.iloc[idx]
        if analysis.get("calldata_protocol") and not row.get("defi_protocol"):
            df.loc[idx, "defi_protocol"] = analysis.get("calldata_protocol")

    return df


def get_defi_summary_statistics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate summary statistics for DeFi activity in the portfolio.

    Returns:
        Dict with statistics like total yield, farming protocols used, etc.
    """
    if df.empty:
        return {
            "total_defi_transactions": 0,
            "protocols_used": [],
            "total_yield_earned_usd": 0.0,
            "total_impermanent_loss_usd": 0.0,
            "lp_positions_opened": 0,
            "lp_positions_closed": 0,
        }

    defi_df = df[df["defi_protocol"].notna()]

    # Count by protocol
    protocol_counts = defi_df["defi_protocol"].value_counts().to_dict()

    # Total yield from staking/farming
    yield_df = defi_df[defi_df["defi_event_type"].isin(
        ["defi_staking_reward", "defi_farming_reward", "defi_governance_claim"]
    )]
    total_yield = yield_df["defi_yield_earned_usd"].sum()

    # LP positions
    lp_added = len(defi_df[defi_df["defi_event_type"] == "defi_lp_add"])
    lp_removed = len(defi_df[defi_df["defi_event_type"] == "defi_lp_remove"])

    return {
        "total_defi_transactions": len(defi_df),
        "protocols_used": list(protocol_counts.keys()),
        "protocol_statistics": protocol_counts,
        "total_yield_earned_usd": float(total_yield),
        "lp_positions_opened": lp_added,
        "lp_positions_closed": lp_removed,
        "swaps_performed": len(defi_df[defi_df["defi_event_type"] == "defi_swap"]),
        "lending_deposits": len(defi_df[defi_df["defi_event_type"] == "defi_lending_deposit"]),
        "confidence_score": float(defi_df["defi_classification_confidence"].mean()),
    }


def get_defi_events_by_protocol(df: pd.DataFrame, protocol: str) -> pd.DataFrame:
    """Filter transactions by DeFi protocol."""
    if df.empty:
        return df

    return df[df["defi_protocol"] == protocol]


def get_defi_events_by_type(df: pd.DataFrame, event_type: str) -> pd.DataFrame:
    """Filter transactions by DeFi event type."""
    if df.empty:
        return df

    return df[df["defi_event_type"] == event_type]


def get_tax_classified_transactions(df: pd.DataFrame, tax_type: str) -> pd.DataFrame:
    """
    Get transactions classified for specific tax purpose.

    tax_type: 'income', 'capital_gain', 'capital_loss', 'expense', 'non_taxable'
    """
    if df.empty:
        return df

    return df[df["tax_event_type"] == tax_type]


def calculate_lp_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """
    Calculate metrics for LP positions.

    Returns:
        - Total value added to LPs
        - Total value removed from LPs
        - Average holding period
        - Estimated impermanent loss
    """
    lp_operations = df[df["defi_event_type"].isin(["defi_lp_add", "defi_lp_remove"])]

    if lp_operations.empty:
        return {
            "total_lp_value_added": 0.0,
            "total_lp_value_removed": 0.0,
            "average_position_duration_days": 0,
            "estimated_impermanent_loss_usd": 0.0,
        }

    lp_adds = lp_operations[lp_operations["defi_event_type"] == "defi_lp_add"]
    lp_removes = lp_operations[lp_operations["defi_event_type"] == "defi_lp_remove"]

    total_added = lp_adds["amount"].sum()
    total_removed = lp_removes["amount"].sum()

    # Rough estimate: if more removed than added, likely minimal IL
    il_estimate = max(0, total_added - total_removed) * 0.05  # Conservative 5% estimate

    return {
        "total_lp_value_added": float(total_added),
        "total_lp_value_removed": float(total_removed),
        "positions_opened": len(lp_adds),
        "positions_closed": len(lp_removes),
        "estimated_impermanent_loss_usd": float(il_estimate),
    }


def calculate_farming_metrics(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate yield farming statistics."""
    farming_ops = df[df["defi_event_type"].isin(
        ["defi_farming_deposit", "defi_farming_reward", "defi_staking_reward"]
    )]

    if farming_ops.empty:
        return {
            "total_staked_value_usd": 0.0,
            "total_rewards_earned_usd": 0.0,
            "farming_protocols": [],
            "average_apr": 0.0,
        }

    rewards = farming_ops[farming_ops["defi_event_type"].isin(
        ["defi_farming_reward", "defi_staking_reward"]
    )]
    total_rewards = rewards["defi_yield_earned_usd"].sum()

    protocols = farming_ops["defi_protocol"].unique().tolist()

    return {
        "total_staked_value_usd": float(farming_ops["amount"].sum()),
        "total_rewards_earned_usd": float(total_rewards),
        "farming_protocols": protocols,
        "number_of_reward_events": len(rewards),
    }


def generate_defi_audit_report(df: pd.DataFrame) -> dict[str, Any]:
    """
    Generate comprehensive DeFi audit report for tax purposes.

    Includes:
    - All protocols used
    - All event types
    - Tax implications
    - Potential issues (missing data, unclear events)
    """
    if df.empty:
        return {
            "summary": "No DeFi activity detected",
            "total_transactions": 0,
            "protocols_used": [],
            "events": {},
            "tax_statistics": {},
            "warnings": [],
        }

    defi_df = df[df["defi_protocol"].notna()]

    events_summary = defi_df["defi_event_type"].value_counts().to_dict()
    protocols_summary = defi_df["defi_protocol"].value_counts().to_dict()

    # Tax implications by event type
    tax_summary = defi_df["tax_event_type"].value_counts().to_dict()

    # Low confidence transactions (potential risks)
    low_confidence = defi_df[defi_df["defi_classification_confidence"] < 0.5]
    warnings = []

    if len(low_confidence) > 0:
        warnings.append(
            f"{len(low_confidence)} transactions with low confidence "
            f"(< 50%) - manual review recommended"
        )

    # Check for unclassified protocol interactions
    unclassified = df[
        (df["calldata"].notna()) &
        (df["defi_protocol"].isna()) &
        (df["defi_protocol"].apply(lambda x: is_defi_interaction(x) if isinstance(x, str) else False))
    ]

    if len(unclassified) > 0:
        warnings.append(
            f"{len(unclassified)} potential DeFi interactions detected "
            f"but not classified"
        )

    return {
        "summary": f"Analyzed {len(defi_df)} DeFi transactions",
        "total_transactions": len(defi_df),
        "total_transaction_value_usd": float(defi_df["amount"].sum()),
        "protocols_used": list(protocols_summary.keys()),
        "protocols_summary": protocols_summary,
        "events_summary": events_summary,
        "tax_statistics": tax_summary,
        "lp_metrics": calculate_lp_metrics(df),
        "farming_metrics": calculate_farming_metrics(df),
        "confidence_metrics": {
            "average_confidence": float(defi_df["defi_classification_confidence"].mean()),
            "high_confidence_percentage": float(
                (defi_df["defi_classification_confidence"] >= 0.8).sum() / len(defi_df)
            ) * 100,
        },
        "warnings": warnings,
    }
