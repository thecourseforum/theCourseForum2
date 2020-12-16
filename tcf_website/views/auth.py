"""Auth related views."""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django import forms
from .browse import browse


def login(request):
    """Login view."""
    if request.user.is_authenticated:
        messages.success(request, "Logged in successfully!")
        return redirect('profile')
    return browse(request)
    # Note: For some reason the data won't load if you use render like below:
    # return render(request, 'browse/browse.html')


def login_error(request):
    """Login error view."""
    messages.error(request, 'There was an error logging you in. Please make \
                   sure you\'re using an @virginia.edu email address.')
    return browse(request)


class ExtraUserInfoForm(forms.Form):
    """Form to collect extra user info on sign up."""
    grad_year = forms.IntegerField()


def collect_extra_info(request):
    """Extra sign up info collection view."""
    if request.method == 'POST':
        form = ExtraUserInfoForm(request.POST)
        if form.is_valid():
            # because of FIELDS_STORED_IN_SESSION, this will get copied
            # to the request dictionary when the pipeline is resumed
            request.session['grad_year'] = form.cleaned_data['grad_year']

            # once we have the grad_year stashed in the session, we can
            # tell the pipeline to resume by using the "complete" endpoint
            return redirect(reverse('social:complete', args=["google-oauth2"]))
    else:
        form = ExtraUserInfoForm()

    return render(request, "login/extra_info_form.html", {'form': form})


def unauthenticated_index(request):
    """Index shown to non-logged in users."""
    return render(request, "landing/landing.html")


@login_required
def logout(request):
    """Logs out user."""
    auth_logout(request)
    messages.add_message(request, messages.SUCCESS, "Logged out successfully!")
    return redirect('browse')
