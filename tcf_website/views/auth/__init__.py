"""Auth related views."""

import hashlib
import hmac
import json
import logging
import urllib.parse
from base64 import b64encode

import boto3
import requests
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)
User = get_user_model()


def _cognito_secret_hash(username: str) -> str:
    """Compute SecretHash for Cognito API calls when the app client has a secret."""
    message = username + settings.COGNITO_APP_CLIENT_ID
    secret = settings.COGNITO_APP_CLIENT_SECRET.encode("utf-8")
    digest = hmac.new(secret, msg=message.encode("utf-8"), digestmod=hashlib.sha256).digest()
    return b64encode(digest).decode()


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


def forgot_password(request):
    """Show a form to request a password reset.

    Validates that the email belongs to a known account before forwarding the
    request to Cognito, so users receive clear feedback rather than silence.
    """
    if request.user.is_authenticated:
        return redirect("browse")

    if request.method != "POST":
        return render(request, "site/auth/forgot_password.html")

    email = request.POST.get("email", "").strip().lower()

    if not email:
        messages.error(request, "Please enter your email address.")
        return render(request, "site/auth/forgot_password.html")

    if not User.objects.filter(email=email).exists():
        messages.error(
            request,
            "No account is associated with that email address. "
            "Sign in with your UVA email to create an account.",
        )
        return render(request, "site/auth/forgot_password.html", {"email": email})

    try:
        cognito = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION_NAME)
        kwargs: dict = {
            "ClientId": settings.COGNITO_APP_CLIENT_ID,
            "Username": email,
        }
        if settings.COGNITO_APP_CLIENT_SECRET:
            kwargs["SecretHash"] = _cognito_secret_hash(email)
        cognito.forgot_password(**kwargs)
    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code == "UserNotFoundException":
            messages.error(
                request,
                "No account is associated with that email address. "
                "Sign in with your UVA email to create an account.",
            )
        else:
            logger.exception("Cognito forgot_password error: %s", exc)
            messages.error(request, "Something went wrong. Please try again later.")
        return render(request, "site/auth/forgot_password.html", {"email": email})

    messages.success(
        request,
        "A password reset link has been sent to your email address. Please check your inbox.",
    )
    return redirect("login")
