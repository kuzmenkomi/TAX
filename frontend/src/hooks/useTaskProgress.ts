import { useState, useEffect, useCallback, useRef } from 'react';

interface TaskProgress {
  task_id: string;
  stage: string;
  progress: number;
  message: string;
  rows_processed: number;
  total_rows: number;
  error: string | null;
  result: any | null;
}

interface UseTaskProgressReturn {
  progress: TaskProgress | null;
  isComplete: boolean;
  isFailed: boolean;
  isRunning: boolean;
  error: string | null;
  connect: (taskId: string) => void;
  disconnect: () => void;
}

const STAGE_LABELS: Record<string, string> = {
  queued: 'Queued',
  uploading: 'Uploading file...',
  normalizing: 'Normalizing transactions...',
  deduplicating: 'Removing duplicates...',
  matching: 'Matching transfers...',
  calculating_pnl: 'Calculating P&L...',
  generating_reports: 'Generating reports...',
  reconciliation: 'Running reconciliation...',
  complete: 'Analysis complete!',
  failed: 'Analysis failed',
};

export function useTaskProgress(): UseTaskProgressReturn {
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const taskIdRef = useRef<string | null>(null);

  const isComplete = progress?.stage === 'complete';
  const isFailed = progress?.stage === 'failed';
  const isRunning = !!progress && !isComplete && !isFailed;

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const startPolling = useCallback((taskId: string) => {
    // Fallback polling every 2 seconds
    const token = localStorage.getItem('token');
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/task/${taskId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data: TaskProgress = await res.json();
          data.message = data.message || STAGE_LABELS[data.stage] || data.stage;
          setProgress(data);

          if (data.stage === 'complete' || data.stage === 'failed') {
            if (pollingRef.current) clearInterval(pollingRef.current);
            pollingRef.current = null;
            if (data.error) setError(data.error);
          }
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);
  }, []);

  const connect = useCallback((taskId: string) => {
    disconnect();
    setProgress(null);
    setError(null);
    taskIdRef.current = taskId;

    const token = localStorage.getItem('token');

    // Try SSE first
    try {
      const es = new EventSource(`/api/v1/sse/task/${taskId}?token=${token}`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const data: TaskProgress = JSON.parse(event.data);
          data.message = data.message || STAGE_LABELS[data.stage] || data.stage;
          setProgress(data);

          if (data.stage === 'complete' || data.stage === 'failed') {
            es.close();
            eventSourceRef.current = null;
            if (data.error) setError(data.error);
          }
        } catch {
          // Ignore parse errors
        }
      };

      es.onerror = () => {
        // SSE failed — fallback to polling
        es.close();
        eventSourceRef.current = null;
        startPolling(taskId);
      };
    } catch {
      // SSE not supported — fallback to polling
      startPolling(taskId);
    }
  }, [disconnect, startPolling]);

  // Cleanup on unmount
  useEffect(() => {
    return () => disconnect();
  }, [disconnect]);

  return {
    progress,
    isComplete,
    isFailed,
    isRunning,
    error,
    connect,
    disconnect,
  };
}

export { STAGE_LABELS };
export type { TaskProgress };
