"""
Audit Trail with Blockchain Proof Links

Creates an immutable record of all transactions with blockchain explorer links
for verification. Enables tax inspectors to independently verify claims.

Features:
- Blockchain transaction hash tracking
- Explorer link generation (Etherscan, Solscan, etc.)
- Audit archive creation with timestamps
- Export for tax authorities
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json
import hashlib

import pandas as pd


@dataclass
class BlockchainProof:
    """Proof of a transaction on blockchain."""
    
    tx_hash: str
    network: str  # "ethereum", "solana", "polygon", etc.
    block_number: Optional[int] = None
    timestamp: Optional[datetime] = None
    
    @property
    def explorer_url(self) -> str:
        """Generate blockchain explorer URL for this transaction."""
        explorers = {
            "ethereum": "https://etherscan.io/tx/",
            "ethereum-sepolia": "https://sepolia.etherscan.io/tx/",
            "polygon": "https://polygonscan.com/tx/",
            "arbitrum": "https://arbiscan.io/tx/",
            "optimism": "https://optimistic.etherscan.io/tx/",
            "solana": "https://solscan.io/tx/",
            "solana-devnet": "https://solscan.io/tx/?cluster=devnet",
            "avalanche": "https://snowtrace.io/tx/",
            "bsc": "https://bscscan.com/tx/",
        }
        
        base_url = explorers.get(self.network, "")
        if not base_url:
            return ""
        
        return f"{base_url}{self.tx_hash}"


@dataclass
class AuditEntry:
    """Single entry in the audit trail."""
    
    # Transaction identification
    tx_id: str
    timestamp: datetime
    
    # Transaction details
    tx_type: str  # BUY, SELL, TRANSFER, STAKING, etc.
    asset: str
    amount: float
    price: float
    
    # User info
    user_id: str
    wallet_address: Optional[str] = None
    
    # Blockchain proof
    blockchain_proof: Optional[BlockchainProof] = None
    
    # Data integrity
    data_hash: str = field(default="")
    previous_hash: str = field(default="")
    
    def compute_hash(self) -> str:
        """Compute SHA256 hash of this entry (for blockchain-style chain)."""
        entry_str = (
            f"{self.tx_id}|{self.timestamp}|{self.tx_type}|"
            f"{self.asset}|{self.amount}|{self.price}|{self.user_id}|"
            f"{self.previous_hash}"
        )
        return hashlib.sha256(entry_str.encode()).hexdigest()
    
    @property
    def is_verified(self) -> bool:
        """True if blockchain proof exists."""
        return self.blockchain_proof is not None and self.blockchain_proof.tx_hash
    
    def to_dict(self) -> dict:
        """Convert to dictionary for export."""
        result = {
            "tx_id": self.tx_id,
            "timestamp": self.timestamp.isoformat(),
            "type": self.tx_type,
            "asset": self.asset,
            "amount": self.amount,
            "price": self.price,
            "user_id": self.user_id,
            "wallet_address": self.wallet_address,
            "is_verified": self.is_verified,
        }
        
        if self.blockchain_proof:
            result["blockchain_proof"] = {
                "tx_hash": self.blockchain_proof.tx_hash,
                "network": self.blockchain_proof.network,
                "block_number": self.blockchain_proof.block_number,
                "explorer_url": self.blockchain_proof.explorer_url,
            }
        
        result["data_hash"] = self.data_hash
        
        return result


class AuditTrail:
    """Manages audit trail with blockchain proofs."""
    
    def __init__(self):
        """Initialize empty audit trail."""
        self.entries: list[AuditEntry] = []
        self.chain_hash = ""  # Hash of previous entry
    
    def add_entry(
        self,
        tx_id: str,
        timestamp: datetime,
        tx_type: str,
        asset: str,
        amount: float,
        price: float,
        user_id: str,
        wallet_address: Optional[str] = None,
        blockchain_proof: Optional[BlockchainProof] = None,
    ) -> AuditEntry:
        """Add a new entry to the audit trail.
        
        Entries are linked via hash for integrity verification.
        """
        entry = AuditEntry(
            tx_id=tx_id,
            timestamp=timestamp,
            tx_type=tx_type,
            asset=asset,
            amount=amount,
            price=price,
            user_id=user_id,
            wallet_address=wallet_address,
            blockchain_proof=blockchain_proof,
            previous_hash=self.chain_hash,
        )
        
        # Compute entry hash and update chain
        entry.data_hash = entry.compute_hash()
        self.chain_hash = entry.data_hash
        
        self.entries.append(entry)
        return entry
    
    def verify_integrity(self) -> bool:
        """Verify that audit trail has not been tampered with.
        
        Returns:
            True if all entries form a valid chain
        """
        chain_hash = ""
        
        for entry in self.entries:
            expected_hash = entry.compute_hash()
            if expected_hash != entry.data_hash:
                return False
            
            chain_hash = entry.data_hash
        
        return chain_hash == self.chain_hash
    
    def verification_statistics(self) -> dict:
        """Get statistics about blockchain verification coverage."""
        total = len(self.entries)
        verified = sum(1 for e in self.entries if e.is_verified)
        
        by_network = {}
        for entry in self.entries:
            if entry.blockchain_proof:
                network = entry.blockchain_proof.network
                by_network[network] = by_network.get(network, 0) + 1
        
        return {
            "total_entries": total,
            "verified_entries": verified,
            "verification_rate": verified / total if total > 0 else 0,
            "networks": by_network,
            "chain_integrity": self.verify_integrity(),
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert audit trail to DataFrame."""
        data = [entry.to_dict() for entry in self.entries]
        return pd.DataFrame(data)


