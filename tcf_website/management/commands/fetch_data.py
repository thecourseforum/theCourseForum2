"""Export SIS search pages with mapped attributes and course descriptions.

HoosList descriptions fall back to SIS; historical terms default to SIS.
The original implementation is preserved in fetch_data_old for benchmarking.
"""

import csv
import json
import os
import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import date
from datetime import time as time_of_day
from itertools import chain
from pathlib import Path
from threading import Event, Thread

import requests
from django.core.management.base import BaseCommand, CommandError
from tqdm import tqdm

from tcf_website.management.http import requests_session_with_pool_and_retries

TIMEOUT = 30
MAX_RETRIES = 5
MAX_MEETINGS = 4
SIS_URL = "https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula."
HOOSLIST_URL = "https://hooslist.virginia.edu/ClassSchedule/_GetCourseDescription"
SEASON_MAPPING = {"fall": 8, "summer": 6, "spring": 2, "january": 1}
COURSE_DATA_DIR = Path("tcf_website/management/commands/semester_data/csv")
FIELDNAMES = [
    "ClassNumber",
    "Mnemonic",
    "Number",
    "Section",
    "Type",
    "Units",
    *[
        f"{field}{i}"
        for i in range(1, MAX_MEETINGS + 1)
        for field in ("Instructor", "Days", "Room", "MeetingDates")
    ],
    "Title",
    "Topic",
    "Status",
    "Enrollment",
    "EnrollmentLimit",
    "Waitlist",
    "WaitlistLimit",
    "Description",
    "Disciplines",
    "Cost",
]
COMPONENT_MAPPING = {"LEC": "Lecture", "DIS": "Discussion", "LAB": "Laboratory"}
SECTION_MAPPING = {
    "ClassNumber": "class_nbr",
    "Mnemonic": "subject",
    "Number": "catalog_nbr",
    "Section": "class_section",
    "Type": "component",
    "Units": "units",
    "Title": "descr",
    "Topic": "topic",
    "Status": "enrl_stat_descr",
    "Enrollment": "enrollment_total",
    "EnrollmentLimit": "class_capacity",
    "Waitlist": "wait_tot",
    "WaitlistLimit": "wait_cap",
}
ATTRIBUTE_MAPPING = {  # Full labels verified against SIS ClassDetails. Unknown codes fail;
    "ASUD-AIP": "Artistic, Interpretive, & Philosophical Inquiry",
    "ASUD-CMP": "Chemical, Mathematical, and Physical Universe",
    "ASUD-CSW": "Cultures & Societies of the World",
    "ASUD-HP": "Historical Perspectives",
    "ASUD-LS": "Living Systems",
    "ASUD-QCD": "Quantification, Computation & Data Analysis",
    "ASUD-SS": "Science & Society",
    "ASUD-SES": "Social & Economic Systems",
    "ASUD-WL": "World Languages",
    "ASUW-WL": "World Languages",
    "ASUQ-QCD": "Quantification, Computation & Data Analysis",
    "ASUR-R21C1": "First Writing",
    "ASUR-R21C2": "Second Writing",
    "NCLC-NOCOST": "No Cost Course Materials",
    "NCLC-LOWCOST": "Low Cost Course Materials",
}
IGNORED_ATTRIBUTES = {  # Verified absent from SIS's exported class_attributes, despite appearing in search.
    "CORE-CRITTHINK",
    "CORE-ORALCOMM",
    "CORE-WRITTEN",
    "CORE-RESEARCH",
    "CORE-SCIENTIFIC",
    "CORE-QUANTITAT",
    "CORE-ABROAD",
    "ASUM-POST1800",
    "ASUM-PRE1800",
    "LAW-1LCORE",
    "LAW-1LCORESEM",
    "LAW-303C",
    "LAW-PROFETHIC",
    "LAW-PROFSKILL",
    "LAW-ULWR",
}


def create_session(cookie_file=None, user_agent=None, *, term=None):
    cookies = []
    if cookie_file:
        header = Path(cookie_file).read_text().strip().removeprefix("Cookie:").strip()
        if not header or "\n" in header or "\r" in header:
            raise ValueError("Cookie file must contain one raw Cookie header value.")
        for item in header.split(";"):
            name, separator, value = item.strip().partition("=")
            if not separator or not name:
                raise ValueError(
                    "Invalid cookie file; use the raw Cookie header value."
                )
            cookies.append((name, value))
    session = requests_session_with_pool_and_retries(
        workers=min(
            32, (os.cpu_count() or 1) + 4
        ),  # Match Python 3.12 executor defaults.
        status_forcelist=(429, 500, 502, 503, 504),
        retry_total=MAX_RETRIES,
    )
    if term is not None:
        session.params.update(institution="UVA01", term=term)
    if user_agent:
        session.headers["User-Agent"] = user_agent
    for name, value in cookies:
        session.cookies.set(
            name, value, domain="sisuva.admin.virginia.edu", path="/", secure=True
        )
    return session


