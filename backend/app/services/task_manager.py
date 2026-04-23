"""
Task Manager — submit and run analysis tasks in the background.

Uses FastAPI BackgroundTasks with SSE progress streaming.
"""
from __future__ import annotations

import traceback
from typing import Any

from app.services.stream_transport import TaskStage, TaskStore


class TaskManager:
    """Manages background analysis tasks with progress reporting."""

    def __init__(self):
        self.store = TaskStore.get()

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        return self.store.create_task()

    def run_analysis(
        self,
        task_id: str,
        file_bytes: bytes,
        user_id: int,
        filename: str,
        *,
        format_name: str = "native",
        accounting_method: str = "FIFO",
        country: str = "br",
        quote_currency: str = "BRL",
        use_ptax: bool = False,
        max_amount_diff: float = 0.01,
        max_time_diff_seconds: int = 3600,
        db_factory=None,
    ):
        """
        Run the full analysis pipeline with progress updates.
        This is called inside a BackgroundTask.
        """
        try:
            self.store.update(task_id, TaskStage.UPLOADING, "Processing uploaded file...")

            # Import here to avoid circular imports
            from pathlib import Path
            import tempfile
            import os
            import pandas as pd
            from app.ingestion.csv_loader import load_csv

            suffix = Path(filename).suffix or ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name

            try:
                # Stage 1: Load CSV
                self.store.update(task_id, TaskStage.NORMALIZING, "Loading and normalizing transactions...")
                raw = load_csv(tmp_path, validate_native_schema=(format_name == "native"))
                total_rows = len(raw)
                self.store.update(task_id, TaskStage.NORMALIZING,
                                  f"Normalizing {total_rows} transactions...",
                                  rows_processed=0, total_rows=total_rows)

                # Stage 2: Run the pipeline with progress callbacks
                from app.pipeline.analysis import run_tax_pipeline

                self.store.update(task_id, TaskStage.DEDUPLICATING, "Deduplicating transactions...",
                                  rows_processed=total_rows // 4, total_rows=total_rows)

                result = run_tax_pipeline(
                    raw,
                    format_name=format_name,
                    accounting_method=accounting_method,
                    country=country,
                    max_amount_diff=max_amount_diff,
                    max_time_diff_seconds=max_time_diff_seconds,
                    quote_currency=quote_currency,
                    use_ptax=use_ptax,
                    source_provider=format_name if format_name != "native" else None,
                    output_dir="output",
                )

                self.store.update(task_id, TaskStage.CALCULATING_PNL,
                                  "Calculating profit & loss...",
                                  rows_processed=total_rows * 3 // 4, total_rows=total_rows)

                self.store.update(task_id, TaskStage.GENERATING_REPORTS,
                                  "Generating reports...",
                                  rows_processed=total_rows, total_rows=total_rows)

                # Persist the run
                if db_factory:
                    from app.services.analysis_service import persist_run
                    import json

                    db = db_factory()
                    try:
                        run_id = persist_run(
                            db, user_id, result["normalized"],
                            {
                                "pnl": result["pnl"],
                                "rows_processed": result["rows_processed"],
                                "matches_found": result["matches_found"],
                                "format": format_name,
                                "quote_currency": quote_currency,
                                "accounting_method": accounting_method,
                                "use_ptax": use_ptax,
                            },
                            lot_matches=result["pnl"].get("lot_matches"),
                        )
                    finally:
                        db.close()
                else:
                    run_id = None

                # Build result summary (serializable)
                summary = {
                    "status": "ok",
                    "filename": filename,
                    "rows_processed": result["rows_processed"],
                    "matches_found": result["matches_found"],
                    "pnl": result["pnl"],
                    "issues": result["issues"],
                    "analysis_run_id": run_id,
                    "quote_currency": quote_currency.upper(),
                    "use_ptax": use_ptax,
                    "income_events": result.get("income_events", {}),
                    "loss_harvesting": result.get("loss_harvesting", {}),
                    "monthly_sales_brl": result.get("monthly_sales_brl", {}),
                    "isencao_threshold_brl": result.get("isencao_threshold_brl", 35000.0),
                    "darf": result.get("darf"),
                    "offshore_onshore": result.get("offshore_onshore", {}),
                }

                self.store.update(task_id, TaskStage.COMPLETE,
                                  f"Analysis complete: {result['rows_processed']} rows, {result['matches_found']} matches",
                                  rows_processed=total_rows, total_rows=total_rows,
                                  result=summary)

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            self.store.update(task_id, TaskStage.FAILED,
                              f"Analysis failed: {str(e)}",
                              error=str(e))
            traceback.print_exc()
