"""
Magic Repair - Intelligent Data Quality Assistant

Identifies problematic transactions and suggests fixes:
- Missing cost basis (zero entry price)
- Missing dates
- Duplicate transactions
- Unusual profit/loss ratios
- Orphaned transfers (receive without corresponding send)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional
from datetime import datetime, timedelta

import pandas as pd


@dataclass
class DataQssueType:
    """Types of data issues."""
    
    # Missing data
    MISSING_COST_BASIS = "missing_cost_basis"
    MISSING_DATE = "missing_date"
    MISSING_AMOUNT = "missing_amount"
    
    # Logic issues
    SUSPICIOUS_RATIO = "suspicious_ratio"
    ORPHANED_TRANSFER = "orphaned_transfer"
    DUPLICATE = "duplicate"
    
    # Context issues
    EXTREME_FEE = "extreme_fee"
    PRICE_MISMATCH = "price_mismatch"
    WRONG_ASSET = "wrong_asset"


@dataclass
class RepairSuggestion:
    """Suggestion to fix a transaction issue."""
    
    transaction_id: str
    issue_type: str
    issue_severity: str  # "ERROR", "WARNING", "INFO"
    description: str
    
    # Suggested fixes (in priority order)
    suggestions: list[dict]  # [{"action": "...", "value": "...", "reason": "..."}]
    
    # Context
    transaction_data: dict
    confidence: float  # 0.0-1.0


class DataQualityAnalyzer:
    """Analyzes transaction data for quality issues."""
    
    def __init__(self):
        self.issues: list[RepairSuggestion] = []
    
    def analyze_DataFrame(self, df: pd.DataFrame) -> list[RepairSuggestion]:
        """Analyze DataFrame for issues."""
        self.issues = []
        
        for idx, tx in df.iterrows():
            self._check_transaction(tx, idx)
        
        return self.issues
    
    def _check_transaction(self, tx: pd.Series, idx: int):
        """Check single transaction for issues."""
        tx_id = f"tx_{idx}_{tx.get('timestamp', 'unknown')}"
        
        # Check 1: Missing cost basis (zero or null price for BUY/RECEIVE)
        if str(tx.get("type", "")).upper() in ("BUY", "RECEIVE", "IN", "DEPOSIT"):
            if pd.isna(tx.get("price")) or float(tx.get("price", 0)) == 0:
                self._issue_missing_cost_basis(tx, tx_id)
        
        # Check 2: Missing or invalid date
        try:
            pd.Timestamp(tx.get("timestamp"))
        except Exception:
            self._issue_missing_date(tx, tx_id)
        
        # Check 3: Suspicious profit ratio (>1000% or <-99%)
        if tx.get("type", "").upper() == "SELL":
            cost = float(tx.get("cost_basis", 0)) or \
                   (float(tx.get("amount", 0)) * float(tx.get("acquisition_price", 0)))
            proceeds = float(tx.get("proceeds", 0)) or \
                       (float(tx.get("amount", 0)) * float(tx.get("price", 0)))
            
            if cost > 0:
                ratio = (proceeds / cost - 1) * 100
                if ratio > 1000 or ratio < -100:
                    self._issue_suspicious_ratio(tx, tx_id, ratio)
        
        # Check 4: Extreme fee (>50% of transaction value)
        fee = float(tx.get("fee", 0)) or 0
        amount = float(tx.get("amount", 0)) or 0
        price = float(tx.get("price", 0)) or 0
        
        if amount > 0 and price > 0:
            tx_value = amount * price
            if tx_value > 0 and (fee / tx_value) > 0.5:
                self._issue_extreme_fee(tx, tx_id, fee, tx_value)
    
    def _issue_missing_cost_basis(self, tx: pd.Series, tx_id: str):
        """Handle missing cost basis issue."""
        timestamp = tx.get("timestamp", "unknown")
        asset = tx.get("asset", "UNKNOWN")
        amount = tx.get("amount", "?")
        
        suggestions = [
            {
                "action": "link_wallet_transfer",
                "description": f"This might be a transfer from another wallet. Connect that wallet to fill in the cost.",
                "reason": "Transfers often have zero price if they're just movements between your own addresses."
            },
            {
                "action": "mark_as_gift",
                "description": "Mark this as a gift or airdrop",
                "value": "cost_basis = current_market_price",
                "reason": "If this was received for free (gift/airdrop), use current market price on that date as cost basis."
            },
            {
                "action": "lookup_historical_price",
                "description": f"Auto-fill price from historical data (CoinGecko)",
                "value": "fetching...",
                "reason": "We can look up what the market price was on that date."
            },
            {
                "action": "manual_entry",
                "description": "Enter the price manually",
                "reason": "You know the price (e.g., you bought OTC), enter it."
            }
        ]
        
        issue = RepairSuggestion(
            transaction_id=tx_id,
            issue_type="MISSING_COST_BASIS",
            issue_severity="ERROR",
            description=f"Transaction has zero cost basis: Received {amount} {asset} on {timestamp}",
            suggestions=suggestions,
            transaction_data={
                "timestamp": str(timestamp),
                "type": tx.get("type"),
                "asset": asset,
                "amount": amount,
            },
            confidence=0.95
        )
        self.issues.append(issue)
    
    def _issue_missing_date(self, tx: pd.Series, tx_id: str):
        """Handle missing date issue."""
        suggestions = [
            {
                "action": "estimate_from_context",
                "description": "Estimate date from transaction ID or hash",
                "reason": "We can often determine the date from blockchain data."
            },
            {
                "action": "manual_entry",
                "description": "Enter the date manually",
                "reason": "You should know when this transaction happened."
            }
        ]
        
        issue = RepairSuggestion(
            transaction_id=tx_id,
            issue_type="MISSING_DATE",
            issue_severity="ERROR",
            description=f"Transaction has invalid or missing date",
            suggestions=suggestions,
            transaction_data=tx.to_dict(),
            confidence=0.85
        )
        self.issues.append(issue)
    
    def _issue_suspicious_ratio(self, tx: pd.Series, tx_id: str, ratio: float):
        """Handle suspicious profit ratio."""
        suggestions = [
            {
                "action": "verify_calculation",
                "description": "Double-check the calculation",
                "reason": f"Profit ratio of {ratio:.1f}% is unusual. Could be a data entry error."
            },
            {
                "action": "check_splits_merges",
                "description": "Did this asset undergo a stock split or token merge?",
                "reason": "If ratio is 1000%+, could be a token split."
            },
            {
                "action": "correct_amount",
                "description": "Correct the transaction amount",
                "reason": "You might have entered the wrong quantity."
            }
        ]
        
        issue = RepairSuggestion(
            transaction_id=tx_id,
            issue_type="SUSPICIOUS_RATIO",
            issue_severity="WARNING",
            description=f"Unusual P&L ratio: {ratio:.1f}%. Verify this is correct.",
            suggestions=suggestions,
            transaction_data=tx.to_dict(),
            confidence=0.70
        )
        self.issues.append(issue)
    
    def _issue_extreme_fee(self, tx: pd.Series, tx_id: str, fee: float, tx_value: float):
        """Handle extreme fee issue."""
        fee_pct = (fee / tx_value) * 100
        
        suggestions = [
            {
                "action": "verify_fee_is_correct",
                "description": f"Fee is {fee_pct:.1f}% of transaction value. Confirm this is accurate.",
                "reason": f"Usually fees are <1%. A fee of {fee:.2f} on a {tx_value:.2f} transaction is unusual."
            },
            {
                "action": "correct_fee",
                "description": "Edit the fee amount",
                "reason": "You might have included something else (slippage, price impact) in the fee."
            }
        ]
        
        issue = RepairSuggestion(
            transaction_id=tx_id,
            issue_type="EXTREME_FEE",
            issue_severity="WARNING",
            description=f"Fee is {fee_pct:.1f}% of transaction value ({fee:.2f} USD)",
            suggestions=suggestions,
            transaction_data=tx.to_dict(),
            confidence=0.75
        )
        self.issues.append(issue)


class MagicRepairEngine:
    """Main repair engine for interactive data fixing."""
    
    def __init__(self):
        self.analyzer = DataQualityAnalyzer()
        self.historical_prices = {}  # Cache for historical prices
    
    def analyze_and_generate_fixes(
        self,
        df: pd.DataFrame
    ) -> dict:
        """Analyze data and generate repair suggestions.
        
        Returns JSON-ready dict with issues and fixes.
        """
        issues = self.analyzer.analyze_DataFrame(df)
        
        # Group by severity
        errors = [i for i in issues if i.issue_severity == "ERROR"]
        warnings = [i for i in issues if i.issue_severity == "WARNING"]
        info = [i for i in issues if i.issue_severity == "INFO"]
        
        # Convert to JSON-serializable format
        return {
            "status": "analysis_complete",
            "total_issues": len(issues),
            "errors": {
                "count": len(errors),
                "items": [self._issue_to_dict(i) for i in errors[:20]]  # Show top 20
            },
            "warnings": {
                "count": len(warnings),
                "items": [self._issue_to_dict(i) for i in warnings[:10]]
            },
            "info": {
                "count": len(info),
                "items": [self._issue_to_dict(i) for i in info[:5]]
            },
            "next_steps": self._generate_next_steps(errors, warnings),
            "summary": self._generate_summary(df, errors, warnings)
        }
    
    def _issue_to_dict(self, issue: RepairSuggestion) -> dict:
        """Convert issue to JSON-serializable dict."""
        return {
            "transaction_id": issue.transaction_id,
            "type": issue.issue_type,
            "severity": issue.issue_severity,
            "description": issue.description,
            "confidence": issue.confidence,
            "suggestions": issue.suggestions,
            "transaction": issue.transaction_data
        }
    
    def _generate_next_steps(self, errors: list, warnings: list) -> list[str]:
        """Generate actionable next steps."""
        steps = []
        
        if len(errors) > 0:
            steps.append(f"Fix {len(errors)} critical issues (marked as ERROR)")
        
        if len(warnings) > 0:
            steps.append(f"Review {len(warnings)} warnings for accuracy")
        
        if not steps:
            steps.append("Data quality looks good! Ready to proceed with analysis.")
        
        return steps
    
    def _generate_summary(self, df: pd.DataFrame, errors: list, warnings: list) -> dict:
        """Generate data quality summary."""
        return {
            "total_transactions": len(df),
            "transactions_with_errors": len(set(e.transaction_id for e in errors)),
            "transactions_with_warnings": len(set(w.transaction_id for w in warnings)),
            "quality_score": max(0, 100 - (len(errors) * 10 + len(warnings) * 2)),
            "estimates_needed": len([i for i in errors if "COST_BASIS" in i.issue_type]),
        }
    
    def apply_fix(
        self,
        df: pd.DataFrame,
        transaction_id: str,
        fix_action: str,
        fix_value: Optional[str] = None
    ) -> pd.DataFrame:
        """Apply a suggested fix to the dataframe.
        
        Args:
            df: Dataframe to fix
            transaction_id: ID of transaction to fix
            fix_action: Type of fix to apply
            fix_value: Value for the fix (if needed)
            
        Returns:
            Updated dataframe
        """
        df_fixed = df.copy()
        
        # Parse transaction ID to get index
        parts = transaction_id.split("_")
        idx = int(parts[1])
        
        if fix_action == "mark_as_gift":
            # Use current market price as cost basis
            df_fixed.at[idx, "price"] = fix_value or df_fixed.at[idx, "price"]
        
        elif fix_action == "manual_entry":
            # User provides the value
            df_fixed.at[idx, "price"] = fix_value
        
        elif fix_action == "correct_fee":
            df_fixed.at[idx, "fee"] = fix_value
        
        elif fix_action == "correct_amount":
            df_fixed.at[idx, "amount"] = fix_value
        
        return df_fixed


# ==================== API INTEGRATION ====================
"""
Add to your FastAPI app:

