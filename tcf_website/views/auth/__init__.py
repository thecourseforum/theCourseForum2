"""Auth related views."""

import hashlib
import hmac
import json
import logging
import urllib.parse
from base64 import b64encode

import boto3
import requests
from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# Shown when the submitted email has no local account. Deliberately identical
# to the message rendered for Cognito's ``UserNotFoundException`` so the two
# "no account" paths are indistinguishable to the user (see issue #1251).
NO_ACCOUNT_MESSAGE = (
    "No account is associated with that email address. "
    "Sign in with your UVA email to create an account."
)


def login(request):
    """Redirect to Cognito login page."""
    if request.user.is_authenticated:
        messages.success(request, "Logged in successfully!")
        return redirect("profile")

    cognito_base_url = settings.COGNITO_DOMAIN
    next_url = request.GET.get("next")

    cognito_login_url = (
        f"{cognito_base_url}/login?"
        + f"client_id={settings.COGNITO_APP_CLIENT_ID}&"
        + "response_type=code&"
        + "scope=email+openid+profile&"
        + f"redirect_uri={request.build_absolute_uri(settings.COGNITO_REDIRECT_URI).rstrip('/')}"
    )

    if next_url:
        cognito_login_url += f"&state={urllib.parse.quote(next_url)}"

    return HttpResponseRedirect(cognito_login_url)


def cognito_callback(request):
    """Handle callback from Cognito."""
    code = request.GET.get("code")

    if not code:
        messages.error(request, "Authentication failed. Please try again.")
        return redirect("index")

    try:
        token_endpoint = f"{settings.COGNITO_DOMAIN}/oauth2/token"

        auth_header = b64encode(
            f"{settings.COGNITO_APP_CLIENT_ID}:{settings.COGNITO_APP_CLIENT_SECRET}".encode()
        ).decode()

        response = requests.post(
            token_endpoint,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "grant_type": "authorization_code",
                "client_id": settings.COGNITO_APP_CLIENT_ID,
                "code": code,
                "redirect_uri": request.build_absolute_uri(
                    settings.COGNITO_REDIRECT_URI
                ).rstrip("/"),
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error("Error exchanging code for tokens: %s", response.text)
            messages.error(request, "Authentication error. Please try again.")
            return redirect("index")

        tokens = response.json()
        id_token = tokens.get("id_token")

        user = authenticate(request, token=id_token)

        if user is None:
            messages.error(request, "Authentication failed. Please try again.")
            return redirect("index")

        auth_login(request, user)
        messages.success(request, "Logged in successfully!")

        next_url = request.GET.get("state")
        if next_url and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(next_url)

        return redirect("browse")

    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        logger.exception("Error in Cognito callback: %s", str(e))
        messages.error(request, "Authentication error. Please try again.")
        return redirect("index")


@login_required
@require_POST
def logout(request):
    """Logs out user and redirects to Cognito logout."""
    auth_logout(request)

    cognito_base_url = settings.COGNITO_DOMAIN

    cognito_logout_url = (
        f"{cognito_base_url}/logout?"
        + f"client_id={settings.COGNITO_APP_CLIENT_ID}&"
        + f"logout_uri={request.build_absolute_uri(settings.COGNITO_LOGOUT_URI).rstrip('/')}"
    )

    return HttpResponseRedirect(cognito_logout_url)


def _cognito_secret_hash(username):
    """Return the Cognito ``SECRET_HASH`` for ``username``.

    Required only when the app client is configured with a client secret.
    It is the base64-encoded HMAC-SHA256 of ``username + client_id`` keyed by
    the client secret, per the AWS Cognito docs.
    """
    message = f"{username}{settings.COGNITO_APP_CLIENT_ID}".encode()
    key = settings.COGNITO_APP_CLIENT_SECRET.encode()
    digest = hmac.new(key, message, hashlib.sha256).digest()
    return b64encode(digest).decode()


def forgot_password(request):
    """Custom password-reset entry point.

    Cognito's hosted UI is configured with ``prevent_user_existence_errors``
    enabled, so a reset request for an unknown email silently no-ops and the
    user is left with no feedback (issue #1251). This view checks the local
    account table first: if no account matches the submitted email, it tells
    the user to sign in with their UVA email to create one; otherwise it asks
    Cognito to send the reset code and redirects to login.
    """
    if request.method != "POST":
        return render(request, "site/auth/forgot_password.html")

    email = request.POST.get("email", "").strip()

    if not email:
        messages.error(request, "Please enter your email address.")
        return render(request, "site/auth/forgot_password.html")

    user_model = get_user_model()
    # Emails are stored from the Cognito ``email`` claim; match
    # case-insensitively so casing differences don't hide an account.
    account = user_model.objects.filter(email__iexact=email).first()

    if account is None:
        messages.error(request, NO_ACCOUNT_MESSAGE)
        return render(request, "site/auth/forgot_password.html")

    # Cognito usernames are the local part of the UVA email (see
    # ``CognitoBackend.authenticate``), and the reset code is delivered to the
    # address on file, so drive the Cognito call with the stored username.
    username = account.username

    try:
        client = boto3.client(
            "cognito-idp", region_name=settings.COGNITO_REGION_NAME
        )
        params = {
            "ClientId": settings.COGNITO_APP_CLIENT_ID,
            "Username": username,
        }
        if settings.COGNITO_APP_CLIENT_SECRET:
            params["SecretHash"] = _cognito_secret_hash(username)

        client.forgot_password(**params)
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "")
        if error_code == "UserNotFoundException":
            # Local account exists but Cognito has no matching user. Treat it
            # the same as "no account" rather than leaking the discrepancy.
            messages.error(request, NO_ACCOUNT_MESSAGE)
            return render(request, "site/auth/forgot_password.html")

        logger.error("Cognito forgot_password failed: %s", exc)
        messages.error(
            request,
            "We couldn't start a password reset right now. Please try again "
            "later.",
        )
        return render(request, "site/auth/forgot_password.html")
    except BotoCoreError as exc:
        logger.exception("Cognito forgot_password client error: %s", exc)
        messages.error(
            request,
            "We couldn't start a password reset right now. Please try again "
            "later.",
        )
        return render(request, "site/auth/forgot_password.html")

    messages.success(
        request,
        "If an account exists for that email, we've sent a password reset "
        "link. Check your inbox.",
    )
    return redirect("login")
