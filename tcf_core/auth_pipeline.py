# pylint: disable=unused-argument
# pylint: disable=keyword-arg-before-vararg
# pylint: disable=inconsistent-return-statements
# pylint: disable=line-too-long
"""Custom authentication pipeline steps."""

from functools import wraps

import social_core.pipeline.mail
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from social_core.exceptions import InvalidEmail
from social_core.strategy import BaseStrategy

from tcf_website.models import User


def auth_allowed(backend, details, response, *args, **kwargs):
    """Route unallowed auth attempts to error page."""
    if not backend.auth_allowed(response, details):
        return redirect("/login/error", error=True)
    return None


def password_validation(backend, details, request, response, *args, **kwargs):
    """Route unallowed auth attempts to error page."""
    if backend.name != "email":
        return
    if not response.get("login"):
        if response.get("password") != response.get("password_confirm"):
            return render(
                request,
                "login/register_form.html",
                {"error_message": ["passwords do not match"]},
            )
        try:
            validate_password(response.get("password"))
        except ValidationError as err:
            return render(request, "login/register_form.html", {"error_message": err})
    else:
        if not User.objects.filter(email=response.get("email")).exists():
            return redirect("/login/password_error", error=True)
    return {"password": response.get("password")}


def mail_validation(*args, **kwargs):
    """Wrapper for social_core.pipeline.mail.mail_validation which ignores InvalidEmail exception."""
    result = None
    try:
        result = social_core.pipeline.mail.mail_validation(*args, **kwargs)
    except InvalidEmail:
        pass  # do nothing
    return result


def implement_partial_token_persistence():
    """Apply a wrapper over strategy.clean_partial_pipeline() to implement partial token persistence."""
    if hasattr(BaseStrategy.clean_partial_pipeline, "wrapped"):
        return  # already wrapped

    def wrapper(orig_func):
        @wraps(orig_func)
        def new_func(self, *args, **kwargs):
            if self.session.get("persist_partial_token", default=False):
                # Persist partial token
                pass
            else:
                # Delete partial token
                orig_func(self, *args, **kwargs)

        return new_func

    # Apply wrapper
    wrapped_func = wrapper(BaseStrategy.clean_partial_pipeline)
    wrapped_func.wrapped = True
    BaseStrategy.clean_partial_pipeline = wrapped_func


def collect_extra_info(strategy, backend, request, details, user=None, *args, **kwargs):
    """Collect extra information on sign up."""

    # Disable partial token persistence
    implement_partial_token_persistence()
    strategy.session_set("persist_partial_token", False)

    if user:
        return {"is_new": False}

    # session 'grad_year' is set by the pipeline infrastructure
    # because it exists in FIELDS_STORED_IN_SESSION
    grad_year = strategy.session_get("grad_year", None)
    if not grad_year:
        # If grad year isn't available yet, persist the current partial token
        strategy.session_set("persist_partial_token", True)

        # if we return something besides a dict or None, then that is
        # returned to the user -- in this case we will redirect to a
        # view that can be used to get a password
        if "verification_code" in request.GET:
            # For email/password login
            return redirect(
                f"/login/collect_extra_info/{backend.name}"
                + "?verification_code="
                + request.GET["verification_code"]
                + "&partial_token="
                + request.GET["partial_token"]
            )
        else:
            # For social auth login
            return redirect(f"/login/collect_extra_info/{backend.name}")


USER_FIELDS = ["email", "username"]


def create_user(strategy, details, backend, user=None, *args, **kwargs):
    """
    Add extra information to saved user.

    Based on https://github.com/python-social-auth/social-core/blob/3.3.3/social_core/pipeline/user.py#L64
    """
    # User has registered previously.
    if user:
        if backend.name == "email":
            details["fullname"] = user.full_name
            details["first_name"] = user.first_name
            details["last_name"] = user.last_name
        return {"is_new": False, "details": details}

    fields = dict(
        (name, kwargs.get(name, details.get(name)))
        for name in backend.setting("USER_FIELDS", USER_FIELDS)
    )
    if not fields:
        return None

    # Add graduation year and computing ID. This is extra info not
    # automatically collected by python-social-auth.
    fields["graduation_year"] = strategy.session_get("grad_year", None)
    fields["computing_id"] = kwargs.get("email", details.get("email")).split("@")[0]

    return {"is_new": True, "user": strategy.create_user(**fields)}


def check_user_password(strategy, backend, user, is_new=False, password="", *args, **kwargs):
    """
    Saves password to user object if a new user (registering).
    Otherwise, validates given password is correct.
    """
    if backend.name != "email":
        return

    if is_new:
        user.set_password(password)
        user.save()
    elif not user.check_password(password):
        return redirect("/login/password_error", error=True)


def validate_email(strategy, backend, code, partial_token):
    """
    Used in auth pipeline to generate the verificaion email for account creation
    """
    if not code.verified:
        url = (
            strategy.build_absolute_uri(reverse("social:complete", args=(backend.name,)))
            + "?verification_code="
            + code.code
            + "&partial_token="
            + partial_token
        )
        send_mail(
            "theCourseForum Email Verification",
            f"Please go to {url} to confirm your new account for theCourseForum",
            settings.EMAIL_HOST_USER,
            [code.email],
            fail_silently=False,
        )
