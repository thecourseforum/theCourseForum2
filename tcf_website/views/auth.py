"""Auth related views."""

import json
from datetime import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from .browse import browse


def login(request):
    """Login view."""
    if request.user.is_authenticated:
        messages.success(request, "Logged in successfully!")
        return redirect("profile")
    return browse(request)
    # Note: For some reason the data won't load if you use render like below:
    # return render(request, 'browse/browse.html')


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
            return redirect(reverse("social:complete", args=[method]))
    else:
        form = ExtraUserInfoForm()

    return render(request, "login/extra_info_form.html", {"form": form})


def unauthenticated_index(request):
    """Index shown to non-logged in users."""
    return render(request, "landing/landing.html")


@login_required
def logout(request):
    """Logs out user."""
    auth_logout(request)
    messages.add_message(request, messages.SUCCESS, "Logged out successfully!")
    return redirect("browse")


def email_verification(request):
    """Loads Microsoft verification document in order to be an authorized
    provider for Microsoft authentication"""
    return render(
        request,
        "login/email_verification.html",
        {"address": request.session.get("email_validation_address")},
    )


def load_microsoft_verification(request):
    """Loads Microsoft verification document in order to be an authorized
    provider for Microsoft authentication"""
    with open(
        "tcf_website/microsoft-identity-association.json", encoding="UTF-8"
    ) as data_file:
        json_content = json.load(data_file)
    return JsonResponse(json_content)
