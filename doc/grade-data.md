# Grade Data

## Fetching Grade Data

Instructions below fetch grade data from [IRA Grade Data Distribution](https://ira.virginia.edu/university-data-home/grade-distribution-last-5-years?check_logged_in=1)

### Before fetching grades
- `fetch_grades.py` (available in Google Drive `Engineering` folder) must be in *root* of repository
- Up-to-date semester data csv must be at `tcf_website/management/commands/semester_data/csv/year_season.csv`

### Fetching Grades
- Run this command to obtain grades for a semester:
```console
$ python fetch_grades.py <year>_<season>
```

Output saved in `tcf_website/management/commands/grade_data/csv`

## Loading Grade Data
- To load grades:
```console
$ python3 manage.py load_grades ALL_DANGEROUS
```
***NOTE***: For loading grades in production, add this command to container-startup.sh and remove after grade data is loaded into prod database


## Other useful commands

For other useful commands, see [useful-commands.md](useful-commands.md)
