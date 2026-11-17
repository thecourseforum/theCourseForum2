"""SIS's "To Be Announced" placeholder must never surface as an instructor (#1290)."""

from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase

from tcf_website.management.commands.fetch_grades import (
    format_engine_name,
    format_sis_name,
)
from tcf_website.management.commands.load_semester import Command as LoadSemester
from tcf_website.models import Instructor
from tcf_website.utils import is_tba_instructor
from tcf_website.views.catalog.search import fetch_instructors

from .test_utils import setup

hide_tba_instructors = import_module(
    "tcf_website.migrations.0030_hide_tba_instructors"
).hide_tba_instructors

VARIANTS = (
    "To Be Announced",
    "To be Announced",
    "to be announced",
    " To  be\tAnnounced ",
)


class TBAInstructorTests(TestCase):
    def test_is_tba_instructor_ignores_case_and_spacing(self):
        for name in VARIANTS:
            self.assertTrue(is_tba_instructor(name), name)
        self.assertFalse(is_tba_instructor("Jane Doe"))
        self.assertFalse(is_tba_instructor(""))

    def test_fetch_grades_drops_every_variant(self):
        for name in VARIANTS:
            self.assertEqual(format_sis_name(name), "...", name)
            self.assertEqual(format_engine_name(name), "...", name)
        self.assertEqual(format_sis_name("Jane Doe"), "Doe,Jane")

    def test_load_semester_maps_every_variant_to_staff(self):
        command = LoadSemester()
        command.verbose = False
        command.STAFF = Instructor.objects.create(last_name="Staff")
        for name in VARIANTS:
            self.assertEqual(command.load_instructors([name]), {command.STAFF}, name)
        self.assertFalse(Instructor.objects.filter(last_name="Announced").exists())

    def test_migration_hides_existing_placeholder_and_search_skips_it(self):
        setup(self)
        tba = Instructor.objects.create(first_name="To", last_name="Announced")
        real = Instructor.objects.create(first_name="Ann", last_name="Announced")
        self.section_course.instructors.set([tba])
        hide_tba_instructors(apps, SimpleNamespace(connection=connection))
        # The section stays addable in the schedule builder under Staff.
        self.assertTrue(
            self.section_course.instructors.filter(
                last_name="Staff", hidden=False
            ).exists()
        )
        tba.refresh_from_db()
        real.refresh_from_db()
        self.assertTrue(tba.hidden)
        self.assertFalse(real.hidden)
        ids = {row["id"] for row in fetch_instructors("Announced")}
        self.assertNotIn(tba.id, ids)
        self.assertIn(real.id, ids)
