"""Auth related views."""

import logging
import requests
from base64 import b64encode
from datetime import datetime

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse

from .browse import browse

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
        + f"response_type=code&"
        + f"scope=email+openid+profile&"
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
                "redirect_uri": request.build_absolute_uri(settings.COGNITO_REDIRECT_URI).rstrip(
                    "/"
                ),
            },
        )

        if response.status_code != 200:
            logger.error(f"Error exchanging code for tokens: {response.text}")
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

    except Exception as e:
        logger.exception(f"Error in Cognito callback: {str(e)}")
        messages.error(request, "Authentication error. Please try again.")
        return redirect("index")


def login_error(request):
    """Login error view."""
    messages.error(
        request,
        "There was an error logging you in. Please make \
                   sure you're using an @virginia.edu email address.",
    )
    return browse(request)


def password_error(request):
    """Incorrect password error view."""
    messages.error(
        request,
        "There was an error logging you in. Please check \
                    your email and password",
    )
    return browse(request)


class ExtraUserInfoForm(forms.Form):
    """Form to collect extra user info on sign up."""

    current_yr = datetime.now().year
    max_yr = current_yr + 6
    grad_year = forms.IntegerField(
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1900",
                "max": max_yr,
                "value": current_yr,
            }
        )
    )


def collect_extra_info(request, method):
    """Extra sign up info collection view."""
    if request.method == "POST":
        form = ExtraUserInfoForm(request.POST)
        if form.is_valid():
            # because of FIELDS_STORED_IN_SESSION, this will get copied
            # to the request dictionary when the pipeline is resumed
            request.session["grad_year"] = form.cleaned_data["grad_year"]

            # once we have the grad_year stashed in the session, we can
            # tell the pipeline to resume by using the "complete" endpoint
            return redirect(
                reverse("social:complete", args=[method])
                + "?verification_code="
                + request.GET["verification_code"]
                + "&partial_token="
                + request.GET["partial_token"]
            )
    else:
        form = ExtraUserInfoForm()

    return render(request, "login/extra_info_form.html", {"form": form})


def unauthenticated_index(request):
    """Index shown to non-logged in users."""
    return render(request, "landing/landing.html")


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
