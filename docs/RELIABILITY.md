# Reliability & operations

## Backups

- Schedule `scripts/production_backup.sh` (or provider-native snapshots) for PostgreSQL.
- Run **restore drills** on staging quarterly.

## Horizontal scaling

- Use PostgreSQL-backed APScheduler job store when `DATABASE_URL` is PostgreSQL.
- Move task progress to Redis for multi-worker SSE (see `app.services.stream_transport.TaskStore`).

## Deployments

- Prefer blue/green or canary releases behind nginx or a load balancer.
- Set `ENABLE_METRICS=1` to expose Prometheus `/metrics` on the API (restrict at the network edge).

## SLOs (suggested)

- API availability 99.5%+
- p95 login latency < 500ms
- Exchange sync success rate tracked in metrics
