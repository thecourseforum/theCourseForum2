#!/bin/sh

LATEST_DB_URL='https://github.com/theCourseForum/tCF-Secrets/db.sql'
DB_FILE='db/db.sql'
curl "$LATEST_DB_URL" >"$DB_FILE"

docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db bash -c "psql tcf_db -U tcf_django < $DB_FILE"
