"""SIS term codes derived from a <year>_<season> argument."""

from datetime import date
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from tcf_website.management.commands import fetch_data as fetch_data_mod
from tcf_website.utils import current_semester, sis_term_code


class SisTermCodeTests(SimpleTestCase):
    def test_seasons(self):
        self.assertEqual(sis_term_code("2026_fall"), "1268")
        self.assertEqual(sis_term_code("2024_spring"), "1242")
        self.assertEqual(sis_term_code("2026_SUMMER"), "1266")
        self.assertEqual(sis_term_code("2026_january"), "1261")

    def test_rejects_bad_arguments(self):
        self.assertIsNone(sis_term_code("2026"))
        self.assertIsNone(sis_term_code("fall"))
        self.assertIsNone(sis_term_code("2026_winter"))
        self.assertIsNone(sis_term_code("26_fall"))

    def test_current_semester_follows_published_starts(self):
        self.assertEqual(current_semester(date(2026, 1, 1)), "2025_fall")
        self.assertEqual(current_semester(date(2026, 1, 2)), "2026_january")
        self.assertEqual(current_semester(date(2026, 1, 12)), "2026_spring")
        self.assertEqual(current_semester(date(2026, 5, 17)), "2026_spring")
        self.assertEqual(current_semester(date(2026, 5, 18)), "2026_summer")
        self.assertEqual(current_semester(date(2026, 8, 24)), "2026_summer")
        self.assertEqual(current_semester(date(2026, 8, 25)), "2026_fall")
        self.assertEqual(current_semester(date(2026, 10, 3)), "2026_fall")
        self.assertEqual(sis_term_code(current_semester(date(2026, 10, 3))), "1268")
        self.assertEqual(current_semester(date(2028, 1, 3)), "2028_january")
        self.assertEqual(current_semester(date(2028, 1, 18)), "2028_january")
        self.assertEqual(current_semester(date(2028, 1, 19)), "2028_spring")
        self.assertEqual(sis_term_code(current_semester(date(2028, 1, 10))), "1281")
        self.assertEqual(current_semester(date(2028, 6, 1)), "2028_summer")
        self.assertEqual(current_semester(date(2031, 1, 2)), "2031_january")

    def test_fetch_data_rejects_a_bad_semester(self):
        with self.assertRaises(CommandError):
            call_command("fetch_data", "2026_winter")

    def test_fetch_data_rejects_disallowed_branch(self):
        with (
            patch.dict("os.environ", {"COURSE_DATA_REPO_BRANCH": "evil"}, clear=False),
            self.assertRaises(CommandError),
        ):
            call_command("fetch_data", "2026_fall")

    def test_fetch_data_rejects_header_only_csv_and_keeps_existing(self):
        import tempfile

        header_only = b"Mnemonic,Number\n"
        with tempfile.TemporaryDirectory() as tmp:
            dest_dir = Path(tmp) / "fetched"
            dest_dir.mkdir()
            dest = dest_dir / "2026_fall.csv"
            dest.write_text("Mnemonic,Number\nCS,1110\n", encoding="utf-8")

            with (
                patch.object(fetch_data_mod, "DEST_DIR", dest_dir),
                patch.object(fetch_data_mod, "_raw_download", return_value=header_only),
                self.assertRaises(CommandError),
            ):
                call_command("fetch_data", "2026_fall")

            self.assertEqual(
                dest.read_text(encoding="utf-8"), "Mnemonic,Number\nCS,1110\n"
            )
