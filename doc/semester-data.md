# (Deprecated) Semester Data

> This guide is deprecated for the new compose stack.

## Fetching Semester Data

Download one semester CSV from thecourseforum/tCF-data on branch main. This does not call SIS:

```console
$ docker exec -it tcf_django python manage.py fetch_data <year>_<season>
```

Saved in `fetched/`.

See [fetch_data.py](../tcf_website/management/commands/fetch_data.py) for more information.

## Loading Semester Data

Delete existing semester data (if exists) and load new data from csv into database:

```console
$ docker exec -it tcf_django python manage.py load_semester <year>_<season>
```

In production, the daily Load course data Action (08:15 UTC) runs fetch then load
on a dedicated ECS task family `tcf-load-course-data`. Manually:

```bash
./scripts/ecs-load-course-data.sh
./scripts/ecs-load-course-data.sh 2026_fall
```

See [load_semester.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/load_semester.py) for more information.

## Frequency

The semester data for a semester should be updated at least two times:
1. When the courses offered for following semester are released
   - Fall and Summer and Spring and January can typically be added around the same time
2. After the first day of classes of that semester

## Other useful commands

For other useful commands, see [useful-commands.md](https://github.com/thecourseforum/theCourseForum2/blob/dev/doc/useful-commands.md)
