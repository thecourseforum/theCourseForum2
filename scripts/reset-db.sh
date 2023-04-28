#!/bin/bash

# Make sure to set the DB_FILE environment variable to the name of your SQL dump
docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db bash -c 'psql tcf_db -U tcf_django < "app/$DB_FILE"'
