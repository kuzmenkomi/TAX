"""
DeFi Plugin Base class.

All DeFi protocol integrations must inherit from this class to be 
automatically discovered by the PluginRegistry.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.integrations.defi_recognizer import DeFiMetadata


class DeFiPlugin(ABC):
    """Abstract base class for all DeFi protocol plugins."""

    # Unique protocol identifier (e.g., "eigenlayer", "ethena")
    name: str = "base"
    
    # Plugin version
    version: str = "1.0.0"
    
    # Supported blockchains (e.g., ["ethereum", "arbitrum"])
    supported_chains: list[str] = []
    
    # Supported event types (e.g., ["RESTAKE", "CLAIM", "MINT"])
    supported_events: list[str] = []

    @abstractmethod
    def detect(self, row: dict[str, Any], next_rows: list[dict[str, Any]]) -> Optional[DeFiMetadata]:
        """
        Analyze a transaction row (and optionally subsequent rows for multi-step TXs)
        to detect if they belong to this protocol.

        Returns:
            DeFiMetadata if a match is found, None otherwise.
        """
        ...

    @abstractmethod
    def get_known_addresses(self) -> dict[str, dict[str, str]]:
        """
        Return a dictionary of known smart contract addresses for this protocol.
        Format: {"chain_name": {"address_lowercase": "Contract Name/Role"}}
        """
        ...

    @abstractmethod
    def classify_for_tax(self, event_type: str) -> str:
        """
        Map a protocol-specific event type to a standard tax classification.
        e.g., "RESTAKE" -> "INTERNAL_TRANSFER"
              "CLAIM_REWARDS" -> "INCOME"
        """
        ...
