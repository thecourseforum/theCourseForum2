"""Sanity check: schedule domain package imports without Django view layer."""

from django.forms import ModelForm
from django.test import SimpleTestCase


class ScheduleDomainImportTests(SimpleTestCase):
    def test_schedule_subpackage_imports(self):
        from tcf_website.schedule import (  # pylint: disable=import-outside-toplevel
            ScheduleForm,
            build_weekly_calendar,
            resolve_builder_semester,
            schedule_visible_q,
        )

        self.assertTrue(callable(build_weekly_calendar))
        self.assertTrue(callable(resolve_builder_semester))
        self.assertTrue(callable(schedule_visible_q))
        self.assertTrue(issubclass(ScheduleForm, ModelForm))