class AuditArchive:
    """Creates exportable audit archive for tax authorities."""
    
    @staticmethod
    def create_csv_export(audit_trail: AuditTrail, filename: str) -> str:
        """Export audit trail to CSV format."""
        df = audit_trail.to_dataframe()
        
        # Reorder columns for tax authority clarity
        columns = [
            "timestamp",
            "tx_id",
            "type",
            "asset",
            "amount",
            "price",
            "wallet_address",
            "is_verified",
        ]
        
        # Add blockchain columns if any proof exists
        if any(audit_trail.entries):
            if audit_trail.entries[0].blockchain_proof:
                columns.extend([
                    "blockchain_proof.tx_hash",
                    "blockchain_proof.network",
                    "blockchain_proof.explorer_url",
                ])
        
        available_cols = [c for c in columns if c in df.columns or "blockchain_proof" in c]
        
        if "blockchain_proof" in df.columns:
            # Flatten blockchain proof
            df["blockchain_proof.tx_hash"] = df["blockchain_proof"].apply(
                lambda x: x.get("tx_hash") if isinstance(x, dict) else ""
            )
            df["blockchain_proof.network"] = df["blockchain_proof"].apply(
                lambda x: x.get("network") if isinstance(x, dict) else ""
            )
            df["blockchain_proof.explorer_url"] = df["blockchain_proof"].apply(
                lambda x: x.get("explorer_url") if isinstance(x, dict) else ""
            )
            df = df.drop(columns=["blockchain_proof"])
        
        return df.to_csv(index=False)
    
    @staticmethod
    def create_json_export(audit_trail: AuditTrail) -> str:
        """Export audit trail to JSON with explorer links."""
        archive = {
            "export_timestamp": datetime.now().isoformat(),
            "audit_version": "1.0",
            "statistics": audit_trail.verification_statistics(),
            "integrity_verified": audit_trail.verify_integrity(),
            "entries": [entry.to_dict() for entry in audit_trail.entries],
            "chain_hash": audit_trail.chain_hash,
        }
        
        return json.dumps(archive, indent=2)
    
    @staticmethod
    def create_html_export(audit_trail: AuditTrail, filename: str) -> str:
        """Export audit trail to printable HTML report.
        
        Includes clickable blockchain explorer links for verification.
        """
        stats = audit_trail.verification_statistics()
        
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<title>Audit Trail Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 20px; }",
            "h1 { color: #333; }",
            "table { border-collapse: collapse; width: 100%; margin-top: 20px; }",
            "th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }",
            "th { background-color: #4CAF50; color: white; }",
            "tr:nth-child(even) { background-color: #f2f2f2; }",
            "a { color: #2196F3; text-decoration: none; }",
            "a:hover { text-decoration: underline; }",
            ".verified { color: green; font-weight: bold; }",
            ".unverified { color: red; }",
            ".stats { background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>Audit Trail Report</h1>",
            f"<p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>",
            
            # Statistics section
            "<div class='stats'>",
            f"<h2>Statistics</h2>",
            f"<p><strong>Total Entries:</strong> {stats['total_entries']}</p>",
            f"<p><strong>Verified Entries:</strong> {stats['verified_entries']} ({stats['verification_rate']*100:.1f}%)</p>",
            f"<p><strong>Chain Integrity:</strong> <span class=\"{'verified' if stats['chain_integrity'] else 'unverified'}\">",
            f"{'✓ Valid' if stats['chain_integrity'] else '✗ Invalid'}</span></p>",
        ]
        
        if stats["networks"]:
            html.append("<p><strong>Networks:</strong> " + ", ".join(stats["networks"].keys()) + "</p>")
        
        html.extend([
            "</div>",
            
            # Transactions table
            "<h2>Transactions</h2>",
            "<table>",
            "<tr>",
            "<th>Date</th>",
            "<th>Type</th>",
            "<th>Asset</th>",
            "<th>Amount</th>",
            "<th>Price</th>",
            "<th>Verified</th>",
            "<th>Blockchain Link</th>",
            "</tr>",
        ])
        
        for entry in audit_trail.entries:
            verified_class = "verified" if entry.is_verified else "unverified"
            verified_text = "✓ Yes" if entry.is_verified else "✗ No"
            
            blockchain_link = ""
            if entry.blockchain_proof:
                url = entry.blockchain_proof.explorer_url
                tx_hash = entry.blockchain_proof.tx_hash[:10] + "..."
                blockchain_link = f"<a href='{url}' target='_blank'>{tx_hash}</a>"
            
            html.extend([
                "<tr>",
                f"<td>{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</td>",
                f"<td>{entry.tx_type}</td>",
                f"<td>{entry.asset}</td>",
                f"<td>{entry.amount:.8f}</td>",
                f"<td>${entry.price:.2f}</td>",
                f"<td class='{verified_class}'>{verified_text}</td>",
                f"<td>{blockchain_link}</td>",
                "</tr>",
            ])
        
        html.extend([
            "</table>",
            "</body>",
            "</html>",
        ])
        
        return "\n".join(html)


