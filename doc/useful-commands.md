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

See instructions in [grade-data.md](https://github.com/thecourseforum/theCourseForum2/blob/dev/doc/grade-data.md)


## Fetching and Loading Semester Data

See instructions in [semester-data.md](https://github.com/thecourseforum/theCourseForum2/blob/dev/doc/semester-data.md)

## Fetching Club Data

Fetch club data from virginia.presence.io API:

```console
$ docker exec -it tcf_django python manage.py fetch_clubs
```

Saved in `tcf_website/management/commands/club_data/csv`

See [fetch_clubs.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/fetch_clubs.py) for more information.

## Loading Club Data

Load club data from csv into database:

```console
$ docker exec -it tcf_django python manage.py load_clubs
```

See [load_clubs.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/load_clubs.py) for more information.

## Creating Production Database Backup

A backup of the prod database can be created with a script.
  - ***NOTE***: The prod_dump part of the .env must first be filled out (consult exec for access)
```console
$ scripts/prod_dump.sh
```
