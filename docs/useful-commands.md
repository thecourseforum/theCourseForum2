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

5. Commit the semesterly data to the repo
6. Remove production credentialing (use `.env` credentials like normal)

## Downloading Semester Data

Use the [fetch_data](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/fetch_data.py)
script to load data for a specified semester from the SIS API. The resulting CSV
is stored in `tcf_website/management/commands/semester_data/sis_csv`.
For example, loading the 2024 fall semester:

```sh
$ cd tcf_website/management/commands/
$ python fetch_data.py 2024_FALL
$ cd -
```

## Loading Semester Data

Load semester data from Lou's List (soon to be straight from the SIS API) using the provided Django management command:

```console
$ docker exec -it tcf_django python manage.py load_semester <year>_<season>
```

See [load_semester.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/load_semester.py) for more information.

## [Requesting Grade Data/FOIA Requests](docs/grade-data.md)

## Formatting the Codebase

Simply run the format script (a `.bat` file is available for Windows):

```console
$ sh scripts/format.sh
```
