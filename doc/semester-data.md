# Semester Data

## Fetching Semester Data

Fetch semester data from SIS API (~1.5-2 hours to run):

```console
$ docker exec -it tcf_django python manage.py fetch_data <year>_<season>
```

Saved in `tcf_website/management/commands/semester_data/csv`

See [fetch_data.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/fetch_data.py) for more information.

## Loading Semester Data

Delete existing semester data (if exists) and load new data from csv into database:

```console
$ docker exec -it tcf_django python manage.py load_semester <year>_<season>
```

See [load_semester.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/load_semester.py) for more information.

## Frequency

The semester data for a semester should be updated at least two times:
1. Before course enrollment for that semester opens 
2. After the first day of classes of that semester