def request_sis_json(session, endpoint, *, timeout=TIMEOUT, **params):
    response = session.get(
        SIS_URL + endpoint,
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    try:
        return response.json()
    except ValueError as exc:
        raise ValueError("SIS returned non-JSON data (possibly a login page).") from exc


def refresh_progress(bar, stopped):
    while not stopped.wait(1):
        bar.refresh()


@contextmanager
def live_progress(desc, unit, *, total=None, progress=False, progress_file=None):
    """Refresh elapsed time while network calls block, without advancing the count."""
    with tqdm(
        desc=desc,
        unit=unit,
        total=total,
        disable=not progress,
        file=progress_file,
        dynamic_ncols=True,
    ) as bar:
        stopped = Event()

        heartbeat = None
        if progress:
            heartbeat = Thread(
                target=refresh_progress, args=(bar, stopped), daemon=True
            )
            heartbeat.start()
        try:
            yield bar
        finally:
            stopped.set()
            if heartbeat:
                heartbeat.join()


def fetch_sis_courses(
    session,
    subjects=None,
    acad_org=None,
    *,
    timeout=TIMEOUT,
    progress=False,
    progress_file=None,
):
    courses = {}
    for subject in subjects or [None]:
        filters = {
            key: value
            for key, value in {
                "subject": subject.upper() if subject else None,
                "acad_org": acad_org,
            }.items()
            if value
        }
        subject_seen = set()
        with live_progress(
            desc=f"SIS pages ({subject or 'all subjects'})",
            unit="page",
            progress=progress,
            progress_file=progress_file,
        ) as bar:
            bar.set_postfix_str(
                "waiting for page 1; total unknown until first response"
            )
            first = request_sis_json(
                session, "IScript_ClassSearch", timeout=timeout, page=1, **filters
            )
            # Only the first response supplies the real total; later pages report 0.
            total_pages = int(first["pageCount"])
            if total_pages < 0 or bool(first["classes"]) != bool(total_pages):
                raise ValueError("SIS page count does not match its first page.")
            bar.total = total_pages
            remaining = (
                request_sis_json(
                    session,
                    "IScript_ClassSearch",
                    timeout=timeout,
                    page=page,
                    **filters,
                )
                for page in range(2, total_pages + 1)
            )
            pages = chain([first] if total_pages else [], remaining)
            for page, data in enumerate(pages, 1):
                records = {str(c["class_nbr"]): c for c in data["classes"]}
                if not records.keys() - subject_seen:
                    raise ValueError(
                        f"Empty or repeated SIS page {page}/{total_pages}."
                    )
                subject_seen.update(records)
                courses.update(records)
                bar.set_postfix_str(
                    f"{len(courses)} sections received"
                    + (
                        f"; waiting for page {page + 1}/{total_pages}"
                        if page < total_pages
                        else ""
                    ),
                    refresh=False,
                )
                bar.update(1)
    return list(courses.values())


def format_time(value):
    """Parse SIS clock times; datetime rejects malformed/out-of-range values."""
    return (
        time_of_day.fromisoformat(value.replace(".", ":", 2))
        .strftime("%I:%M%p")
        .lstrip("0")
        .lower()
        if value
        else ""
    )


def section_to_csv_row(course):
    """Convert a SIS record locally, without changing its fields."""
    codes = filter(None, map(str.strip, (course["crse_attr_value"] or "").split(",")))
    attributes = [
        (code, ATTRIBUTE_MAPPING[code])
        for code in codes
        if code not in IGNORED_ATTRIBUTES
    ]
    row = (
        dict.fromkeys(FIELDNAMES, "")
        | {column: course[key] for column, key in SECTION_MAPPING.items()}
        | {"Type": COMPONENT_MAPPING.get(course["component"], course["component"])}
        | {
            "Instructor1": ", ".join(
                i["name"] for i in course["instructors"] if i["name"] not in ("", "-")
            ),
            "Disciplines": "$".join(
                label for code, label in attributes if not code.startswith("NCLC-")
            ),
            "Cost": next(
                (
                    label
                    for code, label in reversed(attributes)
                    if code.startswith("NCLC-")
                ),
                "",
            ),
        }
    )
    for index, meeting in enumerate(course["meetings"][:MAX_MEETINGS], 1):
        instructor = " ".join(meeting["instructor"].split())
        days = meeting["days"]
        start, end = map(format_time, (meeting["start_time"], meeting["end_time"]))
        row.update(
            {
                f"Instructor{index}": "" if instructor == "-" else instructor,
                f"Room{index}": meeting["room"],
                f"MeetingDates{index}": (
                    f"{meeting['start_dt']} - {meeting['end_dt']}"
                    if meeting["start_dt"] and meeting["end_dt"]
                    else ""
                ),
                f"Days{index}": (
                    "TBA"
                    if days in ("TBA", "-")
                    else (f"{days} {start} - {end}" if days and start and end else "")
                ).lower(),
            }
        )
    return row


def current_season():
    month = date.today().month
    return "fall" if month >= 8 else "summer" if month >= 5 else "spring"


def course_key(term, course):
    return (
        term,
        course["subject"],
        course["catalog_nbr"],
        str(course["crse_id"]),
        str(course["crse_offer_nbr"]),
    )


def fetch_sis_description(session, course, timeout):
    data = request_sis_json(
        session,
        "IScript_ClassDetails",
        timeout=timeout,
        class_nbr=course["class_nbr"],
    )
    section_info = data.get("section_info") or {}
    catalog_descr = section_info.get("catalog_descr") or {}
    text = catalog_descr.get("crse_catalog_description")
    return text if text and text.strip() else ""


def fetch_hooslist_description(hoos_session, course, timeout):
    response = hoos_session.get(
        HOOSLIST_URL,
        params={
            "subject": course["subject"],
            "courseNum": course["catalog_nbr"],
        },
        timeout=timeout,
    )
    response.raise_for_status()
    text = response.text
    if (
        "text/plain" not in response.headers.get("Content-Type", "").lower()
        or not text.strip()
        or "<html" in text.lower()
        or "<!doctype" in text.lower()
    ):
        raise ValueError("HoosList returned an empty or non-text description.")
    return text


def fetch_course_description(course, sis_session, hoos_session, source, timeout):
    """HoosList descriptions are the only permitted source fallback."""
    failed = False
    if source == "hooslist":
        try:
            desc = fetch_hooslist_description(hoos_session, course, timeout)
            true_source = "hooslist"
        except (requests.RequestException, ValueError):
            failed = True
    if source != "hooslist" or failed:
        desc = fetch_sis_description(sis_session, course, timeout)
        true_source = "sis"

    return desc.replace("\n", "").replace("\r", " "), true_source


def fetch_descriptions(
    courses,
    sis_session,
    term,
    *,
    source="auto",
    timeout=TIMEOUT,
    progress=False,
    progress_file=None,
):
    """Download each unique course description; report its actual source."""
    if source == "auto":
        current_term = (
            f"1{date.today().year % 100:02d}{SEASON_MAPPING[current_season()]}"
        )
        source = "sis" if int(term) < int(current_term) else "hooslist"
    if source not in {"sis", "hooslist"}:
        raise ValueError(f"Unknown description source: {source}")
    unique = {course_key(term, c): c for c in courses}
    descriptions, sources = {}, Counter()
    true_sources = {}
    with (
        create_session() as hoos_session,
        ThreadPoolExecutor() as pool,
    ):
        futures = {
            pool.submit(
                fetch_course_description,
                c,
                sis_session,
                hoos_session,
                source,
                timeout,
            ): key
            for key, c in unique.items()
        }
        with live_progress(
            total=len(unique),
            desc="Descriptions",
            unit="course",
            progress=progress,
            progress_file=progress_file,
        ) as bar:
            try:
                for future in as_completed(futures):
                    text, actual_source = future.result()
                    descriptions[futures[future]] = text
                    true_sources[futures[future]] = actual_source
                    sources[actual_source] += 1
                    bar.set_postfix(
                        hoos=sources["hooslist"],
                        sis_downloads=sources["sis"],
                        sis_fallbacks=sources["sis"] if source == "hooslist" else 0,
                        refresh=False,
                    )
                    bar.update(1)
            except BaseException:
                for future in futures:
                    future.cancel()
                raise
    return descriptions, {
        "unique_courses": len(unique),
        "description_fallbacks": sources["sis"] if source == "hooslist" else 0,
        "description_sis_downloads": sources["sis"],
        "descriptions": dict(sources),
        "true_sources": true_sources,
    }


class Command(BaseCommand):
    help = "Fetch SIS pages, map attributes and enrich course descriptions"
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            "semester",
            nargs="?",
            help="Optional <year>_<season>; defaults to the current semester",
        )
        parser.add_argument("--subjects", nargs="+", help="Filter by subject codes")
        parser.add_argument("--output", type=Path, help="CSV output path")
        parser.add_argument(
            "--json",
            action="store_true",
            help="Also save raw SIS records beside the CSV",
        )
        parser.add_argument(
            "--description-source",
            choices=("auto", "hooslist", "sis"),
            default="auto",
            help="Auto: SIS for past terms, HoosList otherwise",
        )
        parser.add_argument(
            "--no-progress", action="store_true", help="Disable progress bars"
        )
        parser.add_argument(
            "--timeout", type=float, default=TIMEOUT, help="HTTP timeout in seconds"
        )
        parser.add_argument("--acad-org", help="Filter by academic organization")
        parser.add_argument("--cookie-file", type=Path, help="SIS Cookie header file")
        parser.add_argument("--user-agent", help="Browser User-Agent")

    def handle(self, *args, **options):
        semester = options.get("semester")
        if semester is None:
            semester = f"{date.today().year}_{current_season()}"
        match = re.fullmatch(r"(\d{4})_(fall|summer|spring|january)", semester.lower())
        if not match:
            raise CommandError("Use <year>_<season>, e.g. 2026_fall.")
        if options["timeout"] <= 0:
            raise CommandError("--timeout must be positive.")
        year, season = match.groups()
        self.stdout.write(f"Fetching {season.title()} {year}.")
        term = f"1{year[-2:]}{SEASON_MAPPING[season]}"
        if (options["subjects"] or options.get("acad_org")) and not options["output"]:
            raise CommandError(
                "Use --output with --subjects or --acad-org to keep partial exports separate."
            )
        output = options["output"] or COURSE_DATA_DIR / f"{year}_{season}.csv"
        if output.suffix.lower() != ".csv":
            raise CommandError("--output must end in .csv.")
        start = time.monotonic()
        request_options = {
            "timeout": options["timeout"],
            "progress": not options.get("no_progress", False),
            # Django's output wrapper adds newlines that break tqdm redraws.
            "progress_file": self.stderr._out,
        }
        try:
            with create_session(
                options.get("cookie_file"), options.get("user_agent"), term=term
            ) as session:
                courses = fetch_sis_courses(
                    session,
                    options["subjects"],
                    options.get("acad_org"),
                    **request_options,
                )
                if not courses:
                    raise CommandError(
                        "SIS returned no sections; existing files were kept."
                    )
                output.parent.mkdir(parents=True, exist_ok=True)
                if options.get("json"):
                    output.with_suffix(".json").write_text(
                        json.dumps(courses, indent=2), encoding="utf-8"
                    )
                overflow = sum(len(c["meetings"]) > MAX_MEETINGS for c in courses)
                if overflow:
                    self.stderr.write(
                        self.style.WARNING(
                            f"{overflow} sections exceed {MAX_MEETINGS} meetings. CSV keeps "
                            f"the first {MAX_MEETINGS}. The optional --json export preserves all meetings."
                        )
                    )
                self.stdout.write(
                    f"Processing {len(courses):,} sections and "
                    f"{len({course_key(term, c) for c in courses}):,} unique courses."
                )
                rows = list(map(section_to_csv_row, courses))
                description_start = time.monotonic()
                descriptions, stats = fetch_descriptions(
                    courses,
                    session,
                    term,
                    source=options["description_source"],
                    **request_options,
                )
                self.description_seconds = time.monotonic() - description_start
                self.description_sources = {
                    str(course["class_nbr"]): stats["true_sources"][
                        course_key(term, course)
                    ]
                    for course in courses
                }
                rows = [
                    row | {"Description": descriptions[course_key(term, course)]}
                    for course, row in zip(courses, rows, strict=True)
                ]
                with output.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    writer.writerows(rows)
        except KeyboardInterrupt:
            raise CommandError("Fetch cancelled.") from None
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
            OSError,
        ) as exc:
            raise CommandError(f"Fetch failed: {exc}") from exc
        elapsed = time.monotonic() - start
        description_percent = 100 * self.description_seconds / elapsed if elapsed else 0
        self.stdout.write(
            f"Descriptions: {stats['unique_courses']} courses; "
            f"{stats['descriptions'].get('hooslist', 0)} from HoosList, "
            f"{stats['description_sis_downloads']} from SIS "
            f"({stats['description_fallbacks']} HoosList fallbacks)."
        )
        self.stdout.write(
            f"Time spent: descriptions {self.description_seconds:.1f}s "
            f"({description_percent:.1f}%); everything else "
            f"{elapsed - self.description_seconds:.1f}s ({100 - description_percent:.1f}%)."
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Saved {len(rows)} sections to {output} in {elapsed:.1f}s"
            )
        )
        if options.get("json"):
            self.stdout.write(f"Saved raw SIS records to {output.with_suffix('.json')}")
