# pylint: disable=no-member
"""Tests for User model."""

from django.test import TestCase

from .test_utils import setup


class UserTestCase(TestCase):
    """Tests for User model."""

    def setUp(self):
        setup(self)

    def test_user_name(self):
        """Test __str__ method in User model"""
        self.assertEqual("Taylor Comb (tcf2yay@virginia.edu)", str(self.user1))

    def test_user_name_no_email(self):
        """Test __str__ method in User model with no email"""
        self.assertEqual("Kjell Kool ()", str(self.user4))

    def test_full_name(self):
        """Test full_name method in User model when fullname exists"""
        self.assertEqual("Taylor Comb", self.user1.full_name())

    def test_full_name_no_first(self):
        """Test full_name method in User model when first name missing exists"""
        self.assertEqual(" NoFirstName", self.user2.full_name())
