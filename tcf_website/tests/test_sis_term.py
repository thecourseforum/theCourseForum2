"""SIS term codes derived from a <year>_<season> argument."""

from datetime import date

from django.test import SimpleTestCase

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

    def test_current_semester_follows_the_date(self):
        self.assertEqual(current_semester(date(2026, 1, 17)), "2026_january")
        self.assertEqual(current_semester(date(2026, 1, 18)), "2026_spring")
        self.assertEqual(current_semester(date(2026, 5, 1)), "2026_summer")
        self.assertEqual(current_semester(date(2026, 8, 1)), "2026_fall")
        self.assertEqual(current_semester(date(2026, 10, 3)), "2026_fall")
        self.assertEqual(sis_term_code(current_semester(date(2026, 10, 3))), "1268")
