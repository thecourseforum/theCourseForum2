"""Tests for Review model."""

import json

from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse

from ..models import Review, Vote
from ..review.forms import ReviewForm
from .test_utils import setup, suppress_request_warnings


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
