from __future__ import annotations

from typing import Any, Optional

from app.integrations.defi_recognizer import DeFiMetadata
from app.integrations.plugins.plugin_base import DeFiPlugin


class EthenaPlugin(DeFiPlugin):
    name = "Ethena"
    version = "1.0.0"
    supported_chains = ["ethereum"]
    supported_events = ["USDE_MINT", "USDE_REDEEM", "SUSDE_STAKE", "SUSDE_UNSTAKE"]

    def __init__(self):
        self.addresses = {
            "ethereum": {
                "0x4c9edd5852cd905f086c759e8383e09bff1e68b3": "USDe Token",
                "0x9d39a5de30e57443bff2a8307a4256c8797a3497": "sUSDe Staking",
            }
        }

    def detect(self, row: dict[str, Any], next_rows: list[dict[str, Any]]) -> Optional[DeFiMetadata]:
        asset = str(row.get("asset", "")).upper()
        row_type = str(row.get("type", "")).upper()
        to_address = str(row.get("to_address", "")).lower()
        from_address = str(row.get("from_address", "")).lower()

        # sUSDe Staking detection
        susde_contract = "0x9d39a5de30e57443bff2a8307a4256c8797a3497"
        
        if asset == "USDE" and row_type == "TRANSFER" and to_address == susde_contract:
            # We look for a RECEIVE of sUSDe shortly after
            for next_row in next_rows[:5]:
                if str(next_row.get("asset", "")).upper() == "SUSDE" and str(next_row.get("type", "")).upper() == "RECEIVE":
                    return DeFiMetadata(
                        protocol="Ethena",
                        event_type="SUSDE_STAKE",
                        description="Stake USDe for sUSDe",
                        related_tx_indices=[int(next_row.get("csv_index", 0))],
                        involved_assets=["USDE", "SUSDE"]
                    )
            
            # Found transfer to contract, but no explicit receive matched yet
            return DeFiMetadata(
                protocol="Ethena",
                event_type="SUSDE_STAKE",
                description="Stake USDe (Transfer to Contract)",
                involved_assets=["USDE"]
            )

        return None

    def get_known_addresses(self) -> dict[str, dict[str, str]]:
        return self.addresses

    def classify_for_tax(self, event_type: str) -> str:
        mapping = {
            "SUSDE_STAKE": "SWAP",        # Usually a taxable swap of USDe -> sUSDe
            "SUSDE_UNSTAKE": "SWAP",      # Swap back
            "USDE_MINT": "MINT",          # Minting
            "USDE_REDEEM": "TRADE",       # Redeeming
        }
        return mapping.get(event_type, "UNKNOWN")
