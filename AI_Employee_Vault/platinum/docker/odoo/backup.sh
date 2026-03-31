#!/bin/bash
BACKUP_DIR="$HOME/odoo_backups"
DATE=$(date +%Y-%m-%d)
mkdir -p "$BACKUP_DIR"
docker exec platinum-db-1 pg_dump -U odoo ai_employee \
  | gzip > "$BACKUP_DIR/odoo_${DATE}.sql.gz"
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
echo "Backup complete: $BACKUP_DIR/odoo_${DATE}.sql.gz"
