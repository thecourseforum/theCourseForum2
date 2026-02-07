"""Auth related views."""

import logging
from base64 import b64encode
import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


logger = logging.getLogger(__name__)


def login(request):
    """Redirect to Cognito login page."""
    if request.user.is_authenticated:
        messages.success(request, "Logged in successfully!")
        return redirect("profile")

    cognito_base_url = settings.COGNITO_DOMAIN

    # Redirect to Cognito hosted UI
    cognito_login_url = (
        f"{cognito_base_url}/login?"
        + f"client_id={settings.COGNITO_APP_CLIENT_ID}&"
        + "response_type=code&"
        + "scope=email+openid+profile&"
        + f"redirect_uri={request.build_absolute_uri(settings.COGNITO_REDIRECT_URI).rstrip('/')}"
    )

    return HttpResponseRedirect(cognito_login_url)


def cognito_callback(request):
    """Handle callback from Cognito."""
    code = request.GET.get("code")

    if not code:
        messages.error(request, "Authentication failed. Please try again.")
        return redirect("index")

    try:
        # Exchange authorization code for tokens
        # Check if COGNITO_DOMAIN already has https:// prefix
        token_endpoint = f"{settings.COGNITO_DOMAIN}/oauth2/token"

        # Create basic auth header with client_id and client_secret
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
            timeout=30,  # Add reasonable timeout
        )

        if response.status_code != 200:
            logger.error("Error exchanging code for tokens: %s", response.text)
            messages.error(request, "Authentication error. Please try again.")
            return redirect("index")

        tokens = response.json()
        id_token = tokens.get("id_token")

        # Authenticate the user with our custom backend
        user = authenticate(request, token=id_token)

        if user is None:
            messages.error(request, "Authentication failed. Please try again.")
            return redirect("index")

        # Log the user in
        auth_login(request, user)
        messages.success(request, "Logged in successfully!")
        return redirect("browse")

    except (requests.RequestException, ValueError, json.JSONDecodeError) as e:
        logger.exception("Error in Cognito callback: %s", str(e))
        messages.error(request, "Authentication error. Please try again.")
        return redirect("index")


@login_required
def logout(request):
    """Logs out user and redirects to Cognito logout."""
    auth_logout(request)
    # messages.add_message(request, messages.SUCCESS, "Logged out successfully!")

    cognito_base_url = settings.COGNITO_DOMAIN

    # Redirect to Cognito logout
    cognito_logout_url = (
        f"{cognito_base_url}/logout?"
        + f"client_id={settings.COGNITO_APP_CLIENT_ID}&"
        + f"logout_uri={request.build_absolute_uri(settings.COGNITO_LOGOUT_URI).rstrip('/')}"
    )

    return HttpResponseRedirect(cognito_logout_url)
