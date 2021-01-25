# pylint: disable=no-member
"""Tests for Review model."""

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse


from .test_utils import setup


class DeleteReviewTests(TestCase):
    """Tests for the DeleteReview view."""

    def setUp(self):
        setup(self)  # set up tests: add some example data

    def test_delete_review_message(self):
        """Test if a message is shown when a user deletes their review."""
        self.client.force_login(
            self.review1.user)  # force a login as the author of review1
        # try and make the user delete review1
        response = self.client.post(
            reverse('delete_review', args=[self.review1.id]),
        )

        self.assertEqual(response.status_code, 302)  # ensure 302 Found status

        # get messages from the request
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(str(messages[0]), 'Successfully deleted your review!')

    def test_delete_nonexistent_review_id(self):
        """Test if a 404 is returned for deleting a nonexistent review ID."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse('delete_review', args=[0])  # id 0 = nonexistent review
        )

        self.assertEqual(response.status_code, 404)

    def test_unauthorized_user_delete(self):
        """Test if a 403 is returned for unauthorized review deletion."""
        self.client.force_login(self.user2)  # force login as user2

        # Note: because PermissionDenied is (should be) raised in this view, we get a really ugly
        # traceback in the test runner. This isn't so nice, because it makes the
        # `./precommit` output annoying to sort through.
        # Is there any way to silence the errors while we're running tests?
        response = self.client.post(
            # try to delete review1, which is not authored by user2
            reverse('delete_review', args=[self.review1.pk])
        )

        # trying to delete a review you don't have access to should result in
        # 403 - forbidden
        self.assertEqual(response.status_code, 403)
