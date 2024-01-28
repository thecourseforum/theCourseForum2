# Useful Commands

## Review Drive

Enable the review drive banner by reverting [this commit](https://github.com/thecourseforum/theCourseForum2/commit/c16383ff2b987dbfde127da97f5a280cb6e0a210) to include the HTML banner template.

## Picking Review Drive Winners

- Use Python via Django's builtin management shell:

```console
$ docker exec -it tcf_django python manage.py shell
```

- Select all relevant reviews:

```python
from random import sample
from tcf_website.models import *

# For example, the review drive tag for the Fall 2023 semester is `tCFF23`
# Consult marketing for exact semesterly drive tag
reviews = list(Review.objects.filter(text__icontains='<review drive tag>'))

# However many winners (consult marketing)
total_winners = 3

winners = reviews.order_by('?')[:total_winners]
```

- Finally, send all winners to the marketing team.

## Inspecting Production

To alter/inspect the production database directly, first use the production `.env.prod` credentials (consult exec for access). Then, either:

- Use Python via Django's builtin management shell:

```console
$ docker exec -it tcf_django python manage.py shell
```

- Use SQL and production credentials to dump the production database manually wherever desired (`db/prod.sql` is used by default):

```console
$ env $(cat .env.prod | grep -v '^#' | xargs) sh scripts/dump.sh
```

**_NOTE_**: Windows users won't be able to use the above CLI hack - substitute in the environment variables manually.

3. Remove production credentialing (use `.env` credentials like normal)

## Updating Grades

1. Build the project

- Switch to master
- Use production `.env.prod` credentials (consult exec for access)
- Build normally

2. Retrieve the latest semesterly grade data if required:

- Fetch the data from Lou's List (specify the year and season accordingly):

```
$ cd tcf_website/management/commands/semester_data
$ python fetch_data.py <year> {spring,summer,fall,january}
$ cd -
```

- If necessary, move the csv to `tcf_website/management/commands/grade_data/csv/<year>_<season>.csv`.

4. Load the recent data. See [load_grades.py](tcf_website/management/commands/load_grades.py) for info.

A normal update may look like the following:

```console
$ docker exec -it tcf_django python manage.py load_grades <year>_<season>.csv
```

5. Update ElasticSearch to reflect the latest database changes:

```
$ docker exec tcf_django python manage.py index_elasticsearch
```

**_NOTE_**: this command may take +1 hour(s) to run, so plan accordingly!

6. Commit the semesterly data to the repo
7. Remove production credentialing (use `.env` credentials like normal)
