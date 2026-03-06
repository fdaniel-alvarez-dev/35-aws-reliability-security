#!/usr/bin/env bash
set -euo pipefail

mkdir -p artifacts/backups
ts="$(date -u +%Y%m%dT%H%M%SZ)"
out="artifacts/backups/appdb-${ts}.sql"

primary_id="$(docker compose ps -q mysql-primary)"
if [[ -z "${primary_id}" ]]; then
  echo "MySQL primary container not found. Run: make up"
  exit 2
fi

echo "Creating logical backup to ${out}..."
docker exec -e MYSQL_PWD=app-password -i "${primary_id}" mysqldump -uapp --single-transaction --skip-lock-tables appdb > "${out}"

echo "Backup created."