# ==================== API INTEGRATION ====================
"""
Add to your FastAPI app:

from app.tax.audit_trail import AuditTrail, AuditArchive, BlockchainProof
from datetime import datetime
from decimal import Decimal

@app.post("/audit/export/csv")
def export_audit_csv(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Export audit trail with blockchain proofs as CSV.'''
    
    # Get analysis run
    run = db.query(AnalysisRun).filter(
        AnalysisRun.id == run_id,
        AnalysisRun.user_id == current_user.id
    ).first()
    if not run:
        raise HTTPException(status_code=404)
    
    # Build audit trail from normalized transactions
    import pandas as pd
    
    df = pd.read_csv(run.normalized_csv_path)
    audit = AuditTrail()
    
    for idx, tx in df.iterrows():
        blockchain_proof = None
        if "tx_hash" in tx and pd.notna(tx["tx_hash"]):
            blockchain_proof = BlockchainProof(
                tx_hash=tx["tx_hash"],
                network=tx.get("network", "ethereum"),
                block_number=int(tx.get("block_number", 0)) if "block_number" in tx else None
            )
        
        audit.add_entry(
            tx_id=str(idx),
            timestamp=pd.Timestamp(tx["timestamp"]),
            tx_type=tx["type"],
            asset=tx["asset"],
            amount=float(tx["amount"]),
            price=float(tx.get("price", 0)),
            user_id=str(current_user.id),
            wallet_address=tx.get("wallet_address"),
            blockchain_proof=blockchain_proof
        )
    
    # Export to CSV
    csv_content = AuditArchive.create_csv_export(audit, "audit_trail.csv")
    
    return {
        "filename": "audit_trail.csv",
        "content": csv_content,
        "statistics": audit.verification_statistics()
    }


@app.post("/audit/export/json")
def export_audit_json(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Export audit trail with blockchain proofs as JSON (complete archive).'''
    
    # [Same audit trail building as above]
    
    json_content = AuditArchive.create_json_export(audit)
    
    return {
        "filename": "audit_trail.json",
        "content": json.loads(json_content),
        "note": "Complete archive with blockchain explorer links for verification"
    }


@app.post("/audit/export/html")
def export_audit_html(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Export audit trail as printable HTML report with clickable blockchain links.'''
    
    # [Same audit trail building as above]
    
    html_content = AuditArchive.create_html_export(audit, "audit_trail.html")
    
    return {
        "filename": "audit_trail.html",
        "content": html_content,
        "note": "Printable report for tax inspectors with clickable blockchain verification links"
    }


@app.get("/audit/verify/{run_id}")
def verify_audit_trail(
    run_id: int,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Verify integrity of audit trail (blockchain-style chain validation).'''
    
    # [Same audit trail building as above]
    
    stats = audit.verification_statistics()
    
    return {
        "integrity_verified": audit.verify_integrity(),
        "total_entries": stats["total_entries"],
        "verified_entries": stats["verified_entries"],
        "verification_rate": f"{stats['verification_rate']*100:.1f}%",
        "status": "VALID" if audit.verify_integrity() else "INVALID"
    }
"""
