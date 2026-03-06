#!/usr/bin/env bash
set -euo pipefail

latest="$(ls -1 artifacts/backups/*.sql 2>/dev/null | tail -n 1 || true)"
if [[ -z "${latest}" ]]; then
  echo "No backups found under artifacts/backups/. Run: make backup"
  exit 1
fi

primary_id="$(docker compose ps -q mysql-primary)"
if [[ -z "${primary_id}" ]]; then
  echo "MySQL primary container not found. Run: make up"
  exit 2
fi

verify_db="appdb_verify"

echo "Restoring latest backup into isolated database '${verify_db}': ${latest}"
docker exec -e MYSQL_PWD=root-password -i "${primary_id}" mysql -uroot -e "drop database if exists ${verify_db}; create database ${verify_db};"

echo "Loading dump (stripping USE statements to keep restore isolated)..."
sed -e '/^-- Current Database:/d' -e '/^USE `/d' "${latest}" | docker exec -e MYSQL_PWD=root-password -i "${primary_id}" mysql -uroot "${verify_db}"

echo "Verifying restored data..."
docker exec -e MYSQL_PWD=root-password -i "${primary_id}" mysql -uroot "${verify_db}" -e "select count(*) as demo_items_count from demo_items;"

echo "Restore verification complete."
