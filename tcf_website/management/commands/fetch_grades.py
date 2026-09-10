"""
Fetch Grade Data from UVA's FOIA Grade Distribution Qlik app.

The public FOIA page at TARGET_URL is a thin Qlik Sense mashup whose engine
accepts anonymous WebSocket sessions, so this queries that engine directly
instead of driving the page in a browser. A whole term is two hypercube
queries rather than one browser round-trip per section, and needs no
credentials, no VPN and no Chrome.

The semester file for the term is optional. When it is present its instructor
names are preferred, because they match more Instructor rows than the
registrar's legal names do; without it the command warns and uses the legal
names. See doc/grade-data.md.

USAGE:
    uv run python manage.py fetch_grades 2024_fall
    uv run python manage.py fetch_grades 2024_fall --min-rows 500
    uv run python manage.py fetch_grades 2024_fall --output /tmp/check.csv

OUTPUT:
    Creates: tcf_website/management/commands/grade_data/csv/<year>_<season>.csv
"""

import json
import os
import re
from collections import defaultdict

import pandas as pd
import requests
import websocket
from django.core.management.base import BaseCommand, CommandError

HOST = "qlksnpn-apprd01.eservices.virginia.edu"
TARGET_URL = (
    f"https://{HOST}/extensions/FOIAGradeDistribution/FOIAGradeDistribution.html"
)
MASHUP_JS_URL = (
    f"https://{HOST}/extensions/FOIAGradeDistribution/FOIAGradeDistribution.js"
)

# App GUID is read off the mashup JS at runtime so a change on UVA's side
# surfaces as a clear error rather than an empty CSV. This is the fallback.
FALLBACK_APP_ID = "7fc7c70d-021f-4de0-9efc-97e4f8806e59"

TIMEOUT = 120
MAX_CELLS = 10000

GRADE_DATA_DIR = "tcf_website/management/commands/grade_data/csv"
SEMESTER_DATA_DIR = "tcf_website/management/commands/semester_data/csv"

SEASON_NAMES = {
    "fall": "Fall",
    "spring": "Spring",
    "summer": "Summer",
    "january": "January",
}

# Grade buckets published by the FOIA app, in load_grades column order.
GRADE_COLUMNS = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "DFW"]

# Output CSV columns (must match load_grades.py expectations)
OUTPUT_COLUMNS = [
    "Term Desc",
    "Subject",
    "Catalog Number",
    "Class Title",
    "Course ID",
    "Primary Instructor Name",
    "Class Section",
    "Class Num",
    "Class Academic Group",
    "Course GPA",
    "# of Students",
    *GRADE_COLUMNS,
]

# Expressions lifted from the app's own chart definitions so the numbers match
# what the FOIA page publishes.
STUDENT_COUNT = "Count(distinct [Student System ID])"
COURSE_GPA = (
    'Avg({< [Student Enrollment Status]={"Enrolled"},'
    '[Official Grade]={"A", "A+", "A-", "B", "B+", "B-", '
    '"C", "C+", "C-", "D", "D+", "D-", "F"}>}'
    "[Grade Points]/[Units Earned])"
)

# Let the engine round the GPA so the value matches what the FOIA page shows
# rather than reimplementing Qlik's rounding.
GPA_NUM_FORMAT = {
    "qType": "F",
    "qnDec": 2,
    "qUseThou": 0,
    "qFmt": "#,##0.00",
    "qDec": ".",
    "qThou": ",",
}

# Let the engine round the GPA so the value matches what the FOIA page shows
# rather than reimplementing Qlik's rounding.
GPA_NUM_FORMAT = {
    "qType": "F",
    "qnDec": 2,
    "qUseThou": 0,
    "qFmt": "#,##0.00",
    "qDec": ".",
    "qThou": ",",
}

SECTION_DIMENSIONS = [
    "Class Num",
    "Subject",
    "Catalog Number",
    "Class Section",
    "Class Title",
    "=[Class Academic Group Desc]",
    "Primary Instructor Name",
    "Course ID",
]