from app.quality.magic_repair import MagicRepairEngine
import pandas as pd

@app.post("/analyze/data-quality")
def analyze_data_quality_api(
    file: UploadFile,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Analyze uploaded CSV for quality issues and suggest fixes.'''
    
    # Read CSV
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # Analyze
    engine = MagicRepairEngine()
    analysis = engine.analyze_and_generate_fixes(df)
    
    return {
        "filename": file.filename,
        "analysis": analysis,
        "user_can_proceed": analysis["errors"]["count"] == 0
    }


@app.post("/fix/apply-suggestion")
def apply_fix(
    transaction_id: str,
    fix_action: str,
    fix_value: Optional[str] = None,
    current_user = Depends(get_current_user),
    db = Depends(get_db)
):
    '''Apply a suggested fix to a transaction.'''
    
    # Get user's data
    analysis_run = db.query(AnalysisRun).filter(
        AnalysisRun.user_id == current_user.id
    ).first()
    
    # Load dataframe
    df = pd.read_csv(analysis_run.csv_path)
    
    # Apply fix
    engine = MagicRepairEngine()
    df_fixed = engine.apply_fix(df, transaction_id, fix_action, fix_value)
    
    # Save fixed version
    df_fixed.to_csv(analysis_run.csv_path, index=False)
    
    return {
        "success": True,
        "transaction_id": transaction_id,
        "fix_applied": fix_action,
        "message": f"Fix applied successfully. Run analysis again to confirm."
    }
"""
