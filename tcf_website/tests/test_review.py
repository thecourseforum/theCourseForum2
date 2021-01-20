# pylint: disable=no-member
"""Tests for Review model."""
from urllib.parse import urlencode

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from .test_utils import setup


class EditReviewTests(TestCase):
    """Tests for the `edit_review` view."""

    def setUp(self):
        setup(self)
        self.valid_data_with_different_text = urlencode({
            'text': 'new text',
            'course': self.review1.course.id,
            'instructor': self.review1.instructor.id,
            'semester': self.review1.semester.id,
            'instructor_rating': self.review1.instructor_rating,
            'difficulty': self.review1.difficulty,
            'recommendability': self.review1.recommendability,
            'enjoyability': self.review1.enjoyability,
            'amount_reading': self.review1.amount_reading,
            'amount_writing': self.review1.amount_writing,
            'amount_group': self.review1.amount_group,
            'amount_homework': self.review1.amount_homework,
        })

    def test_nonexistent_review_id(self):
        """Test if a 404 error is returned for a nonexistent review ID."""
        self.client.force_login(self.review1.user)
        response = self.client.post(
            reverse('edit_review', args=[0]),  # nonexistent review id: 0
            self.valid_data_with_different_text,
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 404)

    def test_different_user(self):
        """Test if a user can edit someone else's review."""
        self.client.force_login(self.user2)  # self.user2 != self.review1.user
        response = self.client.post(
            reverse('edit_review', args=[self.review1.id]),
            self.valid_data_with_different_text,
            content_type='application/x-www-form-urlencoded',
        )
        self.assertEqual(response.status_code, 403)

    def test_update_text(self):
        """Test if review text is updated."""
        self.client.force_login(self.review1.user)
        response = self.client.post(
            reverse('edit_review', args=[self.review1.id]),
            self.valid_data_with_different_text,  # data with updated text
            content_type='application/x-www-form-urlencoded',
        )
        self.assertRedirects(response, reverse('reviews'))
        self.review1.refresh_from_db()
        self.assertEqual(self.review1.text, 'new text')
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertEqual(str(messages[0]),
                         'Successfully updated your review for CS 420 | Software Testing!')

    def test_message_for_invalid_form(self):
        """Test if a message is shown when invalid form data is submitted."""
        self.client.force_login(self.review1.user)
        data_with_invalid_difficulty = urlencode({'difficulty': -1})
        response = self.client.post(
            reverse('edit_review', args=[self.review1.id]),
            data_with_invalid_difficulty,  # invalid form data
            content_type='application/x-www-form-urlencoded',
        )
        messages = [m.message for m in get_messages(response.wsgi_request)]
        self.assertIn('difficulty', str(messages[0]))
