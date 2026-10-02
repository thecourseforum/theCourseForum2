"""SIS term codes derived from a <year>_<season> argument."""

from django.test import SimpleTestCase

from tcf_website.utils import sis_term_code


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
