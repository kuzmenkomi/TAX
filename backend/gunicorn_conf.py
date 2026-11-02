import multiprocessing
import os

# Gunicorn configuration for production
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
# Keep a conservative default for 1 GB container targets; allow override via WEB_CONCURRENCY.
default_workers = max(1, min(multiprocessing.cpu_count(), 2))
workers = int(os.getenv("WEB_CONCURRENCY", str(default_workers)))
worker_class = "uvicorn.workers.UvicornWorker"

# Stability: restart workers after N requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Timeout for long crypto calculations/syncs
timeout = 120
keepalive = 5

# Logging
accesslog = "-" # Stdout
errorlog = "-"  # Stderr
loglevel = "info"

# Security: trust forwarded headers only from Docker-internal proxies (Nginx sidecar).
# Override via FORWARDED_ALLOW_IPS env var if running behind a different proxy.
_trusted = os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1,172.16.0.0/12,192.168.0.0/16,10.0.0.0/8")
forwarded_allow_ips = _trusted
proxy_allow_ips = _trusted
