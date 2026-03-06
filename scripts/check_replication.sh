#!/usr/bin/env bash
set -euo pipefail

primary_id="$(docker compose ps -q mysql-primary)"
replica_id="$(docker compose ps -q mysql-replica)"

if [[ -z "${primary_id}" || -z "${replica_id}" ]]; then
  echo "Containers not found. Start the lab first:"
  echo "  make up"
  exit 2
fi

echo "Waiting for primary to accept connections..."
for _ in $(seq 1 60); do
  if docker exec -e MYSQL_PWD=root-password -i "${primary_id}" mysqladmin -uroot ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Waiting for replica to accept connections..."
for _ in $(seq 1 60); do
  if docker exec -e MYSQL_PWD=root-password -i "${replica_id}" mysqladmin -uroot ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Checking replica replication status..."
status="$(docker exec -e MYSQL_PWD=root-password -i "${replica_id}" mysql -uroot -e 'show slave status\\G' 2>/dev/null || true)"
if [[ -z "${status}" ]]; then
  echo "Replica did not return slave status. Replication may not be configured."
  exit 1
fi

echo "${status}" | grep -q "Slave_IO_Running: Yes" || { echo "Slave_IO_Running is not Yes"; echo "${status}"; exit 1; }
echo "${status}" | grep -q "Slave_SQL_Running: Yes" || { echo "Slave_SQL_Running is not Yes"; echo "${status}"; exit 1; }

echo "Replication looks healthy."
