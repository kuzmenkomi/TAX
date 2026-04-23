"""
Stream Transport Abstraction — SSE (free), WebSocket (upgrade), Polling (fallback).

Switch transports via STREAM_TRANSPORT env var: sse | ws | polling
"""
from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncGenerator, Optional


class TaskStage(str, Enum):
    QUEUED = "queued"
    UPLOADING = "uploading"
    NORMALIZING = "normalizing"
    DEDUPLICATING = "deduplicating"
    MATCHING = "matching"
    CALCULATING_PNL = "calculating_pnl"
    GENERATING_REPORTS = "generating_reports"
    RECONCILIATION = "reconciliation"
    COMPLETE = "complete"
    FAILED = "failed"


STAGE_PROGRESS = {
    TaskStage.QUEUED: 0,
    TaskStage.UPLOADING: 5,
    TaskStage.NORMALIZING: 15,
    TaskStage.DEDUPLICATING: 25,
    TaskStage.MATCHING: 40,
    TaskStage.CALCULATING_PNL: 60,
    TaskStage.GENERATING_REPORTS: 80,
    TaskStage.RECONCILIATION: 90,
    TaskStage.COMPLETE: 100,
    TaskStage.FAILED: -1,
}


@dataclass
class TaskProgress:
    """Progress update for a background task."""
    task_id: str
    stage: TaskStage
    progress: int  # 0-100
    message: str = ""
    rows_processed: int = 0
    total_rows: int = 0
    error: str | None = None
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "stage": self.stage.value,
            "progress": self.progress,
            "message": self.message,
            "rows_processed": self.rows_processed,
            "total_rows": self.total_rows,
            "error": self.error,
            "result": self.result,
        }

    def to_sse_event(self) -> str:
        """Format as SSE event string."""
        data = json.dumps(self.to_dict())
        return f"data: {data}\n\n"


# ---------------------------------------------------------------------------
# Task Store (in-memory, upgradeable to Redis)
# ---------------------------------------------------------------------------

class TaskStore:
    """
    In-memory task progress store.
    
    Upgrade path: Replace with Redis-backed store for multi-worker deployments.
    Just implement the same interface with redis pub/sub.
    """

    _instance: Optional["TaskStore"] = None

    def __init__(self):
        self._tasks: dict[str, TaskProgress] = {}
        self._events: dict[str, asyncio.Event] = {}
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    @classmethod
    def get(cls) -> "TaskStore":
        if cls._instance is None:
            cls._instance = TaskStore()
        return cls._instance

    def create_task(self) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskProgress(
            task_id=task_id,
            stage=TaskStage.QUEUED,
            progress=0,
            message="Task queued",
        )
        self._events[task_id] = asyncio.Event()
        self._subscribers[task_id] = []
        return task_id

    def update(self, task_id: str, stage: TaskStage, message: str = "",
               rows_processed: int = 0, total_rows: int = 0,
               error: str | None = None, result: dict | None = None):
        """Update task progress and notify subscribers."""
        progress = TaskProgress(
            task_id=task_id,
            stage=stage,
            progress=STAGE_PROGRESS.get(stage, 0),
            message=message,
            rows_processed=rows_processed,
            total_rows=total_rows,
            error=error,
            result=result,
        )
        self._tasks[task_id] = progress

        # Notify all subscribers
        for queue in self._subscribers.get(task_id, []):
            try:
                queue.put_nowait(progress)
            except asyncio.QueueFull:
                pass

        # Signal completion
        if stage in (TaskStage.COMPLETE, TaskStage.FAILED):
            event = self._events.get(task_id)
            if event:
                event.set()

    def get_status(self, task_id: str) -> TaskProgress | None:
        return self._tasks.get(task_id)

    def subscribe(self, task_id: str) -> asyncio.Queue:
        """Subscribe to task progress updates. Returns a queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=50)
        if task_id not in self._subscribers:
            self._subscribers[task_id] = []
        self._subscribers[task_id].append(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue):
        """Unsubscribe from task progress."""
        subs = self._subscribers.get(task_id, [])
        if queue in subs:
            subs.remove(queue)

    async def wait_for_completion(self, task_id: str, timeout: float = 300) -> TaskProgress | None:
        """Wait for a task to complete."""
        event = self._events.get(task_id)
        if event:
            try:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                pass
        return self._tasks.get(task_id)

    def cleanup(self, task_id: str):
        """Clean up completed task resources."""
        self._tasks.pop(task_id, None)
        self._events.pop(task_id, None)
        self._subscribers.pop(task_id, None)


# ---------------------------------------------------------------------------
# SSE Transport (FREE — default)
# ---------------------------------------------------------------------------

async def sse_stream(task_id: str) -> AsyncGenerator[str, None]:
    """
    Server-Sent Events stream for task progress.
    
    Usage in FastAPI:
        from starlette.responses import StreamingResponse
        return StreamingResponse(sse_stream(task_id), media_type="text/event-stream")
    """
    store = TaskStore.get()
    queue = store.subscribe(task_id)

    # Send current status first
    current = store.get_status(task_id)
    if current:
        yield current.to_sse_event()

    try:
        while True:
            try:
                progress = await asyncio.wait_for(queue.get(), timeout=15.0)
                yield progress.to_sse_event()

                if progress.stage in (TaskStage.COMPLETE, TaskStage.FAILED):
                    break
            except asyncio.TimeoutError:
                # Heartbeat keepalive
                yield ": heartbeat\n\n"
    finally:
        store.unsubscribe(task_id, queue)
