# Semester Data

Use the workflow configured in the [developer guide](dev.md): the running bundled
Compose `web` service or the VS Code devcontainer. Run commands from the project
root, replacing `2026_fall` with the desired `<year>_<season>`.

## Fetching Semester Data

Fetch semester data from SIS API (takes ~TBD to run):

With the bundled `web` service running:

```sh
docker compose --profile full exec web python manage.py fetch_data 2026_fall
```

Inside the devcontainer:

```sh
uv run python manage.py fetch_data 2026_fall
```

Saved in `tcf_website/management/commands/semester_data/csv`

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

See [load_semester.py](https://github.com/thecourseforum/theCourseForum2/blob/dev/tcf_website/management/commands/load_semester.py) for more information.

## Frequency

The semester data for a semester should be updated at least two times:
1. When the courses offered for following semester are released
   - Fall and Summer and Spring and January can typically be added around the same time
2. After the first day of classes of that semester

## Other useful commands

For other useful commands, see [useful-commands.md](https://github.com/thecourseforum/theCourseForum2/blob/dev/doc/useful-commands.md)

## Optimized fetcher notes

The Django command names remain unchanged. `fetch_data` now uses the optimized
implementation while preserving the semester argument, CSV columns and order,
output directory, and `<year>_<season>.csv` filename. Fetching still only writes
files; `load_semester` remains the separate database-loading step.


SIS page-based requests supply all course and section fields; SIS attribute codes
map locally to CSV labels. Unknown attribute codes trigger a SIS ClassDetails
lookup for that section's discipline and cost labels, with a separate section-field
progress bar. HoosList is used **only for descriptions**, once per
unique course, with SIS fallback if HoosList fails. Past semesters use SIS
for descriptions by default because HoosList has no term parameter. HoosList
wording or spacing may differ from SIS.

Useful options:

- `--description-source sis` or `--description-source hooslist` overrides automatic source selection.
- `--json` also saves raw SIS search records beside the CSV; no JSON is written by default.
- `--output /tmp/courses.csv` selects another CSV destination.
- `--acad-org CS` or `--subjects CS` filters by academic organization or subject; filtered fetches require `--output`.
- `--no-progress` disables progress bars.

There is no persistent cache, warmup, or CourseForum scraping. Requests retry up
to five times. If a SIS request still fails or SIS returns a malformed response,
`fetch_data` exits with an error and does not write a CSV.
Progress shows the page total after the first response and counts description
sources and SIS fallbacks. CSV retains the first four meetings, matching the
original; optional JSON retains all meetings. Files are written directly.

## Cloudflare bot protection

HoosList is protected by a Cloudflare managed challenge. A request that fails
the challenge receives a `403` response with a "Just a moment..." HTML page
instead of the course description. Whether a request is challenged depends on
the client and the network it is sent from.

Results observed in October 2026:

| Client                        | On eduroam | Off eduroam |
| ----------------------------- | ---------- | ----------- |
| Web browser                   | Passes     | Passes      |
| `curl` / `python-requests`    | Passes     | Blocked     |
| Selenium with headless Chrome | Passes     | Blocked     |
| Selenium with headed Chrome   | Passes     | Passes      |

### Effect on `fetch_data`

When HoosList blocks a request, `fetch_data` falls back to SIS for that
course's description. `403` responses are not retried, so a blocked run makes
one HoosList request and one SIS ClassDetails request per course, roughly
doubling the number of description requests. The summary at the end of the run
reports these as HoosList fallbacks.

SIS has also returned empty, non-JSON responses on some networks. Unlike a
HoosList block, this makes `fetch_data` exit with an error without writing a
CSV. Any existing CSV at the output path is left unchanged.

### Request volume

For Fall 2026 (9,717 sections and 2,971 unique courses), a full fetch makes:

- 98 SIS search requests (100 sections per page)
- 2,971 HoosList description requests
- one SIS ClassDetails request for each section with an unmapped attribute code
  and for each HoosList fallback
