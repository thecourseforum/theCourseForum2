# pylint: disable=no-member
"""Tests for Review model."""

from django.contrib.messages import get_messages
from django.db import IntegrityError
from django.forms.models import model_to_dict
from django.test import TestCase
from django.urls import reverse

from ..models import Review, Vote
from ..views.review import ReviewForm
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
