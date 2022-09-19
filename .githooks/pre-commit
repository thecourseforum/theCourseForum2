#!/bin/sh

# List of files staged for commit
changing_files=`git diff --cached --name-status | awk '$1 != "D" { print $2 }'`
passing=true

# Autoformat (autopep8) and Pylint
if `echo $changing_files | grep -q .py` ; then
    echo 'Autoformatting...'
    docker exec tcf_django autopep8 --in-place --jobs=0 --max-line-length=100 --aggressive --aggressive -r tcf_website tcf_core
    git add $changing_files # Re-add files that got autoformatted
    echo 'Linting...'
    docker exec tcf_django pylint --jobs=0 -s no --load-plugins pylint_django --django-settings-module=tcf_core.settings tcf_website tcf_core || { echo 'ERROR: Pylint failed'; passing=false; }
else
    echo 'No Python files changed, skipping autoformat.'
    echo 'No Python files changed, skipping Pylint.'
fi

# ESLint
if `echo $changing_files | grep -q .js` ; then
    docker exec tcf_django node_modules/.bin/eslint --cache --fix -c .config/.eslintrc.yml tcf_website/static/ || { echo 'ERROR: ESLint failed'; passing=false; }
else
    echo 'No JavaScript files changed, skipping ESLint.'
fi

# Django tests
if `echo $changing_files | grep -q .py` ; then
    echo 'Running tests...'
    docker exec tcf_django coverage run manage.py test --keepdb || { echo 'ERROR: Django tests failed'; passing=false; }
else
    echo 'No Python files changed, skipping Django tests.'
fi

# Only commits if none of the checks failed, otherwise exits without committing
if [ "$passing" = true ] ; then
    echo 'Success!'
else
    echo 'One or more checks failed. Please fix and try committing again.'
    exit 1
fi
