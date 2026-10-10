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

The original fetcher is retained unchanged in
[fetch_data_old.py](../tcf_website/management/commands/fetch_data_old.py) for
benchmarking. Actual runtime depends on the semester and server response times.
Omitting the semester now defaults to the current semester, with progress bars.

SIS page-based requests supply all course and section fields; SIS attribute codes
map locally to CSV labels. HoosList is used **only for descriptions**, once per
unique course, with SIS fallback if HoosList fails. Past semesters use SIS
for descriptions by default because HoosList has no term parameter. HoosList
wording or spacing may differ from SIS.

Useful options:

- `--description-source sis` or `--description-source hooslist` overrides automatic source selection.
- `--json` also saves raw SIS search records beside the CSV; no JSON is written by default.
- `--output /tmp/courses.csv` selects another CSV destination.
- `--acad-org CS` or `--subjects CS` filters by academic organization or subject; filtered exports require `--output`.
- `--no-progress` disables progress bars.

There is no persistent cache, warmup, or CourseForum scraping. Requests retry up
to five times; exhausted SIS requests and unknown attribute codes stop the export.
Progress shows the page total after the first response and counts description
sources and SIS fallbacks. CSV retains the first four meetings, matching the
original; optional JSON retains all meetings. Files are written directly.

## Benchmark

Run [benchmark_fetch_data.py](../tcf_website/management/commands/benchmark_fetch_data.py)
as a standalone script from the project root inside the devcontainer:

```sh
uv run python tcf_website/management/commands/benchmark_fetch_data.py
```

Or, with the bundled `web` service running:

```sh
docker compose --profile full exec web python tcf_website/management/commands/benchmark_fetch_data.py
```

It compares the original, optimized with HoosList descriptions, and optimized with
SIS descriptions for Fall 2026, `acad_org=CS`. Each configuration runs once with no
warmups. Outputs go to the Git-ignored directory
`tcf_website/management/commands/semester_data/benchmark_data/` as `old.csv`,
`optimized-hooslist.csv`, and `optimized-sis.csv`; each run replaces these files.

The terminal summary reports timings, request counts excluding retries, and exact
CSV comparisons against the original, including capitalization and whitespace.
No comparison JSON is written. Both the fetcher and benchmark report elapsed
seconds and percentages for descriptions versus everything else, including retries
and SIS fallbacks. Concurrent durations are not added together. For the original,
class-detail requests count as description time even though they fetch other
fields too; overlapping requests count once.

When differences exist, `differences-hooslist.csv` and `differences-sis.csv` contain
one row per differing field, including missing/extra classes and fields:

- Class number, course, section, `DeviationType` (the field name), and `Change` (changed value or missing/extra class/field).
- `Difference`: `spacing`, `capitalization`, `spacing&capitalization`, or `other`; classification does not hide mismatches.
- `true_source`: the actual description provider (`sis` or `hooslist`), including fallbacks; other fields come from SIS.
- `OriginalHighlighted` and `DeviatedHighlighted`: full text with changed spans inside ⟦brackets⟧.
- `Original` and `Deviated`: the full, unchanged raw values as the last two columns.

Inside highlighted spans, · means space, ⍽ nonbreaking space, ↵ newline,
␍ carriage return, and ⇥ tab. Enable **Wrap Text** in Excel to read long cells;
the CSV uses UTF-8 with a BOM so Excel recognizes these characters.

Actual sources are tracked in memory during the benchmark without changing the
normal CSV schema. Re-comparing older exports without this metadata shows
`unknown` for descriptions. Clean comparisons remove stale differences files;
filenames follow the requested mode, such as `differences-auto.csv` for auto mode.
