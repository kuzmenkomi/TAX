"""SSE endpoint for streaming task progress."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.auth import get_current_user
from app.models import User
from app.services.stream_transport import TaskStore, sse_stream

router = APIRouter(prefix="/sse", tags=["SSE"])


@router.get("/task/{task_id}")
async def stream_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    SSE endpoint that streams real-time task progress.
    
    Connect with EventSource:
        const es = new EventSource('/api/v1/sse/task/<task_id>');
        es.onmessage = (e) => { const data = JSON.parse(e.data); ... };
    """
    store = TaskStore.get()
    status = store.get_status(task_id)
    if status is None:
        return {"error": "Task not found"}

    return StreamingResponse(
        sse_stream(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )
