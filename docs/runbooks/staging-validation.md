# Staging validation

Use this runbook to validate the Docker production path against a clean staging environment before release.

## Inputs

- `.env.staging` created from `.env.staging.example`
- DNS for the staging domain pointed at the host
- SSL certs mounted under `./nginx/ssl`
- Clean PostgreSQL volume or a brand-new database

## 1. Prepare the environment

```bash
python scripts/release_preflight.py --env-file .env.staging --expected-env staging --require-sentry
cp .env.staging .env
docker compose down -v
docker compose pull
docker compose build --no-cache
```

If you want to preserve an existing staging database, skip `-v` and create a fresh database name in `.env.staging` instead.

## 2. Start the full stack

```bash
docker compose up -d
docker compose ps
```

Expected services:

- `postgres` healthy
- `redis` running
- `backend` healthy
- `worker` running
- `frontend` running

## 3. Verify container health

```bash
curl -fsS https://<staging-domain>/
docker compose exec backend curl -fsS http://localhost:8000/health
docker compose logs backend --tail=100
docker compose logs worker --tail=100
```

Pass criteria:

- Frontend returns `200`
- `/health` returns `{"status":"healthy", ...}`
- Backend logs are readable and include startup context
- Worker logs include startup and no Redis/auth failures

## 4. Verify PostgreSQL and Redis connectivity

```bash
docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" PING
docker compose exec backend python -c "from app.core.config import get_settings; s=get_settings(); print(s.DATABASE_URL); print(s.REDIS_URL)"
```

Pass criteria:

- `pg_isready` reports the database is accepting connections
- Redis returns `PONG`
- Backend starts without connection or credential errors

## 5. Verify migrations on a clean database

```bash
docker compose down -v
docker compose up -d postgres redis
docker compose run --rm backend alembic upgrade head
docker compose up -d backend worker frontend
```

Optional schema check:

```bash
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

Pass criteria:

- `alembic upgrade head` exits `0`
- Backend becomes healthy after migrations
- Application pages load without migration errors

## 6. Evidence to capture

- `docker compose ps`
- backend and worker log excerpts
- `/health` response
- successful `alembic upgrade head`
- successful `python scripts/release_preflight.py ...`
- successful `python scripts/sentry_smoke.py ...`
- screenshots of login page and dashboard

## 7. Exit criteria

Staging validation is complete only when infrastructure checks and the release smoke test both pass in the same staging environment.
