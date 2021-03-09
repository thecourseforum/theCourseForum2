#!/bin/sh
# Auto format.
docker exec tcf_django autopep8 --in-place --jobs=0 --aggressive --aggressive -r tcf_website tcf_core
# Lint.
docker exec tcf_django pylint --jobs=0 --load-plugins pylint_django --django-settings-module=tcf_core.settings tcf_website tcf_core
docker exec tcf_django node_modules/.bin/eslint --cache --fix tcf_website/static/**/*.js -c .config/.eslintrc.yml
# Test.
docker exec tcf_django coverage run manage.py test --keepdb
# Get code coverage.
docker exec tcf_django coverage report -m
