"""Tests for authentication views."""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ForgotPasswordViewTests(TestCase):
    """Tests for the forgot_password view."""

    def setUp(self):
        self.url = reverse("forgot_password")
        self.user = User.objects.create_user(
            username="testuser",
            email="TestUser@virginia.edu",  # mixed-case to verify iexact lookup
            password="testpassword",
            computing_id="testuser",
        )

    def test_get_renders_form(self):
        """GET request renders the forgot-password template."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site/auth/forgot_password.html")

    def test_post_empty_email(self):
        """POST with no email shows an error."""
        response = self.client.post(self.url, {"email": ""})
        self.assertEqual(response.status_code, 200)
        msg_texts = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("enter your email" in t.lower() for t in msg_texts))

    def test_post_unregistered_email_shows_error(self):
        """POST with an unknown email shows a 'no account' error."""
        response = self.client.post(self.url, {"email": "nobody@virginia.edu"})
        self.assertEqual(response.status_code, 200)
        msg_texts = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("no account" in t.lower() for t in msg_texts))

    @patch("tcf_website.views.auth.boto3.client")
    def test_post_registered_email_calls_cognito_and_redirects(self, mock_boto_client):
        """POST with a registered email calls Cognito and redirects to login."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        response = self.client.post(self.url, {"email": "testuser@virginia.edu"})

        mock_client.forgot_password.assert_called_once()
        self.assertRedirects(response, reverse("login"))

    @patch("tcf_website.views.auth.boto3.client")
    def test_post_mixed_case_email_still_matches(self, mock_boto_client):
        """Email stored with mixed case is matched case-insensitively."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Stored as TestUser@virginia.edu, submitted lowercase
        response = self.client.post(self.url, {"email": "testuser@virginia.edu"})

        mock_client.forgot_password.assert_called_once()
        self.assertRedirects(response, reverse("login"))

    @patch("tcf_website.views.auth.boto3.client")
    def test_post_cognito_user_not_found_shows_error(self, mock_boto_client):
        """UserNotFoundException from Cognito shows a 'no account' error."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.forgot_password.side_effect = ClientError(
            {"Error": {"Code": "UserNotFoundException", "Message": "User not found"}},
            "ForgotPassword",
        )

        response = self.client.post(self.url, {"email": "testuser@virginia.edu"})

        self.assertEqual(response.status_code, 200)
        msg_texts = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("no account" in t.lower() for t in msg_texts))

    @patch("tcf_website.views.auth.boto3.client")
    def test_post_cognito_other_error_shows_generic_message(self, mock_boto_client):
        """A non-UserNotFoundException from Cognito shows a generic error."""
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.forgot_password.side_effect = ClientError(
            {"Error": {"Code": "InternalErrorException", "Message": "Internal error"}},
            "ForgotPassword",
        )

        response = self.client.post(self.url, {"email": "testuser@virginia.edu"})

        self.assertEqual(response.status_code, 200)
        msg_texts = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("something went wrong" in t.lower() for t in msg_texts))

    def test_authenticated_user_redirected_to_browse(self):
        """An authenticated user hitting this view is redirected to browse."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("browse"))