class QlikEngine:
    """Minimal JSON-RPC client for the Qlik Engine API over WebSocket."""

    def __init__(self, app_id):
        self.app_id = app_id
        self.request_id = 0
        self.socket = websocket.create_connection(
            f"wss://{HOST}/app/{app_id}",
            origin=f"https://{HOST}",
            timeout=TIMEOUT,
        )
        self.doc = self.call(-1, "OpenDoc", {"qDocName": app_id})["qReturn"]["qHandle"]

    def call(self, handle, method, params):
        """Send one JSON-RPC request and return its result payload."""
        self.request_id += 1
        self.socket.send(
            json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": self.request_id,
                    "handle": handle,
                    "method": method,
                    "params": params,
                }
            )
        )
        while True:
            message = json.loads(self.socket.recv())
            if message.get("id") != self.request_id:
                continue
            if "error" in message:
                raise CommandError(f"Qlik {method} failed: {message['error']}")
            return message["result"]

    def select(self, field, value):
        """Apply a single-value selection to a field. Returns True if it stuck."""
        handle = self.call(self.doc, "GetField", {"qFieldName": field})["qReturn"][
            "qHandle"
        ]
        return self.call(handle, "Select", {"qMatch": value, "qSoftLock": False})[
            "qReturn"
        ]

    def field_values(self, field):
        """Return every value of a field paired with its selection state."""
        properties = {
            "qInfo": {"qType": "tcf-fetch-grades-list"},
            "qListObjectDef": {
                "qDef": {"qFieldDefs": [field]},
                "qInitialDataFetch": [
                    {"qTop": 0, "qLeft": 0, "qHeight": MAX_CELLS, "qWidth": 1}
                ],
            },
        }
        handle = self.call(self.doc, "CreateSessionObject", {"qProp": properties})[
            "qReturn"
        ]["qHandle"]
        layout = self.call(handle, "GetLayout", {})["qLayout"]["qListObject"]
        return [
            (cell.get("qText"), cell.get("qState"))
            for page in layout.get("qDataPages", [])
            for row in page.get("qMatrix", [])
            for cell in row
        ]

    def hypercube(self, dimensions, measures):
        """Build a session hypercube and page through every row of it."""
        properties = {
            "qInfo": {"qType": "tcf-fetch-grades"},
            "qHyperCubeDef": {
                "qDimensions": [
                    {"qDef": {"qFieldDefs": [d]}, "qNullSuppression": False}
                    for d in dimensions
                ],
                "qMeasures": [
                    {"qDef": {"qDef": m, "qNumFormat": GPA_NUM_FORMAT}}
                    if m == COURSE_GPA
                    else {"qDef": {"qDef": m}}
                    for m in measures
                ],
                "qInitialDataFetch": [],
                "qSuppressZero": True,
                "qMode": "S",
            },
        }
        handle = self.call(self.doc, "CreateSessionObject", {"qProp": properties})[
            "qReturn"
        ]["qHandle"]
        size = self.call(handle, "GetLayout", {})["qLayout"]["qHyperCube"]["qSize"]
        width, height = size["qcx"], size["qcy"]

        rows = []
        top = 0
        while top < height:
            page = {
                "qTop": top,
                "qLeft": 0,
                "qHeight": min(MAX_CELLS // width, height - top),
                "qWidth": width,
            }
            matrix = self.call(
                handle,
                "GetHyperCubeData",
                {"qPath": "/qHyperCubeDef", "qPages": [page]},
            )["qDataPages"][0]["qMatrix"]
            if not matrix:
                break
            rows.extend([cell.get("qText") for cell in row] for row in matrix)
            top += len(matrix)
        return rows

    def close(self):
        self.socket.close()


def resolve_app_id():
    """Read the production app GUID out of the mashup JS, falling back to the
    last known value if the page cannot be reached or its shape has changed."""
    try:
        response = requests.get(MASHUP_JS_URL, timeout=30)
        response.raise_for_status()
    except requests.RequestException:
        return FALLBACK_APP_ID

    pattern = rf"{re.escape(HOST)}'.*?openApp\(\s*'([0-9a-f-]{{36}})'"
    match = re.search(pattern, response.text, re.DOTALL)
    return match.group(1) if match else FALLBACK_APP_ID


def clean_text(text):
    """Collapse the runs of whitespace UVA leaves in titles."""
    return re.sub(r"\s+", " ", text or "").strip()


def is_tba_instructor(name):
    """True when SIS/FOIA used a placeholder instead of a real instructor.

    Recent term files use "To be Announced" (lowercase b); older files used
    "To Be Announced". Compare case-insensitively so both are dropped.
    """
    return clean_text(name).casefold() == "to be announced"


def format_sis_name(name):
    """Convert the semester file's "First Last" to "Last,First".

    Same transformation the legacy scraper applied, so the names in the
    output keep matching the Instructor rows load_grades looks them up in.
    """
    name = clean_text(name)
    if not name or is_tba_instructor(name):
        return "..."
    parts = name.split(",")[0].strip().split()
    if len(parts) < 2:
        return "..."
    return f"{parts[-1]},{' '.join(parts[:-1])}"


def format_engine_name(name):
    """Normalise the engine's instructor name.

    The engine already publishes "Last,First", so this only rejects the
    placeholders. load_grades splits on that single comma and drops rows
    marked "...", so anything not in that shape becomes "...".
    """
    name = clean_text(name)
    if name.count(",") != 1 or is_tba_instructor(name):
        return "..."
    return name


def load_sis_instructors(semester_csv):
    """Map class number to instructor name from the semester file.

    The FOIA app reports the registrar's legal name ("Kreindler,Katharine
    Rachel"), while our Instructor rows come from SIS and carry preferred
    names ("Kreindler,Kate"), so preferring SIS here keeps load_grades'
    name lookup hitting. Returns an empty map if the file is absent.
    """
    if not os.path.exists(semester_csv):
        return {}
    dataframe = pd.read_csv(semester_csv, dtype=str).fillna("")
    return {
        str(row["ClassNumber"]).strip(): format_sis_name(row["Instructor1"])
        for _, row in dataframe.iterrows()
        if str(row.get("ClassNumber", "")).strip()
    }


def pick_instructor(sis_name, engine_name):
    """Prefer the SIS name, falling back to the engine's for sections the
    semester file does not cover."""
    if sis_name and sis_name != "...":
        return sis_name
    return format_engine_name(engine_name)


def build_rows(term, sections, grades, sis_instructors):
    """Join the per-section metadata cube to the per-grade counts cube."""
    counts = defaultdict(dict)
    for class_num, grade, count in grades:
        if grade in GRADE_COLUMNS:
            try:
                counts[class_num][grade] = int(count)
            except (TypeError, ValueError):
                counts[class_num][grade] = 0

    rows = {}
    for (
        class_num,
        subject,
        catalog_number,
        class_section,
        class_title,
        academic_group,
        instructor,
        course_id,
        students,
        gpa,
    ) in sections:
        # Co-taught sections repeat the class number once per instructor;
        # keep the first, which is what the legacy scraper recorded.
        if class_num in rows:
            continue
        row = {
            "Term Desc": term,
            "Subject": clean_text(subject),
            "Catalog Number": clean_text(catalog_number),
            "Class Title": clean_text(class_title),
            "Course ID": clean_text(course_id),
            "Primary Instructor Name": pick_instructor(
                sis_instructors.get(class_num.strip()), instructor
            ),
            "Class Section": clean_text(class_section),
            "Class Num": class_num,
            "Class Academic Group": clean_text(academic_group),
            "Course GPA": clean_text(gpa),
            "# of Students": clean_text(students),
        }
        for grade in GRADE_COLUMNS:
            row[grade] = counts[class_num].get(grade, 0)
        rows[class_num] = row

    return list(rows.values())


class Command(BaseCommand):
    """Pull a term of FOIA grade data straight from the Qlik engine."""

    help = "Fetch FOIA grade data for one semester into grade_data/csv"

    def add_arguments(self, parser):
        parser.add_argument(
            "semester", help="Semester in format: <year>_<season> (e.g., 2024_fall)"
        )
        parser.add_argument(
            "--min-rows",
            type=int,
            default=1,
            help="Fail if fewer than this many sections come back (guards "
            "against silently writing an empty CSV in automation)",
        )
        parser.add_argument(
            "--output",
            default=None,
            help="Override the output CSV path",
        )

    def handle(self, *args, **options):
        parts = options["semester"].split("_")
        if len(parts) != 2:
            raise CommandError(
                f"Invalid semester format '{options['semester']}'. "
                "Expected format: <year>_<season> (e.g., 2024_fall)"
            )

        year, season = parts[0], parts[1].lower()

        if not year.isdigit() or len(year) != 4:
            raise CommandError(f"Invalid year '{year}'")
        if season not in SEASON_NAMES:
            raise CommandError(
                f"Invalid season '{season}'. "
                f"Valid options: {', '.join(SEASON_NAMES.keys())}"
            )

        term = f"{year} {SEASON_NAMES[season]}"
        output_csv = options["output"] or os.path.join(
            GRADE_DATA_DIR, f"{year}_{season}.csv"
        )

        app_id = resolve_app_id()
        self.stdout.write(f"Connecting to Qlik app {app_id}...")
        engine = QlikEngine(app_id)

        try:
            engine.select("Term Desc", term)

            values = engine.field_values("Term Desc")
            selected = sorted(text for text, state in values if state == "S")
            if selected != [term]:
                available = ", ".join(sorted(text for text, _ in values))
                raise CommandError(
                    f"Term '{term}' is not available in the FOIA app. "
                    f"Available terms: {available or '(none)'}. "
                    "Grades for a semester are published some weeks after it ends."
                )

            self.stdout.write(f"Fetching sections for {term}...")
            sections = engine.hypercube(SECTION_DIMENSIONS, [STUDENT_COUNT, COURSE_GPA])

            self.stdout.write("Fetching grade distributions...")
            grades = engine.hypercube(["Class Num", "FOIA Grade"], [STUDENT_COUNT])
        finally:
            engine.close()

        semester_csv = os.path.join(SEMESTER_DATA_DIR, f"{year}_{season}.csv")
        sis_instructors = load_sis_instructors(semester_csv)
        if not sis_instructors:
            self.stdout.write(
                self.style.WARNING(
                    f"No semester file at {semester_csv}; falling back to the "
                    "FOIA app's legal names, which match fewer Instructor rows."
                )
            )

        rows = build_rows(term, sections, grades, sis_instructors)
        self.stdout.write(f"Got {len(rows)} sections from {len(grades)} grade rows")

        if len(rows) < options["min_rows"]:
            raise CommandError(
                f"Only {len(rows)} sections returned, expected at least "
                f"{options['min_rows']}. Refusing to write {output_csv}."
            )

        dataframe = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
        os.makedirs(os.path.dirname(output_csv) or ".", exist_ok=True)
        dataframe.to_csv(output_csv, index=False)

        self.stdout.write(self.style.SUCCESS(f"Saved {len(rows)} rows to {output_csv}"))
