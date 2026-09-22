"""Tests for Review model."""

import json

from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ..models import Club, ClubCategory, Review, Section, Semester, Vote
from ..review.forms import ReviewForm
from ..utils import semesters_for_course
from .test_utils import setup, suppress_request_warnings


def _future_semester_with_section(course, instructor):
    """Create a not-yet-started Fall term with a matching section for ``course``."""
    future_year = timezone.now().year + 1
    number = int(f"1{future_year % 100}8")  # trailing 8 => Fall (starts in August)
    semester = Semester.objects.create(year=future_year, season="FALL", number=number)
    section = Section.objects.create(
        course=course, semester=semester, sis_section_number=999001
    )
    section.instructors.set([instructor])
    return semester


class ReviewFormTests(TestCase):
    """Tests for the ReviewForm."""

    def setUp(self):
        setup(self)

    def test_reviewform_recalculates_hours_per_week_on_save(self):
        """Test if hours_per_week is recalculated on save."""
        review1: dict = model_to_dict(self.review1)
        review1["amount_reading"] = self.review1.amount_reading - 1
        previous_sum: int = self.review1.hours_per_week
        form = ReviewForm(review1, instance=self.review1)
        self.assertTrue(form.is_valid())
        form.save()
        self.review1.refresh_from_db()
        self.assertEqual(previous_sum - 1, self.review1.hours_per_week)

    def _ratings_only_data(self, **overrides):
        """Minimal valid POST data for a ratings-only course review."""
        data = {
            "course": self.course2.id,
            "instructor": self.instructor.id,
            "semester": self.semester.id,
            "instructor_rating": 4,
            "difficulty": 3,
            "recommendability": 5,
            "enjoyability": 4,
            "hours_per_week": 6,
        }
        data.update(overrides)
        return data

    def test_ratings_only_review_is_valid(self):
        """No text and no hours breakdown is a valid review."""
        form = ReviewForm(self._ratings_only_data())
        self.assertTrue(form.is_valid(), form.errors)
        review = form.save(commit=False)
        self.assertEqual(review.text, "")
        self.assertEqual(review.hours_per_week, 6)
        self.assertIsNone(review.amount_reading)
        self.assertIsNone(review.amount_homework)

    def test_short_text_is_rejected(self):
        """Text, when present, still needs 200 characters."""
        form = ReviewForm(self._ratings_only_data(text="Too short to count."))
        self.assertFalse(form.is_valid())
        self.assertIn("text", form.errors)

    def test_full_breakdown_overrides_hours_per_week(self):
        """All four breakdown fields present: hours_per_week is their sum."""
        form = ReviewForm(
            self._ratings_only_data(
                hours_per_week=50,
                amount_reading=1,
                amount_writing=2,
                amount_group=3,
                amount_homework=4,
            )
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.save(commit=False).hours_per_week, 10)

    def test_partial_breakdown_is_rejected(self):
        """Some but not all breakdown fields is an error."""
        form = ReviewForm(self._ratings_only_data(amount_reading=2))
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_missing_hours_is_rejected(self):
        """Neither a breakdown nor hours_per_week is an error."""
        data = self._ratings_only_data()
        del data["hours_per_week"]
        form = ReviewForm(data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_club_review_still_requires_text(self):
        """Club reviews are unchanged: text is required."""
        category = ClubCategory.objects.create(name="Academic", slug="academic")
        club = Club.objects.create(name="Chess Club", category=category)
        form = ReviewForm(
            {
                "club": club.id,
                "semester": self.semester.id,
                "instructor_rating": 4,
                "difficulty": 3,
                "recommendability": 5,
                "enjoyability": 4,
                "hours_per_week": 2,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class DeleteReviewTests(TestCase):
    """Tests for the DeleteReview view."""

    def setUp(self):
        setup(self)  # set up tests: add some example data

    def test_delete_review_message(self):
        """Test if a message is shown when a user deletes their review."""
        self.client.force_login(
            self.review1.user
        )  # force a login as the author of review1
        # try and make the user delete review1
        response = self.client.post(
            reverse("delete_review", args=[self.review1.id]),
        )

        self.assertEqual(response.status_code, 302)  # ensure 302 Found status

        # get messages from the request
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(
            str(messages[0]),
            f"Successfully deleted your review for {str(self.review1.course)}!",
        )

    @suppress_request_warnings
    def test_delete_nonexistent_review_id(self):
        """Test if a 404 is returned for deleting a nonexistent review ID."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("delete_review", args=[0])
        )  # id 0 = nonexistent review

        self.assertEqual(response.status_code, 404)

    @suppress_request_warnings
    def test_unauthorized_user_delete(self):
        """Test if a 403 is returned for unauthorized review deletion."""
        self.client.force_login(self.user2)  # force login as user2

        response = self.client.post(
            # try to delete review1, which is not authored by user2
            reverse("delete_review", args=[self.review1.pk])
        )

        # trying to delete a review you don't have access to should result in
        # 403 - forbidden
        self.assertEqual(response.status_code, 403)


class ModelReviewTests(TestCase):
    """Tests for the Review model."""

    def setUp(self):
        setup(self)

    def test_count_votes(self):
        """Test for count votes method"""
        self.assertDictEqual(self.review1.count_votes(), {"upvotes": 2, "downvotes": 1})

    def test_count_votes_no_votes(self):
        """Test for count votes method for when there are no votes"""
        self.assertEqual(self.review2.count_votes(), {"upvotes": 0, "downvotes": 0})

    def test_upvote(self):
        """Test for upvote method verify with count_votes"""
        self.review1.upvote(self.user4)
        self.assertDictEqual(self.review1.count_votes(), {"upvotes": 3, "downvotes": 1})

    def test_upvote_already_upvoted(self):
        """Test for upvote method verify with count_votes when the user already upvoted"""
        self.review1.upvote(self.user4)
        self.review1.upvote(self.user4)
        self.assertDictEqual(self.review1.count_votes(), {"upvotes": 2, "downvotes": 1})

    def test_downvote(self):
        """Test for downvote method verify with count_votes"""
        self.review1.downvote(self.user4)
        self.assertDictEqual(self.review1.count_votes(), {"upvotes": 2, "downvotes": 2})

    def test_upvote_already_downvoted(self):
        """Test for downvote method verify with count_votes when the user already downvoted"""
        self.review1.downvote(self.user4)
        self.review1.downvote(self.user4)
        self.assertDictEqual(self.review1.count_votes(), {"upvotes": 2, "downvotes": 1})

    def test_double_vote(self):
        """Test for voting twice on same review by same user using vote model"""
        self.assertRaises(
            IntegrityError,
            Vote.objects.create,
            value=-1,
            user=self.user3,
            review=self.review1,
        )

    def test_display_reviews(self):
        """Test display reviews method"""
        review_queryset = Review.objects.filter(course=self.course)

        self.assertQuerysetEqual(
            Review.get_sorted_reviews(self.course, self.instructor, self.user1),
            review_queryset,
            transform=lambda x: x,  # Needed so that the formatting works
            ordered=False,
        )

    def test_display_no_reviews(self):
        """Test display reviews method when there are no reviews"""
        self.review1.delete()
        self.review2.delete()
        self.assertFalse(
            Review.get_sorted_reviews(self.course, self.instructor, self.user1).exists()
        )


def _review_post_data(course, instructor, semester):
    """Minimal valid POST payload for ReviewForm (course review)."""
    return {
        "text": "x" * 200,
        "course": str(course.pk),
        "instructor": str(instructor.pk),
        "semester": str(semester.pk),
        "instructor_rating": "3",
        "difficulty": "3",
        "recommendability": "3",
        "enjoyability": "3",
        "amount_reading": "0",
        "amount_writing": "0",
        "amount_group": "0",
        "amount_homework": "0",
    }


class ReviewFormSectionValidationTests(TestCase):
    """ReviewForm requires a real Section for course/semester/instructor."""

    def setUp(self):
        setup(self)

    def test_accepts_matching_section(self):
        """Instructor on a section for that course and term passes clean()."""
        form = ReviewForm(
            _review_post_data(self.course, self.instructor, self.semester)
        )
        self.assertTrue(form.is_valid())

    def test_rejects_instructor_not_teaching_that_term(self):
        """Instructor with no section for that course+semester fails clean()."""
        form = ReviewForm(
            _review_post_data(self.course, self.instructor2, self.semester)
        )
        self.assertFalse(form.is_valid())

    def test_rejects_future_semester(self):
        """A term that has not started yet cannot be reviewed, even with a section."""
        future = _future_semester_with_section(self.course, self.instructor)
        form = ReviewForm(_review_post_data(self.course, self.instructor, future))
        self.assertFalse(form.is_valid())
        self.assertIn("started", str(form.errors).lower())

    def test_accepts_started_semester(self):
        """A term that has already started passes clean()."""
        # self.semester is Fall 2025, which has already started.
        form = ReviewForm(
            _review_post_data(self.course, self.instructor, self.semester)
        )
        self.assertTrue(form.is_valid())


class ReviewCascadeJsonEndpointsTests(TestCase):
    """XHR helpers for the unified review writer."""

    def setUp(self):
        setup(self)

    def test_semesters_anonymous_redirects(self):
        """Anonymous requests redirect to login."""
        response = self.client.get(
            reverse("review_semester_options"),
            {"course": self.course.pk},
        )
        self.assertEqual(response.status_code, 302)

    def test_semesters_returns_terms_with_sections(self):
        """Semester options only include terms with matching sections."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("review_semester_options"),
            {"course": self.course.pk},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ids = {row["id"] for row in data["semesters"]}
        self.assertIn(self.semester.pk, ids)

    def test_semesters_excludes_future_terms(self):
        """A not-yet-started term is never offered as a review option."""
        future = _future_semester_with_section(self.course, self.instructor)

        # Direct helper used by both the server render and the XHR endpoint.
        self.assertNotIn(future, list(semesters_for_course(self.course)))

        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("review_semester_options"),
            {"course": self.course.pk},
        )
        data = json.loads(response.content)
        ids = {row["id"] for row in data["semesters"]}
        self.assertNotIn(future.pk, ids)
        self.assertIn(self.semester.pk, ids)

    def test_instructors_bad_request_without_params(self):
        """Missing query params yields 400 instead of silent fallback."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("review_instructor_options"))
        self.assertEqual(response.status_code, 400)

    def test_instructors_returns_json(self):
        """Instructor options returns JSON including expected instructors."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("review_instructor_options"),
            {"course": self.course.pk, "semester": self.semester.pk},
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(
            any(row["last_name"] == "Jefferson" for row in data["instructors"])
        )


class ReviewPreflightJsonTests(TestCase):
    """XHR duplicate / hours checks return JSON on validation failure."""

    def setUp(self):
        setup(self)

    def test_check_duplicate_xhr_invalid_returns_json_400(self):
        """Invalid POST with XHR must not redirect with HTML."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("check_review_duplicate"),
            {"text": "ab"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data.get("ok", True))
        self.assertIn("error", data)

    def test_check_zero_hours_xhr_invalid_returns_json_400(self):
        """Invalid XHR to zero-hours check returns JSON 400."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("check_zero_hours_per_week"),
            {"text": "ab"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data.get("ok", True))


class RatingsOnlyReviewViewTests(TestCase):
    """The full review page accepts a review with no text."""

    def setUp(self):
        setup(self)

    def test_post_without_text_creates_review(self):
        """POST new_review with ratings and a breakdown but no text."""
        self.client.force_login(self.user4)
        response = self.client.post(
            reverse("new_review"),
            {
                "course": self.course2.id,
                "instructor": self.instructor.id,
                "semester": self.semester.id,
                "instructor_rating": 4,
                "difficulty": 3,
                "recommendability": 5,
                "enjoyability": 4,
                "amount_reading": 1,
                "amount_writing": 1,
                "amount_group": 0,
                "amount_homework": 3,
                "text": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get(user=self.user4, course=self.course2)
        self.assertEqual(review.text, "")
        self.assertEqual(review.hours_per_week, 5)

    def test_pair_page_header_shows_ratings_count_separately(self):
        """Ratings-only reviews count toward Ratings but not Reviews in the header."""
        Review.objects.create(
            user=self.user4,
            course=self.course2,
            instructor=self.instructor,
            semester=self.semester,
            text="",
            instructor_rating=4,
            difficulty=3,
            recommendability=5,
            enjoyability=4,
            hours_per_week=5,
        )
        response = self.client.get(
            reverse("course_instructor", args=[self.course2.id, self.instructor.id])
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        self.assertIn("2 Reviews · 3 Ratings", body)
        self.assertEqual(body.count('class="review-card"'), 2)


class RatingsOnlyListingTests(TestCase):
    """The pair page's review list excludes ratings-only reviews."""

    def setUp(self):
        setup(self)

    def test_get_sorted_reviews_excludes_ratings_only_review(self):
        """A ratings-only review is not part of the listed (written) reviews."""
        ratings_only = Review.objects.create(
            user=self.user4,
            course=self.course2,
            instructor=self.instructor,
            semester=self.semester,
            text="",
            instructor_rating=4,
            difficulty=3,
            recommendability=5,
            enjoyability=4,
            hours_per_week=5,
        )
        reviews = list(
            Review.get_sorted_reviews(self.course2.id, self.instructor.id, self.user4)
        )
        self.assertNotIn(ratings_only, reviews)
        self.assertIn(self.review3, reviews)
        self.assertIn(self.review4, reviews)
