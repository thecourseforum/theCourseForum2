"""Check semester CSVs from fetch_data before load_semester loads them.

load_semester silently skips values it can't parse (Days -> no SectionTime,
Units -> 0 credits), so CI runs this on every semester CSV a PR adds or changes:

    uv run python -m tcf_website.management.semester_csv path/to/2027_spring.csv
"""

import csv
import re
import sys
from datetime import datetime

from tcf_website.management.commands.fetch_data import FIELDNAMES, MAX_MEETINGS

_CLOCK = r"(?:1[0-2]|[1-9]):[0-5]\d[ap]m"
# SIS day casing ("TuTh"), shown as-is on the site.
DAYS_PATTERN = re.compile(rf"TBA|(?:Mo|Tu|We|Th|Fr|Sa|Su)+ {_CLOCK} - {_CLOCK}")
UNITS_PATTERN = re.compile(r"\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?")
# load_semester drops rows missing any of these (and ClassNumber).
REQUIRED = ("Mnemonic", "Number", "Section")
WHOLE_NUMBERS = (
    "ClassNumber",
    "Enrollment",
    "EnrollmentLimit",
    "Waitlist",
    "WaitlistLimit",
)
MAX_REPORTED = 20


def is_meeting_dates(value):
    """True for "MM/DD/YYYY - MM/DD/YYYY" or "TBA"."""
    if value == "TBA":
        return True
    try:
        start, end = value.split(" - ")
        datetime.strptime(start, "%m/%d/%Y")
        datetime.strptime(end, "%m/%d/%Y")
    except ValueError:
        return False
    return True


def row_problems(row):
    """Return format problems in one CSV row (empty if it matches)."""
    problems: list[str] = [
        f"{column} is empty" for column in REQUIRED if not row[column]
    ]
    problems += [
        f"{column} {row[column]!r} is not a whole number"
        for column in WHOLE_NUMBERS
        if not row[column].isdigit()
    ]
    if row["Number"] and not re.search(r"\d", row["Number"]):
        problems.append(f"Number {row['Number']!r} has no digits")
    if not UNITS_PATTERN.fullmatch(row["Units"]):
        problems.append(f"Units {row['Units']!r} is not like '3' or '1 - 3'")
    for i in range(1, MAX_MEETINGS + 1):
        days, dates = row[f"Days{i}"], row[f"MeetingDates{i}"]
        if days and not DAYS_PATTERN.fullmatch(days):
            problems.append(
                f"Days{i} {days!r} is not like 'TuTh 2:00pm - 3:15pm' or 'TBA'"
            )
        if dates and not is_meeting_dates(dates):
            problems.append(
                f"MeetingDates{i} {dates!r} is not like "
                "'08/25/2026 - 12/08/2026' or 'TBA'"
            )
    return problems


def csv_problems(lines):
    """Return format problems in fetch_data CSV text (empty if it matches)."""
    reader = csv.DictReader(lines)
    header = set(reader.fieldnames or ())
    header_problems = [
        f"{label} columns: {sorted(columns)}"
        for label, columns in (
            ("missing", set(FIELDNAMES) - header),
            ("unexpected", header - set(FIELDNAMES)),
        )
        if columns
    ]
    if header_problems:
        return header_problems
    problems = []
    row_count = 0
    for row in reader:
        row_count += 1
        # DictReader pads short rows with None and keys extra fields under None.
        if None in row or None in row.values():
            problems.append(f"line {reader.line_num}: wrong number of fields")
            continue
        problems += [f"line {reader.line_num}: {p}" for p in row_problems(row)]
    return problems if row_count else ["no sections"]


def main(paths):
    """Print problems in each CSV; return 1 if any CSV has problems."""
    failed = False
    for path in paths:
        with open(path, newline="", encoding="utf-8") as csv_file:
            problems = csv_problems(csv_file)
        print(f"{path}: {len(problems) or 'no'} problems")
        for problem in problems[:MAX_REPORTED]:
            print(f"  {problem}")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
