# pylint: disable=no-member
"""Tests for search views and pure helpers."""

from types import SimpleNamespace

from django.test import TestCase
from django.urls import reverse

from tcf_website.models import Club, ClubCategory
from tcf_website.views.catalog.search import (
    course_to_row_dict,
    decide_order,
    group_by_club_category,
    group_by_dept,
    normalize_search_query,
)

from .base import TCFDataTestCase


class NormalizeSearchQueryTestCase(TestCase):
    """Mnemonic + number normalization for trigram matching."""

    def test_inserts_space_for_four_digit_suffix(self):
        """CS1110-style tokens normalize for trigram index."""
        self.assertEqual(normalize_search_query("CS1110"), "CS 1110")

    def test_leaves_other_queries_unchanged(self):
        """Non-matching strings pass through."""
        self.assertEqual(normalize_search_query("algorithms"), "algorithms")
        self.assertEqual(normalize_search_query("CS 2150"), "CS 2150")


class DecideOrderTestCase(TestCase):
    """Autocomplete ordering between course and instructor hits."""

    def test_prefers_courses_when_scores_higher(self):
        """Higher course similarity lists courses before instructors."""
        courses = [{"max_similarity": 0.9}]
        instructors = [{"max_similarity": 0.3}]
        self.assertTrue(decide_order(courses, instructors))

    def test_empty_instructors_lists_courses_first(self):
        """No instructor hits implies course-first ordering."""
        self.assertTrue(decide_order([{"max_similarity": 0.1}], []))


class GroupByDeptTestCase(TCFDataTestCase):
    """Course rows grouped by mnemonic."""

    def test_groups_same_mnemonic(self):
        """Multiple rows under one mnemonic share one group."""
        courses = [
            {
                "id": self.course.id,
                "title": self.course.title,
                "number": self.course.number,
                "mnemonic": "CS",
                "description": self.course.description,
                "max_similarity": 0.5,
            },
            {
                "id": self.course2.id,
                "title": self.course2.title,
                "number": self.course2.number,
                "mnemonic": "CS",
                "description": self.course2.description,
                "max_similarity": 0.4,
            },
        ]
        grouped = group_by_dept(courses)
        self.assertIn("CS", grouped)
        self.assertEqual(len(grouped["CS"]["courses"]), 2)
        self.assertEqual(grouped["CS"]["dept_id"], self.department.pk)


class GroupByClubCategoryTestCase(TestCase):
    """Club dicts grouped by category slug."""

    def test_groups_by_slug(self):
        """Club results bucket by category slug."""
        clubs = [
            {
                "id": 1,
                "name": "A",
                "description": "",
                "max_similarity": 1.0,
                "category_slug": "stem",
                "category_name": "STEM",
            },
            {
                "id": 2,
                "name": "B",
                "description": "",
                "max_similarity": 0.9,
                "category_slug": "stem",
                "category_name": "STEM",
            },
        ]
        grouped = group_by_club_category(clubs)
        self.assertEqual(len(grouped["stem"]["clubs"]), 2)


class CourseToRowDictTestCase(TestCase):
    """Serialization helper for search rows."""

    def test_include_similarity_optional(self):
        """Serializer optionally exposes trigram score."""
        course = SimpleNamespace(
            id=1,
            title="Intro",
            number=1000,
            mnemonic="CS",
            description="Desc",
            max_similarity=0.42,
        )
        without = course_to_row_dict(course, include_similarity=False)
        self.assertNotIn("max_similarity", without)
        with_sim = course_to_row_dict(course, include_similarity=True)
        self.assertEqual(with_sim["max_similarity"], 0.42)


class SearchViewTestCase(TCFDataTestCase):
    """HTTP behavior for ``search`` view."""

    def test_empty_query_redirects_to_browse(self):
        """Course search without q sends users to browse."""
        response = self.client.get(reverse("search"))
        self.assertRedirects(
            response,
            reverse("browse"),
            fetch_redirect_response=False,
        )

    def test_query_renders_results_page(self):
        """Title search returns matching browsable courses."""
        response = self.client.get(reverse("search"), {"q": "Software Testing"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "Software Testing")
        self.assertGreaterEqual(response.context["total"], 1)

    def test_club_mode_full_page(self):
        """Club listing mode renders without course query."""
        category = ClubCategory.objects.create(name="Arts", slug="arts")
        Club.objects.create(name="Photography Guild", category=category)
        response = self.client.get(reverse("search"), {"mode": "clubs"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_club"])

    def test_autocomplete_xhr_course_mode(self):
        """XHR requests get the dropdown partial, not full search page."""
        response = self.client.get(
            reverse("search"),
            {"q": "CS 1420"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "site/common/components/_autocomplete_dropdown.html"
        )

    def test_autocomplete_schedule_add_urls_use_client_next_not_search_path(self):
        """Schedule autocomplete uses client ``next``, not ``/search/``, in links."""
        next_path = "/schedule/?semester=1&schedule=99"
        response = self.client.get(
            reverse("search"),
            {
                "q": "Software Testing",
                "autocomplete_action": "schedule",
                "autocomplete_target": "42",
                "next": next_path,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        decoded = response.content.decode()
        self.assertIn("next=", decoded)
        self.assertIn("schedule=42", decoded)
        self.assertNotIn("/search/", decoded)
        self.assertIn("%3Fsemester%3D1", decoded)
