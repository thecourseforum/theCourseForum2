# Grade Data

## Fetching Grade Data

Fetch grade data from [IRA Grade Data Distribution](https://ira.virginia.edu/university-data-home/grade-distribution-last-5-years?check_logged_in=1)

### Requirements
- `fetch_grades.py` (available in Google Drive) must be in *root* of repository
- Semester data csv for semester must be in `tcf_website/management/commands/semester_data/csv`

```console
$ python fetch_grades.py <year>_<season>
```

Saved in `tcf_website/management/commands/grade_data/csv`

## Updating Grade Data

See **Updating Grades** in [useful-commands.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/doc/useful-commands.md)

# Prior Method (No longer works as of Feb. 2026)

***The University has stopped providing grade data requested via FOIA as of Feb. 2026.*** However, the below method *may* work with prodding.

The Freedom of Information Act allows us to request records from UVA, which is how we get our grades data. Follow these steps:

1. Go to https://universitycounsel.virginia.edu/foia/request-records
2. Click "Submit a FOIA request," creating an account as necessary.
3. In "Describe the Record(s) Requested", enter the following:

- I am a member of theCourseForum, a student-run team and registered CIO that maintains the top course review site at UVA. We use these grades to provide a free online outlet for students to get the best information on their classes as they navigate course registration. I am requesting the grades for all classes at UVA for `(semester here)`. I am aware that it is available online at https://ira.virginia.edu/university-data-home, but this data does not have a link for export and is thus insufficient for my purposes. Let me know if there is anything I need to do to facilitate this process.

4. Select "Electronic via Records Center" as preferred method and "Status as FOIA requester" to UVA Student
5. You should receive an email within a few days, or you can check status under "View My Requests"

One note: the data will come with the following redactions:
![image](https://user-images.githubusercontent.com/55100084/111021403-f777f180-8399-11eb-85cd-d1bbab710438.png)

## Splitting Data

If you request multiple semesters' worth of data in a single request, you can use `tcf_website/management/commands/grade_data/split_data.py` to divide it into individual `.csv` files. The script uses hardcoded files, but it should be pretty straightforward to adapt it to your needs.
