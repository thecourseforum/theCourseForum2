"""Auth related views."""

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout
from django.contrib import messages
from django import forms


def login(request):
    """Login view."""
    if request.user.is_authenticated:
        return redirect('browse')
    return render(request, 'login/login.html')


def login_error(request):
    """Login error view."""
    return render(request, 'login/login.html', {'error': True})


class ExtraUserInfoForm(forms.Form):
    """Form to collect extra user info on sign up."""
    grad_year = forms.IntegerField(min_value=2000, max_value=2999)
    first_major = forms.CharField(required=False)
    second_major = forms.CharField(required=False)


def collect_extra_info(request):
    """Extra sign up info collection view."""
    if request.method == 'POST':
        form = ExtraUserInfoForm(request.POST)
        if form.is_valid():
            # because of FIELDS_STORED_IN_SESSION, this will get copied
            # to the request dictionary when the pipeline is resumed
            request.session['grad_year'] = form.cleaned_data['grad_year']
            request.session['first_major'] = form.cleaned_data['first_major']
            request.session['second_major'] = form.cleaned_data['second_major']
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
    return redirect('login')
