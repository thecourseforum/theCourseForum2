# Semester Data

Use the workflow configured in the [developer guide](dev.md): the running bundled
Compose `web` service or the VS Code devcontainer. Run commands from the project
root, replacing `2026_fall` with the desired `<year>_<season>`.

## Fetching Semester Data

Download one semester CSV from thecourseforum/tCF-data on branch main. This does
not call SIS.

With the bundled `web` service running:

```sh
docker compose --profile full exec web python manage.py fetch_data 2026_fall
```

Inside the devcontainer:

```sh
uv run python manage.py fetch_data 2026_fall
```

Saved in `fetched/`.

Use the same environment for fetching and loading. The bundled `web` service
stores the CSV inside its container; the devcontainer writes to the mounted checkout.

See [fetch_data.py](../tcf_website/management/commands/fetch_data.py) for more information.

## Loading Semester Data

Delete existing semester data (if exists) and load new data from csv into database:

With the bundled `web` service running:

```sh
docker compose --profile full exec web python manage.py load_semester 2026_fall
```

Inside the devcontainer:

```sh
uv run python manage.py load_semester 2026_fall
```

In production, the daily Load course data Action (08:15 UTC) runs fetch then load
on a dedicated ECS task family `tcf-prod-load-course-data`. Manually:

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
