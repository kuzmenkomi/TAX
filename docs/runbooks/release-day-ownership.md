# Release-day ownership

Use this before any staging promotion or production deployment so ownership is explicit.

## Required roles

- Release owner: drives the deployment, calls go/no-go, and records timestamps.
- Observer/on-call: watches logs, metrics, Sentry, and user-facing health during rollout.
- Rollback owner: prepares the previous known-good revision and executes rollback if triggers fire.
- Incident owner: coordinates communication if rollback or customer impact is required.

One person may hold multiple roles only if the team explicitly accepts the risk before rollout.

## Before deployment

1. Assign named people to each role above.
2. Paste the deployment SHA and previous known-good SHA into the release ticket.
3. Link evidence for:
   - staging validation
   - full smoke test
   - backup filename
   - latest green CI run
4. Confirm where alerts are being watched:
   - backend/container logs
   - Sentry
   - infrastructure health (`/health`, `/ready`)
5. Keep these runbooks open:
   - `docs/runbooks/staging-validation.md`
   - `docs/runbooks/release-smoke-test.md`
   - `docs/runbooks/postgresql-backup-restore.md`
   - `docs/runbooks/deployment-rollback.md`

## Deployment responsibilities

- Release owner:
  - runs the deployment commands
  - announces start, smoke-test start, and completion
  - records exact deploy and verification times
- Observer/on-call:
  - tails backend and worker logs
  - checks Sentry for new errors in the active environment
  - confirms login, sync, and export paths remain healthy
- Rollback owner:
  - keeps rollback commands ready
  - verifies the pre-release backup exists before deployment
  - executes rollback immediately if a listed trigger is hit
- Incident owner:
  - updates the incident/release channel
  - tracks owner and ETA for any blocker

## Core commands

```bash
docker compose ps
docker compose logs backend --tail=100
docker compose logs worker --tail=100
docker compose exec backend curl -fsS http://localhost:8000/health
docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" PING
```

Backup before deploy:

```bash
./scripts/production_backup.sh
```

Rollback if needed:

```bash
git checkout <previous-known-good-revision>
docker compose build
docker compose up -d
docker compose ps
```

## Exit criteria

Mark the release complete only when:

- ownership was assigned and acknowledged
- deployment completed without rollback triggers
- abbreviated post-deploy smoke checks passed
- observer confirmed logs and Sentry are quiet or understood
- release owner recorded final status and follow-up items
