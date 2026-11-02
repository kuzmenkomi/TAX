from __future__ import annotations

from typing import Final, Literal

TransactionCategory = Literal["TRADE", "TRANSFER", "INCOME", "OTHER"]


TRADE_TYPES: Final[set[str]] = {
    "BUY",
    "SELL",
    "SWAP",
    "TRADE",
    "LIQUIDATION",
    "FUTURES_PNL",
}

TRANSFER_TYPES: Final[set[str]] = {
    "TRANSFER",
    "RECEIVE",
    "BRIDGE",
    "TOKEN_TRANSFER",
    "NFT_TRANSFER",
    "APPROVE",
    "WRAP",
    "UNWRAP",
    "DEPOSIT",
    "WITHDRAWAL",
    "LP_ADD",
    "LP_REMOVE",
    "DEFI_LP_ADD",
    "DEFI_LP_REMOVE",
    "MINT",
    "NFT_MINT",
    "BURN",
}

INCOME_TYPES: Final[set[str]] = {
    "INCOME",
    "AIRDROP",
    "REWARD",
    "INTEREST",
    "STAKING",
    "STAKING_REWARD",
    "FARMING_REWARD",
    "LENDING",
    "LENDING_INTEREST",
    "MINING",
    "MINING_REWARD",
    "FORK",
    "CLAIM",
}

CUSTOM_TAG_CATEGORIES: Final[dict[str, TransactionCategory]] = {
    "gift": "INCOME",
    "donation": "INCOME",
    "payment": "INCOME",
    "salary": "INCOME",
    "fork": "INCOME",
    "mining": "INCOME",
    "personal": "TRANSFER",
    "lost": "TRANSFER",
    "stolen": "TRANSFER",
    "ignore": "OTHER",
}

INCOME_HINTS: Final[tuple[str, ...]] = (
    "REWARD",
    "INTEREST",
    "INCOME",
    "AIRDROP",
    "MINING",
    "STAK",
    "FARM",
    "FORK",
    "CLAIM",
)

TRADE_HINTS: Final[tuple[str, ...]] = (
    "BUY",
    "SELL",
    "SWAP",
    "TRADE",
    "LIQUIDATION",
    "FUTURES",
    "PERP",
)

TRANSFER_HINTS: Final[tuple[str, ...]] = (
    "TRANSFER",
    "RECEIVE",
    "DEPOSIT",
    "WITHDRAW",
    "BRIDGE",
    "APPROVE",
    "WRAP",
    "UNWRAP",
    "LP_",
    "MINT",
    "BURN",
)


def normalize_transaction_type(tx_type: str | None) -> str:
    return str(tx_type or "").strip().upper()


def classify_transaction_category(
    tx_type: str | None,
    *,
    custom_tag: str | None = None,
    tax_event_type: str | None = None,
) -> TransactionCategory:
    tag = str(custom_tag or "").strip().lower()
    if tag in CUSTOM_TAG_CATEGORIES:
        return CUSTOM_TAG_CATEGORIES[tag]

    tax_event = str(tax_event_type or "").strip().lower()
    if tax_event == "income":
        return "INCOME"
    if tax_event in {"capital_gain", "capital_loss"}:
        return "TRADE"
    if tax_event in {"non_taxable", "expense"}:
        return "TRANSFER"

    normalized = normalize_transaction_type(tx_type)

    if normalized in INCOME_TYPES:
        return "INCOME"
    if normalized in TRADE_TYPES:
        return "TRADE"
    if normalized in TRANSFER_TYPES:
        return "TRANSFER"

    if any(hint in normalized for hint in INCOME_HINTS):
        return "INCOME"
    if any(hint in normalized for hint in TRADE_HINTS):
        return "TRADE"
    if any(hint in normalized for hint in TRANSFER_HINTS):
        return "TRANSFER"

    return "OTHER"
