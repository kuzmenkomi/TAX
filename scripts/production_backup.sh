#!/bin/bash
set -euo pipefail

# Create a compressed PostgreSQL dump for the Docker deployment.

ENV_FILE="${ENV_FILE:-.env}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
POSTGRES_SERVICE="${POSTGRES_SERVICE:-postgres}"
POSTGRES_USER="${POSTGRES_USER:-taxuser}"
POSTGRES_DB="${POSTGRES_DB:-tax_app_db}"
TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"

if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  set -a && source "$ENV_FILE" && set +a
fi

mkdir -p "$BACKUP_DIR"

BACKUP_NAME="declairo_pg_${TIMESTAMP}.sql.gz"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
CHECKSUM_PATH="${BACKUP_PATH}.sha256"

echo "Starting PostgreSQL backup for database ${POSTGRES_DB} via service ${POSTGRES_SERVICE}..."
docker compose exec -T "$POSTGRES_SERVICE" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$BACKUP_PATH"
sha256sum "$BACKUP_PATH" > "$CHECKSUM_PATH"

find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -type f -name "*.sha256" -mtime +30 -delete

echo "Backup completed: $BACKUP_PATH"
echo "Checksum written: $CHECKSUM_PATH"
