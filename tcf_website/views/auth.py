from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout, login
from django.http import JsonResponse
from django.core.serializers import serialize
from django.core.serializers.json import DjangoJSONEncoder
from django import forms

from ..models import User

def login(request):
    return render(request, 'login/login.html')

def login_error(request):
    return render(request, 'login/login.html', {'error': True})

class ExtraUserInfoForm(forms.Form):
    grad_year = forms.IntegerField()

def collect_extra_info(request):
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
        form = GradYearForm()

    return render(request, "login/extra_info_form.html", {'form': form})

@login_required
def logout(request):
    """Logs out user"""
    auth_logout(request)
    return redirect('login')
