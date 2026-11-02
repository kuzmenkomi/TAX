# PostgreSQL backup and restore

Use this runbook for staging and production PostgreSQL backups when running the Docker stack.

## Backup

Create a compressed dump with the helper script:

```bash
./scripts/production_backup.sh
```

Environment variables the script respects:

- `BACKUP_DIR` default: `./backups`
- `POSTGRES_SERVICE` default: `postgres`
- `POSTGRES_USER`
- `POSTGRES_DB`
- `ENV_FILE` default: `.env`

Expected output:

- a `.sql.gz` dump file
- a matching `.sha256` checksum file

## Restore

Restore a dump file with:

```bash
./scripts/postgresql_restore.sh ./backups/declairo_pg_YYYYMMDD_HHMMSS.sql.gz
```

Safety requirements:

- set `RESTORE_OVERWRITE=true`
- confirm the target database is the intended restore destination

## Verification

After restore:

```bash
docker compose exec postgres pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"
docker compose exec postgres psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"
```

Then start the backend and run:

```bash
docker compose up -d backend worker frontend
docker compose exec backend curl -fsS http://localhost:8000/health
```

## Retention

- Keep daily backups for at least 30 days
- Keep the pre-release backup until the release is stable
- Store backups outside the deployment host when possible
