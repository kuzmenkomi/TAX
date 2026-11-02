#!/bin/bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <backup.sql.gz>"
  exit 1
fi

BACKUP_FILE="$1"
ENV_FILE="${ENV_FILE:-.env}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-taxuser}"
POSTGRES_DB="${POSTGRES_DB:-tax_app_db}"
RESTORE_OVERWRITE="${RESTORE_OVERWRITE:-false}"

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 1
fi

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

if [[ "$RESTORE_OVERWRITE" != "true" ]]; then
  echo "Refusing to restore without RESTORE_OVERWRITE=true"
  exit 1
fi

echo "Restoring $BACKUP_FILE into database $POSTGRES_DB via service $POSTGRES_SERVICE"

docker compose exec -T "$POSTGRES_SERVICE" psql -U "$POSTGRES_USER" -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();"
docker compose exec -T "$POSTGRES_SERVICE" psql -U "$POSTGRES_USER" -d postgres -c "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";"
docker compose exec -T "$POSTGRES_SERVICE" psql -U "$POSTGRES_USER" -d postgres -c "CREATE DATABASE \"$POSTGRES_DB\";"
gzip -dc "$BACKUP_FILE" | docker compose exec -T "$POSTGRES_SERVICE" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"

echo "Restore completed successfully"
