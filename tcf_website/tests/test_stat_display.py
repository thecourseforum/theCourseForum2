# pylint: disable=no-member
"""Tests for stat display normalization (sentinel values on course cards)."""

import unittest

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.auth",
            "tcf_website",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        SECRET_KEY="test",
        USE_TZ=True,
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
            }
        ],
    )
django.setup()

from django.template import Context, Template

from tcf_website.stat_display import stat_display_value


class StatDisplayValueTestCase(unittest.TestCase):
    """``stat_display_value`` hides sentinel and out-of-range aggregates."""

    def test_sentinel_negatives_are_hidden(self):
        """Instructor sort placeholders (-1, -1/3) must not render as real stats."""
        self.assertIsNone(stat_display_value("difficulty", -1))
        self.assertIsNone(stat_display_value("gpa", -1))
        self.assertIsNone(stat_display_value("rating", -1 / 3))

    def test_valid_values_pass_through(self):
        """In-range aggregates are returned as floats."""
        self.assertEqual(stat_display_value("rating", 4.0), 4.0)
        self.assertEqual(stat_display_value("difficulty", 3), 3.0)
        self.assertEqual(stat_display_value("gpa", 3.49), 3.49)

    def test_unknown_kind_returns_none(self):
        """Invalid stat kinds are treated as missing."""
        self.assertIsNone(stat_display_value("bogus", 3.0))


class StatDisplayFilterTestCase(unittest.TestCase):
    """``stat_display`` template filter."""

    def test_filter_hides_sentinel_rating(self):
        """Combined rating sentinel from Coalesce averages must show as empty."""
        rendered = Template(
            "{% load custom_tags %}{{ v|stat_display:'rating'|default:'EMPTY' }}"
        ).render(Context({"v": -1 / 3}))
        self.assertEqual(rendered, "EMPTY")
