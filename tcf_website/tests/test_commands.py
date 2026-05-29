"""Tests for Django management commands"""

from io import StringIO

from django.core import management
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from tcf_website.models import CourseGrade, CourseInstructorGrade

from .test_utils import setup


class LoadGradesTestCase(TestCase):
    """Tests for the load_grades command. Uses the test_data.csv file, which holds dummy
    data for two sections of the same course taught by the same instructor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        # Clearing is required to pass tests
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades", "test/test_data", "--suppress-tqdm", verbosity=0
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_no_duplicates(self):
        """Make sure only one instance of CourseGrade and CourseInstructorGrade were created.
        In particular, make sure that the blank row does *not* have an object created for it.
        """
        self.assertEqual(CourseGrade.objects.count(), 1)
        self.assertEqual(CourseInstructorGrade.objects.count(), 1)

    def test_correct_course(self):
        """Make sure the course for both is CS 1420"""
        self.assertEqual(self.cg.course, self.cig.course)

    def test_correct_instructor(self):
        """Make sure instructor is Tom Jefferson"""
        self.assertEqual(self.cig.instructor.full_name, "Tom Jefferson")

    def test_total_students(self):
        """Check valid total_enrolled"""
        self.assertEqual(self.cg.total_enrolled, 24)
        self.assertEqual(self.cig.total_enrolled, 24)

    def test_correct_distribution(self):
        """Make sure both instances match expected values"""
        self.assert_correct_data(self.cg)
        self.assert_correct_data(self.cig)

    def assert_correct_data(self, model):
        """Helper function. Checks model's data against expected values from
        manually adding together the two rows in the CSV."""
        self.assertEqual(model.a_plus, 1)
        self.assertEqual(model.a, 4)
        self.assertEqual(model.a_minus, 6)
        self.assertEqual(model.b_plus, 3)
        self.assertEqual(model.b, 0)
        self.assertEqual(model.b_minus, 3)
        self.assertEqual(model.c_plus, 1)
        self.assertEqual(model.c, 2)
        self.assertEqual(model.c_minus, 0)
        self.assertEqual(model.dfw, 4)

    def test_matching_data(self):
        """Make sure both instances match each other"""
        for field in [
            "a_plus",
            "a",
            "a_minus",
            "b_plus",
            "b",
            "b_minus",
            "c_plus",
            "c",
            "c_minus",
            "dfw",
        ]:
            cg_field = getattr(self.cg, field)
            cig_field = getattr(self.cig, field)
            self.assertEqual(cg_field, cig_field)


class LoadGradesMissingAggregate(TestCase):
    """Tests case when aggregate data (Course GPA/# Students) is not provided."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades",
            "test/missing_aggregate",
            "--suppress-tqdm",
            verbosity=0,
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_total_students(self):
        """Check valid total_enrolled even when not provided"""
        self.assertEqual(self.cg.total_enrolled, 10)
        self.assertEqual(self.cig.total_enrolled, 10)


class LoadGradesMissingDistribution(TestCase):
    """Tests case when distribution data is not provided."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        CourseGrade.objects.all().delete()
        CourseInstructorGrade.objects.all().delete()
        management.call_command(
            "load_grades",
            "test/missing_distribution",
            "--suppress-tqdm",
            verbosity=0,
        )
        cls.cg = CourseGrade.objects.first()
        cls.cig = CourseInstructorGrade.objects.first()

    def test_aggregate_stats(self):
        """Check aggregate stats across sections combined correctly"""
        self.assertEqual(self.cg.average, 3)
        self.assertEqual(self.cig.average, 3)

        self.assertEqual(self.cg.total_enrolled, 4)
        self.assertEqual(self.cig.total_enrolled, 4)


# ---------------------------------------------------------------------------
# list_reviews command
# ---------------------------------------------------------------------------


def _run(stdout=None, **kwargs):
    """Call list_reviews and return captured stdout as a string."""
    out = stdout or StringIO()
    call_command("list_reviews", stdout=out, **kwargs)
    return out.getvalue()


class ListReviewsHelperMethodTests(TestCase):
    """Unit tests for Command helper methods — no DB required."""

    def setUp(self):
        from tcf_website.management.commands.list_reviews import Command

        self.cmd = Command()

    # _safe_field
    def test_safe_field_strips_pipe(self):
        self.assertEqual(self.cmd._safe_field("foo|bar"), "foo bar")

    def test_safe_field_strips_newline(self):
        self.assertEqual(self.cmd._safe_field("foo\nbar"), "foo bar")

    def test_safe_field_strips_surrounding_whitespace(self):
        self.assertEqual(self.cmd._safe_field("  hello  "), "hello")

    def test_safe_field_handles_combined(self):
        self.assertEqual(self.cmd._safe_field("  a|b\nc  "), "a b c")

    # _mask_name
    def test_mask_name_full_name(self):
        self.assertEqual(self.cmd._mask_name("Taylor Comb"), "T*** C***")

    def test_mask_name_single_word(self):
        self.assertEqual(self.cmd._mask_name("Taylor"), "T***")

    def test_mask_name_empty(self):
        self.assertEqual(self.cmd._mask_name(""), "***")

    def test_mask_name_first_letter_only_preserved(self):
        result = self.cmd._mask_name("Alice Wonderland")
        self.assertTrue(result.startswith("A***"))
        self.assertTrue(result.endswith("W***"))

    # _mask_email
    def test_mask_email_standard(self):
        self.assertEqual(self.cmd._mask_email("jack@example.com"), "j***@example.com")

    def test_mask_email_empty(self):
        self.assertEqual(self.cmd._mask_email(""), "***")

    def test_mask_email_no_at_sign(self):
        self.assertEqual(self.cmd._mask_email("notanemail"), "***")

    def test_mask_email_preserves_domain(self):
        result = self.cmd._mask_email("user@virginia.edu")
        self.assertIn("@virginia.edu", result)
        self.assertNotIn("user", result)

    # _parse_url
    def test_parse_url_path_only(self):
        self.assertEqual(self.cmd._parse_url("/course/42/67/"), (42, 67))

    def test_parse_url_full_url(self):
        self.assertEqual(
            self.cmd._parse_url("https://thecourseforum.com/course/10/20/"), (10, 20)
        )

    def test_parse_url_invalid_raises(self):
        with self.assertRaises(CommandError):
            self.cmd._parse_url("/not/a/course/url/")

    # _resolve_ids
    def test_resolve_ids_via_url(self):
        self.assertEqual(
            self.cmd._resolve_ids(
                {"url": "/course/1/2/", "course_id": None, "instructor_id": None}
            ),
            (1, 2),
        )

    def test_resolve_ids_via_explicit_ids(self):
        self.assertEqual(
            self.cmd._resolve_ids({"url": None, "course_id": 5, "instructor_id": 9}),
            (5, 9),
        )

    def test_resolve_ids_zero_course_id_accepted(self):
        # 0 is a valid (falsy) int — must not fall through to the error branch
        self.assertEqual(
            self.cmd._resolve_ids({"url": None, "course_id": 0, "instructor_id": 3}),
            (0, 3),
        )

    def test_resolve_ids_missing_both_raises(self):
        with self.assertRaises(CommandError):
            self.cmd._resolve_ids(
                {"url": None, "course_id": None, "instructor_id": None}
            )


class ListReviewsIntegrationTests(TestCase):
    """Integration tests that hit the database via call_command."""

    def setUp(self):
        setup(self)
        # review1 and review2 are both on self.course + self.instructor (see test_utils)

    # --- basic output --------------------------------------------------

    def test_header_contains_course_and_count(self):
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        self.assertIn(str(self.course), out)
        self.assertIn("2 total", out)

    def test_review_ids_appear_in_output(self):
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        self.assertIn(f"ID: {self.review1.id}", out)
        self.assertIn(f"ID: {self.review2.id}", out)

    def test_no_parseable_lines_by_default(self):
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        review_lines = [line for line in out.splitlines() if line.startswith("REVIEW|")]
        self.assertEqual(len(review_lines), 0)

    def test_parseable_flag_emits_review_lines(self):
        out = _run(
            course_id=self.course.pk, instructor_id=self.instructor.pk, parseable=True
        )
        review_lines = [line for line in out.splitlines() if line.startswith("REVIEW|")]
        self.assertEqual(len(review_lines), 2)

    def test_machine_line_format(self):
        out = _run(
            course_id=self.course.pk, instructor_id=self.instructor.pk, parseable=True
        )
        review_lines = [line for line in out.splitlines() if line.startswith("REVIEW|")]
        for line in review_lines:
            parts = line.split("|")
            # REVIEW | id | name | email | hidden | excerpt
            self.assertEqual(len(parts), 6)
            self.assertTrue(parts[1].isdigit())

    # --- PII masking (default) -----------------------------------------

    def test_email_is_masked_by_default(self):
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        # user1 email is "tcf2yay@virginia.edu" — should not appear verbatim
        self.assertNotIn("tcf2yay@virginia.edu", out)
        self.assertIn("@virginia.edu", out)  # domain still visible

    def test_full_name_is_masked_by_default(self):
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        # user1 is "Taylor Comb" — full name must not appear
        self.assertNotIn("Taylor Comb", out)

    # --- --show-user-info flag ----------------------------------------

    def test_show_user_info_reveals_email(self):
        out = _run(
            course_id=self.course.pk,
            instructor_id=self.instructor.pk,
            show_user_info=True,
        )
        self.assertIn("tcf2yay@virginia.edu", out)

    def test_show_user_info_reveals_name(self):
        out = _run(
            course_id=self.course.pk,
            instructor_id=self.instructor.pk,
            show_user_info=True,
        )
        self.assertIn("Taylor Comb", out)

    # --- --hidden-only / --visible-only --------------------------------

    def test_hidden_only_shows_only_hidden(self):
        self.review1.hidden = True
        self.review1.save()
        out = _run(
            course_id=self.course.pk,
            instructor_id=self.instructor.pk,
            hidden_only=True,
        )
        self.assertIn(f"ID: {self.review1.id}", out)
        self.assertNotIn(f"ID: {self.review2.id}", out)

    def test_visible_only_excludes_hidden(self):
        self.review1.hidden = True
        self.review1.save()
        out = _run(
            course_id=self.course.pk,
            instructor_id=self.instructor.pk,
            visible_only=True,
        )
        self.assertNotIn(f"ID: {self.review1.id}", out)
        self.assertIn(f"ID: {self.review2.id}", out)

    def test_hidden_flag_label_appears(self):
        self.review1.hidden = True
        self.review1.save()
        out = _run(course_id=self.course.pk, instructor_id=self.instructor.pk)
        self.assertIn("[HIDDEN]", out)

    def test_hidden_and_visible_only_together_raises(self):
        with self.assertRaises(CommandError):
            _run(
                course_id=self.course.pk,
                instructor_id=self.instructor.pk,
                hidden_only=True,
                visible_only=True,
            )

    # --- URL argument -------------------------------------------------

    def test_url_argument_resolves_correctly(self):
        url = f"/course/{self.course.pk}/{self.instructor.pk}/"
        out = _run(url=url)
        self.assertIn("2 total", out)

    # --- error paths --------------------------------------------------

    def test_missing_course_raises(self):
        with self.assertRaises(CommandError):
            _run(course_id=99999, instructor_id=self.instructor.pk)

    def test_missing_instructor_raises(self):
        with self.assertRaises(CommandError):
            _run(course_id=self.course.pk, instructor_id=99999)

    def test_no_reviews_outputs_message(self):
        # course2 has reviews but not with instructor2
        out = _run(course_id=self.course.pk, instructor_id=self.instructor2.pk)
        self.assertIn("No reviews found", out)

    def test_no_args_raises(self):
        with self.assertRaises(CommandError):
            _run()


# ---------------------------------------------------------------------------
# hide_review command
# ---------------------------------------------------------------------------


def _hide(stdout=None, **kwargs):
    """Call hide_review and return captured stdout as a string."""
    out = stdout or StringIO()
    call_command("hide_review", stdout=out, **kwargs)
    return out.getvalue()


class HideReviewTests(TestCase):
    """Tests for the hide_review management command."""

    def setUp(self):
        setup(self)
        # review1 starts visible (hidden=False by default)

    # --- --show flag -------------------------------------------------------

    def test_show_prints_review_details(self):
        out = _hide(id=self.review1.pk, show=True)
        self.assertIn(str(self.review1.pk), out)
        self.assertIn(self.review1.course.__str__(), out)

    def test_show_does_not_modify_review(self):
        _hide(id=self.review1.pk, show=True)
        self.review1.refresh_from_db()
        self.assertFalse(self.review1.hidden)

    # --- hide a visible review ---------------------------------------------

    def test_hide_sets_hidden_true(self):
        _hide(id=self.review1.pk, reason="Test hide")
        self.review1.refresh_from_db()
        self.assertTrue(self.review1.hidden)

    def test_hide_output_contains_log_line(self):
        out = _hide(id=self.review1.pk, reason="Test hide")
        self.assertIn("[HIDE_REVIEW]", out)
        self.assertIn(f"id={self.review1.pk}", out)
        self.assertIn("hidden=True", out)

    def test_hide_output_contains_reason(self):
        out = _hide(id=self.review1.pk, reason="Violates guidelines")
        self.assertIn("Violates guidelines", out)

    def test_hide_output_says_done(self):
        out = _hide(id=self.review1.pk, reason="Test hide")
        self.assertIn("hidden", out)

    # --- unhide a hidden review --------------------------------------------

    def test_unhide_sets_hidden_false(self):
        self.review1.hidden = True
        self.review1.save()
        _hide(id=self.review1.pk, reason="Mistakenly hidden", unhide=True)
        self.review1.refresh_from_db()
        self.assertFalse(self.review1.hidden)

    def test_unhide_output_contains_log_line(self):
        self.review1.hidden = True
        self.review1.save()
        out = _hide(id=self.review1.pk, reason="Mistakenly hidden", unhide=True)
        self.assertIn("[HIDE_REVIEW]", out)
        self.assertIn("hidden=False", out)
        self.assertIn("action=unhide", out)

    # --- already-in-target-state guard ------------------------------------

    def test_hide_already_hidden_no_change(self):
        self.review1.hidden = True
        self.review1.save()
        out = _hide(id=self.review1.pk, reason="Duplicate")
        self.assertIn("already", out)
        self.review1.refresh_from_db()
        self.assertTrue(self.review1.hidden)

    def test_unhide_already_visible_no_change(self):
        out = _hide(id=self.review1.pk, reason="Duplicate", unhide=True)
        self.assertIn("already", out)
        self.review1.refresh_from_db()
        self.assertFalse(self.review1.hidden)

    # --- error paths -------------------------------------------------------

    def test_missing_reason_raises(self):
        with self.assertRaises(CommandError):
            _hide(id=self.review1.pk)

    def test_nonexistent_review_raises(self):
        with self.assertRaises(CommandError):
            _hide(id=99999, reason="Whatever")

    # --- _print_review content ---------------------------------------------

    def test_print_review_shows_status_hidden(self):
        self.review1.hidden = True
        self.review1.save()
        out = _hide(id=self.review1.pk, show=True)
        self.assertIn("HIDDEN", out)

    def test_print_review_shows_status_visible(self):
        out = _hide(id=self.review1.pk, show=True)
        self.assertIn("visible", out)

    def test_print_review_shows_user_email(self):
        out = _hide(id=self.review1.pk, show=True)
        # review1 belongs to user1 whose email is tcf2yay@virginia.edu
        self.assertIn("tcf2yay@virginia.edu", out)

    def test_print_review_shows_text(self):
        out = _hide(id=self.review1.pk, show=True)
        self.assertIn(self.review1.text[:20], out)

    def test_print_review_no_email_fallback(self):
        # user2 has no email — should print "(none)"
        out = _hide(id=self.review2.pk, show=True)
        self.assertIn("(none)", out)
