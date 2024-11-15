#!/bin/sh

if [ -z "$1" ]; then
	echo "Must specify location to clone and set up theCourseForum2 respository."
	exit
fi

exists() {
	command -v "$1" >/dev/null 2>&1 || {
		echo "Error: '$1' is not installed. Please install '$1'." >&2
		exit
	}
}

exists git

exists docker

git clone git@github.com:thecourseforum/theCourseForum2.git
if [ "$?" -ne 0 ]; then
	echo "Unable to clone thecourseforum/theCourseForum2 with SSH. Ensure you have an ssh key set up on your GitHub account."
	echo "See https://docs.github.com/en/authentication/connecting-to-github-with-ssh for more info."
	exit 1
fi

cd theCourseForum2 || exit
# TODO: remove this when on main
git switch lfs-db

echo ""
echo "============================================"
echo "Please ensure that the '.env' file exists in the repository directory: $1"
echo "Once you have created the '.env' file, press Enter to continue."
echo "If the '.env' file does not exist, the script will exit."
echo "============================================"

printf "Press Enter to continue after verifying the '.env' file..."
read -r _ < /dev/tty

[ ! -f ".env" ] && echo "Error: '.env' file does not exist in '$1'. Follow the installation instructions in doc/dev.md after creating a '.env' file." && exit 1

docker compose build --no-cache
docker compose up
(
	docker exec -i tcf_db psql tcf_db -U tcf_django -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	docker exec -i tcf_db psql tcf_db -U tcf_django -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
	docker exec -i tcf_db psql tcf_db -U tcf_django <db/latest.sql
) &

echo ""
echo "============================================"
echo "Your're good to go!"
echo "Run the project with \`docker compose up\`"
echo "============================================"
