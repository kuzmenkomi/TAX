#!/bin/sh
# backup-db.sh — Automated PostgreSQL backup script for Declairo.
# Usage: ./scripts/backup-db.sh
# Designed to run inside the postgres container or from the host via docker exec.

set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="${POSTGRES_DB:-tax_app_db}"
DB_USER="${POSTGRES_USER:-taxuser}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql.gz"

echo "[$(date -Iseconds)] Starting backup of database '$DB_NAME'..."

pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date -Iseconds)] Backup complete: $BACKUP_FILE ($BACKUP_SIZE)"

# Prune old backups beyond retention period
PRUNED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete -print | wc -l)
if [ "$PRUNED" -gt 0 ]; then
    echo "[$(date -Iseconds)] Pruned $PRUNED backups older than $RETENTION_DAYS days"
fi

echo "[$(date -Iseconds)] Backup job finished successfully."
