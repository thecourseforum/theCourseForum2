#!/bin/sh

if [ -z "$1" ]; then
	echo "Must specify location to clone and set up theCourseForum2 respository."
	exit 1
fi

exists() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "Error: '$1' is not installed. Please install '$1'." >&2
		exit 1
	}
}

exists git

exists docker

if [ ! git clone 'git@github.com/thecourseforum/theCourseForum2.git' ]; then
	echo "Unable to clone thecourseforum/theCourseForum2 with SSH. Ensure you have an ssh key set up on your GitHub account."
	echo "See https://docs.github.com/en/authentication/connecting-to-github-with-ssh for more info."
	exit 1
fi

docker compose up --build --no-cache
docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker exec -i tcf_db psql tcf_db -U tcf_django -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
docker exec -i tcf_db psql tcf_db -U tcf_django <db/latest.sql
