"""Placeholder instructor names must be dropped regardless of casing."""

from django.test import SimpleTestCase

from tcf_website.management.commands.fetch_grades import (
    format_engine_name,
    format_sis_name,
    is_tba_instructor,
)


class TBAInstructorNameTestCase(SimpleTestCase):
    def test_is_tba_instructor_case_variants(self):
        self.assertTrue(is_tba_instructor("To Be Announced"))
        self.assertTrue(is_tba_instructor("To be Announced"))
        self.assertTrue(is_tba_instructor("to be announced"))
        self.assertTrue(is_tba_instructor("  To be Announced  "))
        self.assertFalse(is_tba_instructor("Jane Doe"))
        self.assertFalse(is_tba_instructor(""))

    def test_format_sis_name_drops_tba(self):
        self.assertEqual(format_sis_name("To Be Announced"), "...")
        self.assertEqual(format_sis_name("To be Announced"), "...")
        self.assertEqual(format_sis_name("Jane Doe"), "Doe,Jane")

    def test_format_engine_name_drops_tba(self):
        self.assertEqual(format_engine_name("To Be Announced"), "...")
        self.assertEqual(format_engine_name("To be Announced"), "...")
        self.assertEqual(format_engine_name("Doe,Jane"), "Doe,Jane")
