"""Tests for the semester CSV check CI runs on fetched course data."""

import csv
from io import StringIO

from django.test import SimpleTestCase

from tcf_website.management.commands.fetch_data import FIELDNAMES
from tcf_website.management.semester_csv import csv_problems

VALID_ROW = dict.fromkeys(FIELDNAMES, "") | {
    "ClassNumber": "12345",
    "Mnemonic": "CS",
    "Number": "2150",
    "Section": "001",
    "Units": "1 - 3",
    "Days1": "MoWeFr 11:00am - 11:50am",
    "MeetingDates1": "08/25/2026 - 12/08/2026",
    "Days2": "TBA",
    "MeetingDates2": "TBA",
    "Enrollment": "100",
    "EnrollmentLimit": "150",
    "Waitlist": "0",
    "WaitlistLimit": "50",
}


def as_csv(*rows, fieldnames=FIELDNAMES):
    """Write rows the way fetch_data does, ready to read back."""
    out = StringIO()
    writer = csv.DictWriter(out, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    out.seek(0)
    return out


class SemesterCsvTests(SimpleTestCase):
    """csv_problems accepts fetch_data's format and names what breaks it."""

    def test_valid_csv_passes(self):
        self.assertEqual(csv_problems(as_csv(VALID_ROW)), [])

    def test_lowercase_days_fail(self):
        row = VALID_ROW | {"Days1": "mowefr 11:00am - 11:50am"}

        self.assertEqual(
            csv_problems(as_csv(row)),
            [
                "line 2: Days1 'mowefr 11:00am - 11:50am' is not like "
                "'TuTh 2:00pm - 3:15pm' or 'TBA'"
            ],
        )

    def test_bad_dates_and_numbers_fail(self):
        row = VALID_ROW | {"MeetingDates1": "08/25/2026", "Enrollment": "", "Units": ""}

        self.assertEqual(
            csv_problems(as_csv(row)),
            [
                "line 2: Enrollment '' is not a whole number",
                "line 2: Units '' is not like '3' or '1 - 3'",
                "line 2: MeetingDates1 '08/25/2026' is not like "
                "'08/25/2026 - 12/08/2026' or 'TBA'",
            ],
        )

    def test_header_mismatch_fails(self):
        fieldnames = [f for f in FIELDNAMES if f != "WaitlistLimit"] + ["Extra"]

        self.assertEqual(
            csv_problems(as_csv(VALID_ROW, fieldnames=fieldnames)),
            ["missing columns: ['WaitlistLimit']", "unexpected columns: ['Extra']"],
        )

    def test_wrong_field_count_fails(self):
        lines = as_csv(VALID_ROW).getvalue().splitlines()
        short_row = lines[1].rsplit(",", 1)[0]

        self.assertEqual(
            csv_problems([lines[0], short_row, lines[1] + ",extra"]),
            ["line 2: wrong number of fields", "line 3: wrong number of fields"],
        )

    def test_empty_csv_fails(self):
        self.assertEqual(csv_problems(as_csv()), ["no sections"])
