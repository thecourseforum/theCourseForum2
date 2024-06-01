#!/bin/sh

docker exec tcf_django black .
docker exec tcf_django isort .
docker exec tcf_django npx prettier --write .
docker exec tcf_django npx eslint --fix -c .config/.eslintrc.yml tcf_website/static/
