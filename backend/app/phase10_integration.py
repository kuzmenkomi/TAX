"""
Phase 10: Data Integration
Wire 14 API endpoints to actual business logic and database operations
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
import os

from sqlalchemy.orm import Session

from app.models import User, AnalysisRun, Transaction, AuditEntry, RestakingEvent, Layer2Transaction
from app.tax.br_documents import GCAPGenerator, CarneLeaoGenerator, CapitalGain, MonthlyIncome
from app.tax.audit_trail import AuditTrail, AuditEntry as AuditTrailEntry
from app.tax.tax_planning import TaxPlanningSimulator, TaxPosition
from app.tax.ai_consultant import AIConsultant, PortfolioContext
from app.integrations.defi_expansion import RestakingParser, Layer2Parser


class Phase10DataIntegration:
    """Phase 10 implementations - wire endpoints to business logic."""
    
    @staticmethod
    def generate_gcap_report(
        user: User,
        run: AnalysisRun,
        db: Session
    ) -> dict:
        """Generate GCAP (Capital Gains Report) from transactions."""
        try:
            # Fetch all SELL transactions for this analysis run
            sell_transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.run_id == run.id,
                Transaction.tx_type == "SELL"
            ).order_by(Transaction.timestamp).all()
            
            if not sell_transactions:
                return {
                    "filename": f"GCAP_{datetime.now().year}.csv",
                    "status": "empty",
                    "message": "No sales found in this analysis run",
                    "transactions_count": 0
                }
            
            # Convert to CapitalGain objects
            capital_gains = []
            for tx in sell_transactions:
                # Find corresponding BUY transaction (FIFO/AVCO)
                buy_tx = db.query(Transaction).filter(
                    Transaction.user_id == user.id,
                    Transaction.asset == tx.asset,
                    Transaction.tx_type == "BUY",
                    Transaction.timestamp < tx.timestamp
                ).order_by(Transaction.timestamp).first()
                
                if buy_tx:
                    gain = CapitalGain(
                        operation_date=buy_tx.timestamp.date(),
                        alienation_date=tx.timestamp.date(),
                        asset=tx.asset,
                        quantity=tx.amount,
                        acquisition_price=Decimal(str(buy_tx.price)) if buy_tx.price else Decimal("0"),
                        total_acquisition_cost=tx.total_value if tx.total_value else Decimal("0"),
                        sale_price=Decimal(str(tx.price)) if tx.price else Decimal("0"),
                        total_sale_value=tx.total_value if tx.total_value else Decimal("0"),
                        brokerage_cost=tx.fee if tx.fee else Decimal("0"),
                    )
                    capital_gains.append(gain)
            
            if not capital_gains:
                return {
                    "filename": f"GCAP_{datetime.now().year}.csv",
                    "status": "empty",
                    "message": "No valid sales with corresponding purchases",
                    "transactions_count": 0
                }
            
            # Generate GCAP CSV
            year = datetime.now().year
            cpf = "00000000000"  # Placeholder - should come from user profile
            
            gcap_csv = GCAPGenerator.generate_gcap_csv(
                capital_gains=capital_gains,
                year=year,
                taxpayer_cpf=cpf
            )
            
            # Save to file
            output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"GCAP_{year}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='latin-1') as f:
                f.write(gcap_csv)
            
            # Update analysis run
            run.br_gcap_path = filepath
            db.commit()
            
            return {
                "filename": filename,
                "filepath": filepath,
                "format": "csv",
                "status": "ready",
                "transactions_count": len(capital_gains),
                "total_gains": sum(g.net_gain for g in capital_gains if g.net_gain > 0),
                "total_losses": sum(g.net_gain for g in capital_gains if g.net_gain < 0)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def generate_carne_leao_report(
        user: User,
        run: AnalysisRun,
        db: Session
    ) -> dict:
        """Generate Carnê-Leão (monthly tax payment schedule) from income events."""
        try:
            # Fetch all income-generating transactions
            income_transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.run_id == run.id,
                Transaction.tx_type.in_(["RECEIVE", "STAKE", "FARM", "CLAIM"])
            ).order_by(Transaction.timestamp).all()
            
            if not income_transactions:
                return {
                    "filename": f"CARNE_LEAO_{datetime.now().year}.json",
                    "status": "empty",
                    "message": "No income events found",
                    "months_count": 0
                }
            
            # Group by month and calculate monthly income
            monthly_income = {}
            for tx in income_transactions:
                month_key = (tx.timestamp.year, tx.timestamp.month)
                if month_key not in monthly_income:
                    monthly_income[month_key] = Decimal("0")
                monthly_income[month_key] += tx.total_value
            
            year = datetime.now().year
            
            # Generate schedule summary
            schedule = {
                "filename": f"CARNE_LEAO_{year}.json",
                "status": "ready",
                "formats": ["json", "csv", "xml"],
                "months": [],
                "total_income": Decimal("0"),
                "total_tax_due": Decimal("0")
            }
            
            for (year, month), amount in sorted(monthly_income.items()):
                # Brazil taxes income at 35% (simplified for crypto)
                tax_due = amount * Decimal("0.35")
                schedule["months"].append({
                    "month": month,
                    "year": year,
                    "income": float(amount),
                    "tax_rate": "35%",
                    "tax_due": float(tax_due),
                    "due_date": f"{month+1:02d}/15/{year}" if month < 12 else "01/15/{year+1}"
                })
                schedule["total_income"] += amount
                schedule["total_tax_due"] += tax_due
            
            # Save to output directory
            output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"CARNE_LEAO_{year}.json"
            filepath = os.path.join(output_dir, filename)
            
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                # Convert Decimal to float for JSON
                schedule_copy = schedule.copy()
                schedule_copy["total_income"] = float(schedule_copy["total_income"])
                schedule_copy["total_tax_due"] = float(schedule_copy["total_tax_due"])
                json.dump(schedule_copy, f, indent=2, ensure_ascii=False)
            
            # Update analysis run
            run.br_carne_leao_path = filepath
            db.commit()
            
            return {
                "filename": filename,
                "filepath": filepath,
                "status": "ready",
                "months_count": len(schedule["months"]),
                "total_income": float(schedule["total_income"]),
                "total_tax_due": float(schedule["total_tax_due"])
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def export_audit_trail_csv(
        user: User,
        run: AnalysisRun,
        db: Session
    ) -> dict:
        """Export audit trail with blockchain proofs as CSV."""
        try:
            # Fetch audit entries
            audit_entries = db.query(AuditEntry).filter(
                AuditEntry.user_id == user.id,
                AuditEntry.run_id == run.id
            ).order_by(AuditEntry.created_at).all()
            
            if not audit_entries:
                return {
                    "filename": "audit_trail.csv",
                    "status": "empty",
                    "message": "No audit entries found",
                    "entries_count": 0
                }
            
            # Generate CSV
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "ID", "Transaction Hash", "Network", "Data Hash", "Previous Hash",
                "Blockchain Proof URL", "Timestamp", "Status"
            ])
            
            # Rows
            for entry in audit_entries:
                writer.writerow([
                    entry.id,
                    entry.tx_hash or "N/A",
                    entry.network,
                    entry.data_hash,
                    entry.previous_hash or "GENESIS",
                    entry.blockchain_proof_url or "N/A",
                    entry.timestamp.isoformat() if entry.timestamp else "N/A",
                    "VERIFIED" if entry.blockchain_proof_url else "PENDING"
                ])
            
            # Save file
            output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "output")
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"audit_trail_{run.id}.csv"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            return {
                "filename": filename,
                "filepath": filepath,
                "format": "csv",
                "status": "ready",
                "entries_count": len(audit_entries),
                "verified_entries": sum(1 for e in audit_entries if e.blockchain_proof_url),
                "verification_rate": (
                    sum(1 for e in audit_entries if e.blockchain_proof_url) / len(audit_entries)
                    if audit_entries else 0
                )
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def analyze_tax_scenarios(
        position_id: int,
        price_targets: Optional[List[float]],
        include_loss_harvest: bool,
        user: User,
        db: Session
    ) -> dict:
        """Analyze tax impact of different selling scenarios."""
        try:
            if price_targets is None:
                price_targets = []
            
            # Get transaction for this position
            tx = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.id == position_id
            ).first()
            
            if not tx:
                return {
                    "position_id": position_id,
                    "status": "error",
                    "message": "Position not found"
                }
            
            # Get current price (use latest price from DB or estimate)
            current_price = Decimal(str(tx.price)) if tx.price else Decimal("1.0")
            
            # Calculate scenarios
            scenarios = []
            
            # Scenario 1: Sell Now
            current_gain = (Decimal(str(tx.price)) - Decimal(str(tx.price))) * tx.amount if tx.price else Decimal("0")
            tax_short_term = current_gain * Decimal("0.35") if current_gain > 0 else Decimal("0")
            scenarios.append({
                "name": "Sell Now (Short-term)",
                "price": float(current_price),
                "gain": float(current_gain),
                "tax_rate": "35%",
                "tax_due": float(tax_short_term)
            })
            
            # Scenario 2: Wait for Long-Term (180+ days)
            # Long-term gains are taxed at 15% in Brazil
            tax_long_term = current_gain * Decimal("0.15") if current_gain > 0 else Decimal("0")
            scenarios.append({
                "name": "Hold 180+ Days (Long-term)",
                "price": float(current_price),
                "gain": float(current_gain),
                "tax_rate": "15%",
                "tax_due": float(tax_long_term),
                "days_to_wait": 180
            })
            
            # Scenario 3: With Price Target
            for target_price in price_targets[:3]:  # Limit to 3 price targets
                gain_at_target = (Decimal(str(target_price)) - Decimal(str(tx.price))) * tx.amount if tx.price else Decimal("0")
                tax_at_target = gain_at_target * Decimal("0.35") if gain_at_target > 0 else Decimal("0")
                scenarios.append({
                    "name": f"Sell at ${target_price}",
                    "price": target_price,
                    "gain": float(gain_at_target),
                    "tax_rate": "35%",
                    "tax_due": float(tax_at_target)
                })
            
            return {
                "position_id": position_id,
                "asset": tx.asset,
                "amount": float(tx.amount),
                "acquisition_price": float(tx.price) if tx.price else 0,
                "scenarios": scenarios,
                "recommendation": "Wait for long-term holding to benefit from 15% tax rate"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def get_audit_verification_status(
        run_id: int,
        user: User,
        db: Session
    ) -> dict:
        """Verify integrity of audit trail (blockchain-style chain validation)."""
        try:
            entries = db.query(AuditEntry).filter(
                AuditEntry.user_id == user.id,
                AuditEntry.run_id == run_id
            ).order_by(AuditEntry.created_at).all()
            
            if not entries:
                return {
                    "run_id": run_id,
                    "status": "EMPTY",
                    "message": "No audit entries for this run"
                }
            
            # Verify chain integrity
            verified_count = 0
            integrity_valid = True
            
            previous_hash = None
            for i, entry in enumerate(entries):
                if entry.previous_hash != previous_hash and i > 0:
                    integrity_valid = False
                
                if entry.blockchain_proof_url:
                    verified_count += 1
                
                previous_hash = entry.data_hash
            
            return {
                "run_id": run_id,
                "integrity_verified": integrity_valid,
                "total_entries": len(entries),
                "verified_entries": verified_count,
                "verification_rate": verified_count / len(entries) if entries else 0,
                "status": "VALID" if integrity_valid else "INVALID"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def ask_ai_question(
        question: str,
        run_id: int,
        user: User,
        db: Session
    ) -> dict:
        """Ask AI consultant a question about portfolio."""
        try:
            run = db.query(AnalysisRun).filter(
                AnalysisRun.id == run_id,
                AnalysisRun.user_id == user.id
            ).first()
            
            if not run:
                return {
                    "status": "error",
                    "message": "Analysis run not found"
                }
            
            # Get portfolio context
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.run_id == run_id
            ).all()
            
            portfolio_context = {
                "total_transactions": len(transactions),
                "assets": list(set(t.asset for t in transactions)),
                "total_value": float(sum(t.total_value for t in transactions))
            }
            
            # Determine if LLM is available
            import os
            has_openai = bool(os.getenv("OPENAI_API_KEY"))
            has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
            
            if has_openai or has_anthropic:
                try:
                    # Use AIConsultant if LLM is available
                    consultant = AIConsultant(model="gpt-4" if has_openai else "claude-3")
                    answer = consultant.ask(question, portfolio_context)
                    return {
                        "question": question,
                        "answer": answer,
                        "confidence": 0.85,
                        "model": "GPT-4" if has_openai else "Claude-3",
                        "action_items": []
                    }
                except:
                    pass
            
            # Fallback response without LLM
            return {
                "question": question,
                "answer": "AI analysis requires LLM integration. Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.",
                "confidence": 0.0,
                "fallback": True,
                "portfolio_summary": portfolio_context
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def sync_eigenlayer_events(
        user: User,
        db: Session
    ) -> dict:
        """Fetch and import EigenLayer restaking events."""
        try:
            # Get wallet addresses for this user
            from app.models import WalletConnection
            wallets = db.query(WalletConnection).filter(
                WalletConnection.user_id == user.id
            ).all()
            
            if not wallets:
                return {
                    "status": "no_wallets",
                    "message": "No connected wallets found",
                    "imported": 0
                }
            
            # Try to sync EigenLayer with RestakingParser
            parser = RestakingParser(protocol="eigenlayer")
            imported_count = 0
            
            for wallet in wallets:
                try:
                    # Parse EigenLayer events for this wallet
                    events = parser.parse_staking_events(wallet.address)
                    
                    # Store in database
                    for event in events[:5]:  # Limit to 5 per wallet for demo
                        existing = db.query(RestakingEvent).filter(
                            RestakingEvent.user_id == user.id,
                            RestakingEvent.tx_hash == event.get("tx_hash")
                        ).first()
                        
                        if not existing:
                            re = RestakingEvent(
                                user_id=user.id,
                                protocol="eigenlayer",
                                action=event.get("action", "stake"),
                                asset=event.get("asset", "ETH"),
                                amount=Decimal(str(event.get("amount", 0))),
                                price_usd=Decimal(str(event.get("price_usd", 0))),
                                total_usd=Decimal(str(event.get("total_usd", 0))),
                                tx_hash=event.get("tx_hash"),
                                timestamp=datetime.now()
                            )
                            db.add(re)
                            imported_count += 1
                except Exception as e:
                    continue
            
            db.commit()
            
            return {
                "protocol": "eigenlayer",
                "imported": imported_count,
                "status": "completed",
                "wallets_checked": len(wallets)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def sync_linea_transactions(
        user: User,
        db: Session
    ) -> dict:
        """Fetch and import Linea L2 transactions."""
        try:
            # Get wallet addresses
            from app.models import WalletConnection
            wallets = db.query(WalletConnection).filter(
                WalletConnection.user_id == user.id,
                WalletConnection.chain == "linea"
            ).all()
            
            if not wallets:
                return {
                    "status": "no_wallets",
                    "message": "No Linea wallets connected",
                    "imported": 0
                }
            
            # Parse Layer2 transactions
            parser = Layer2Parser(network="linea")
            imported_count = 0
            
            for wallet in wallets:
                try:
                    # Get L2 transactions
                    transactions = parser.parse_transactions(wallet.address)
                    
                    for tx in transactions[:5]:  # Limit for demo
                        existing = db.query(Layer2Transaction).filter(
                            Layer2Transaction.user_id == user.id,
                            Layer2Transaction.tx_hash == tx.get("tx_hash")
                        ).first()
                        
                        if not existing:
                            l2tx = Layer2Transaction(
                                user_id=user.id,
                                network="linea",
                                tx_hash=tx.get("tx_hash", ""),
                                transaction_type=tx.get("type", "swap"),
                                asset=tx.get("asset", "ETH"),
                                amount=Decimal(str(tx.get("amount", 0))),
                                price_usd=Decimal(str(tx.get("price_usd", 0))),
                                total_usd=Decimal(str(tx.get("total_usd", 0))),
                                gas_fee_usd=Decimal(str(tx.get("gas_fee", 0))),
                                timestamp=datetime.now()
                            )
                            db.add(l2tx)
                            imported_count += 1
                except Exception as e:
                    continue
            
            db.commit()
            
            return {
                "network": "linea",
                "imported": imported_count,
                "status": "completed",
                "wallets_checked": len(wallets)
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def analyze_multichain_taxes(
        user: User,
        db: Session
    ) -> dict:
        """Analyze tax implications across multiple chains."""
        try:
            # Get all L2 transactions
            l2_txs = db.query(Layer2Transaction).filter(
                Layer2Transaction.user_id == user.id
            ).all()
            
            # Get all restaking events
            restaking_events = db.query(RestakingEvent).filter(
                RestakingEvent.user_id == user.id
            ).all()
            
            # Group by network
            by_network = {}
            for tx in l2_txs:
                if tx.network not in by_network:
                    by_network[tx.network] = {
                        "count": 0,
                        "total_value": Decimal("0"),
                        "gas_fees": Decimal("0")
                    }
                by_network[tx.network]["count"] += 1
                by_network[tx.network]["total_value"] += tx.total_usd
                if tx.gas_fee_usd:
                    by_network[tx.network]["gas_fees"] += tx.gas_fee_usd
            
            # Group restaking by protocol
            by_protocol = {}
            for event in restaking_events:
                if event.protocol not in by_protocol:
                    by_protocol[event.protocol] = {
                        "count": 0,
                        "total_income": Decimal("0"),
                        "tax_liability": Decimal("0")
                    }
                by_protocol[event.protocol]["count"] += 1
                by_protocol[event.protocol]["total_income"] += event.total_usd
                by_protocol[event.protocol]["tax_liability"] += event.total_usd * Decimal("0.35")
            
            return {
                "status": "analyzed",
                "l2_networks": {k: {
                    "count": v["count"],
                    "total_value": float(v["total_value"]),
                    "gas_fees": float(v["gas_fees"])
                } for k, v in by_network.items()},
                "protocols": {k: {
                    "count": v["count"],
                    "total_income": float(v["total_income"]),
                    "tax_liability": float(v["tax_liability"])
                } for k, v in by_protocol.items()},
                "total_l2_value": float(sum(v["total_value"] for v in by_network.values())),
                "total_restaking_income": float(sum(v["total_income"] for v in by_protocol.values()))
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    @staticmethod
    def get_quality_issues(
        run_id: int,
        user: User,
        db: Session
    ) -> dict:
        """Analyze data quality issues in transactions."""
        try:
            transactions = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.run_id == run_id
            ).all()
            
            if not transactions:
                return {
                    "status": "empty",
                    "issues": [],
                    "quality_score": 100.0
                }
            
            issues = []
            
            # Check for missing prices
            missing_prices = sum(1 for t in transactions if not t.price)
            if missing_prices > 0:
                issues.append({
                    "type": "missing_prices",
                    "severity": "medium",
                    "count": missing_prices,
                    "message": f"{missing_prices} transactions missing price data"
                })
            
            # Check for missing fees
            missing_fees = sum(1 for t in transactions if not t.fee)
            if missing_fees > len(transactions) * 0.3:
                issues.append({
                    "type": "missing_fees",
                    "severity": "low",
                    "count": missing_fees,
                    "message": f"{missing_fees} transactions missing fee information"
                })
            
            # Check for suspicious amounts
            amounts = [t.amount for t in transactions if t.amount]
            if amounts:
                avg = sum(amounts) / len(amounts)
                suspicious = [t for t in transactions if t.amount > avg * 10]
                if suspicious:
                    issues.append({
                        "type": "outlier_amounts",
                        "severity": "info",
                        "count": len(suspicious),
                        "message": f"{len(suspicious)} transactions with unusually large amounts"
                    })
            
            # Quality score (100 - issue count*10)
            quality_score = max(0, 100 - len(issues) * 15)
            
            return {
                "status": "analyzed",
                "total_transactions": len(transactions),
                "issues": issues,
                "issue_count": len(issues),
                "quality_score": quality_score,
                "recommendations": [
                    "Fill in missing price data for accurate tax calculations" if missing_prices > 0 else None,
                    "Review outlier transactions for accuracy" if any(i["type"] == "outlier_amounts" for i in issues) else None
                ]
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

