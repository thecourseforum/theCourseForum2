import csv
import re
from pathlib import Path

GRADE_CSV_DIR = Path(__file__).resolve().parent / "commands" / "grade_data" / "csv"
SEMESTER_CSV_DIR = (
    Path(__file__).resolve().parent / "commands" / "semester_data" / "csv"
)
SEASON_DIGITS = {"january": "1", "spring": "2", "summer": "6", "fall": "8"}


def semester_number(path):
    match = re.fullmatch(r"(\d{4})_(january|spring|summer|fall)", path.stem)
    if not match:
        return None
    year, season = match.groups()
    return int(f"1{year[-2:]}{SEASON_DIGITS[season]}")


def load_grade_last_names(grade_dir=GRADE_CSV_DIR):
    last_names = {}
    for path in Path(grade_dir).glob("*.csv"):
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                name = row.get("Primary Instructor Name") or ""
                if name.count(",") != 1:
                    continue
                last, given = (" ".join(part.split()) for part in name.split(","))
                if last and given:
                    last_names.setdefault(given.split()[0].lower(), set()).add(last)
    return last_names


def split_instructor_name(full_name, grade_last_names=None):
    parts = " ".join((full_name or "").split()).split()
    if len(parts) < 2:
        return "", " ".join(parts)
    first_name = parts[0]
    lowered = " ".join(parts).lower()
    known = [
        last
        for last in (grade_last_names or {}).get(first_name.lower(), ())
        if len(last.split()) < len(parts) and lowered.endswith(" " + last.lower())
    ]
    if known:
        return first_name, max(known, key=len)
    return first_name, " ".join(parts[1:])
