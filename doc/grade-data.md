# Grade Data

## Fetching Grade Data

Instructions below fetch grade data from [IRA Grade Data Distribution](https://ira.virginia.edu/university-data-home/grade-distribution-last-5-years?check_logged_in=1)

### Before fetching grades
- Requires up-to-date semester data at `tcf_website/management/commands/semester_data/csv/year_season.csv`

### Fetching Grades
- Obtain grades for a semester, can be run locally:
```console
$ uv run python fetch_grades.py <year>_<season>
```

Output saved in `tcf_website/management/commands/grade_data/csv`

## Loading Grade Data

With the local Compose stack running, load grades into PostgreSQL with:

```console
$ docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```

For production, run the management command as a one-off ECS task with
`scripts/ecs-run-command.sh`; do not add it to the web container startup.


## Other useful commands

For other useful commands, see [useful-commands.md](useful-commands.md)
