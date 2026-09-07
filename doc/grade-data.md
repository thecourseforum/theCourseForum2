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
- To load grades, run _in the docker container_:
```console
$ python manage.py load_grades ALL_DANGEROUS
```
***NOTE***: For loading grades in production, add this command to container-startup.sh and remove after grade data is loaded into prod database


## Other useful commands

For other useful commands, see [useful-commands.md](useful-commands.md)
