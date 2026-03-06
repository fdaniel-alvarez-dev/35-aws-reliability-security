#!/usr/bin/env bash
set -euo pipefail

primary_id="$(docker compose ps -q mysql-primary)"
if [[ -z "${primary_id}" ]]; then
  echo "MySQL primary container not found. Run: make up"
  exit 2
fi

echo "Seeding demo data into appdb..."
docker exec -e MYSQL_PWD=app-password -i "${primary_id}" mysql -uapp appdb <<'SQL'
create table if not exists demo_items (
  id bigint unsigned not null auto_increment primary key,
  created_at timestamp not null default current_timestamp,
  payload varchar(255) not null
);

insert into demo_items (payload)
values
  ('demo-payload-1'),
  ('demo-payload-2'),
  ('demo-payload-3'),
  ('demo-payload-4'),
  ('demo-payload-5'),
  ('demo-payload-6'),
  ('demo-payload-7'),
  ('demo-payload-8'),
  ('demo-payload-9'),
  ('demo-payload-10');

select count(*) as demo_items_count from demo_items;
SQL

