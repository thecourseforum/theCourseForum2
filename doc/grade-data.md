# Grade Data

## Fetching Grade Data

Instructions below fetch grade data from [IRA Grade Data Distribution](https://ira.virginia.edu/university-data-home/grade-distribution-last-5-years?check_logged_in=1)

### Before fetching grades
- Optional but recommended: up-to-date semester data at
  `tcf_website/management/commands/semester_data/csv/year_season.csv`.
  The grades themselves come from the FOIA app. When the semester file is present the
  command prefers its instructor names, which match more of our `Instructor` rows than
  the registrar's legal names do. Without it the command prints a warning and uses the
  legal names.

### Fetching Grades
- Obtain grades for a semester, can be run locally:
```console
$ uv run python manage.py fetch_grades <year>_<season>
```

This queries the Qlik engine behind the FOIA page directly. It takes less than 1 minute to run. Pass `--min-rows N` in automation to reject a
term that comes back with fewer sections than expected. Pass `--output PATH` to
write somewhere other than the default.

Output saved by default in `tcf_website/management/commands/grade_data/csv`

## Loading Grade Data

With the local Compose stack running, load grades into PostgreSQL with:

```console
$ docker compose --profile full exec web python manage.py load_grades ALL_DANGEROUS
```
***NOTE***: For loading grades in production, use `load_grades` with ecs-run-command.sh


## Other useful commands

For other useful commands, see [useful-commands.md](useful-commands.md)
