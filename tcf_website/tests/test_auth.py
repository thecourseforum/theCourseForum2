"""Custom forgot-password flow (issue #1251).

Cognito's hosted UI silently no-ops password resets for unknown emails
(``prevent_user_existence_errors`` is enabled), leaving users with no
feedback. The ``forgot_password`` view checks the local account table first
and notifies the user when no account exists, then delegates to Cognito for
known accounts.
"""

from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
from django.contrib.messages import get_messages
from django.test import override_settings
from django.urls import reverse

from ..views.auth import NO_ACCOUNT_MESSAGE
from .base import TCFDataTestCase


def _messages(response):
    """Return the flat list of flash message strings on a response."""
    return [str(m) for m in get_messages(response.wsgi_request)]


@override_settings(
    COGNITO_DOMAIN="https://test-pool.auth.us-east-1.amazoncognito.com",
    COGNITO_APP_CLIENT_ID="test-client-id",
    COGNITO_APP_CLIENT_SECRET="test-secret",
    COGNITO_REGION_NAME="us-east-1",
)
class ForgotPasswordTestCase(TCFDataTestCase):
    """GET renders the form; POST branches on local-account existence."""

    def test_get_renders_form(self):
        """GET /forgot-password/ renders the reset form."""
        response = self.client.get(reverse("forgot_password"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site/auth/forgot_password.html")
        self.assertContains(response, 'name="email"')

    @patch("tcf_website.views.auth.boto3.client")
    def test_empty_email_shows_error_and_does_not_call_cognito(self, mock_client):
        """Blank email is rejected before any Cognito call."""
        response = self.client.post(reverse("forgot_password"), {"email": "  "})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any("enter your email" in m.lower() for m in _messages(response))
        )
        mock_client.assert_not_called()

    @patch("tcf_website.views.auth.boto3.client")
    def test_unknown_email_shows_no_account_message(self, mock_client):
        """An email with no local account surfaces the no-account message."""
        response = self.client.post(
            reverse("forgot_password"),
            {"email": "nobody@virginia.edu"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(NO_ACCOUNT_MESSAGE, _messages(response))
        mock_client.assert_not_called()

    @patch("tcf_website.views.auth.boto3.client")
    def test_known_email_calls_cognito_and_redirects(self, mock_client):
        """A known account triggers Cognito ``forgot_password`` and redirects."""
        cognito = MagicMock()
        mock_client.return_value = cognito

        response = self.client.post(
            reverse("forgot_password"),
            {"email": self.user1.email},
        )

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )
        cognito.forgot_password.assert_called_once()
        kwargs = cognito.forgot_password.call_args.kwargs
        self.assertEqual(kwargs["ClientId"], "test-client-id")
        self.assertEqual(kwargs["Username"], self.user1.username)
        # A client secret is configured, so a SECRET_HASH must be supplied.
        self.assertIn("SecretHash", kwargs)

    @patch("tcf_website.views.auth.boto3.client")
    def test_known_email_lookup_is_case_insensitive(self, mock_client):
        """Casing differences don't hide an existing account."""
        cognito = MagicMock()
        mock_client.return_value = cognito

        response = self.client.post(
            reverse("forgot_password"),
            {"email": self.user1.email.upper()},
        )

        self.assertRedirects(
            response,
            reverse("login"),
            fetch_redirect_response=False,
        )
        cognito.forgot_password.assert_called_once()

    @override_settings(COGNITO_APP_CLIENT_SECRET="")
    @patch("tcf_website.views.auth.boto3.client")
    def test_no_secret_hash_when_client_has_no_secret(self, mock_client):
        """Without a client secret, ``SECRET_HASH`` is omitted."""
        cognito = MagicMock()
        mock_client.return_value = cognito

        self.client.post(
            reverse("forgot_password"),
            {"email": self.user1.email},
        )

        kwargs = cognito.forgot_password.call_args.kwargs
        self.assertNotIn("SecretHash", kwargs)

    @patch("tcf_website.views.auth.boto3.client")
    def test_user_not_found_in_cognito_maps_to_no_account(self, mock_client):
        """A local account missing from Cognito is treated as no account."""
        cognito = MagicMock()
        cognito.forgot_password.side_effect = ClientError(
            {"Error": {"Code": "UserNotFoundException", "Message": "not found"}},
            "ForgotPassword",
        )
        mock_client.return_value = cognito

        response = self.client.post(
            reverse("forgot_password"),
            {"email": self.user1.email},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(NO_ACCOUNT_MESSAGE, _messages(response))

    @patch("tcf_website.views.auth.boto3.client")
    def test_generic_cognito_error_shows_retry_message(self, mock_client):
        """Any other Cognito error yields a generic retry message, not a crash."""
        cognito = MagicMock()
        cognito.forgot_password.side_effect = ClientError(
            {"Error": {"Code": "TooManyRequestsException", "Message": "slow down"}},
            "ForgotPassword",
        )
        mock_client.return_value = cognito

        response = self.client.post(
            reverse("forgot_password"),
            {"email": self.user1.email},
        )

        self.assertEqual(response.status_code, 200)
        msgs = _messages(response)
        self.assertTrue(any("try again" in m.lower() for m in msgs), msgs)
        # The generic error must not leak whether the account exists.
        self.assertNotIn(NO_ACCOUNT_MESSAGE, msgs)
