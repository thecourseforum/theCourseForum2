# Grade Data

## Fetching Grade Data

Instructions below fetch grade data from [IRA Grade Data Distribution](https://ira.virginia.edu/university-data-home/grade-distribution-last-5-years?check_logged_in=1)

### Before fetching grades
- Requires up-to-date semester data at `tcf_website/management/commands/semester_data/csv/year_season.csv`.
  The grades themselves come from the FOIA app, but the semester file supplies the
  instructor names that match our `Instructor` rows; without it the command falls back
  to the registrar's legal names, which match fewer instructors.

### Fetching Grades
- Obtain grades for a semester, can be run locally:
```console
$ uv run python manage.py fetch_grades <year>_<season>
```

This queries the Qlik engine behind the FOIA page directly, so a full semester takes
about 20 seconds. It needs no credentials, no VPN and no browser. Pass `--min-rows N`
in automation so a term that comes back empty fails loudly instead of writing a
truncated CSV.

The previous Selenium scraper is kept as `old_grades` for use if the engine endpoint
ever stops serving anonymous sessions. It drives the page in a browser one section at
a time and takes roughly a day per semester:
```console
$ uv run python manage.py old_grades <year>_<season> [--resume]
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
