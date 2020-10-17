"""Views for user profile."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django import forms
import logging
logger = logging.getLogger(__name__)

class ProfileForm(forms.Form):
    first_name = forms.CharField(label='First Name', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Last Name', max_length=255, widget=forms.TextInput(attrs={'class': 'form-control'}))
    graduation_year = forms.IntegerField(label='Graduation Year', widget=forms.NumberInput(attrs={'class': 'form-control'}))


@login_required
def profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = ProfileForm(request.POST, label_suffix='')

        if form.is_valid():
            logger.error(form.cleaned_data['test_field'])
    else:
        form = ProfileForm(label_suffix='')
    return render(request, 'profile/profile.html', {'form': form})


@login_required
def reviews(request):
    """User reviews view."""
    return render(request, 'reviews/user_reviews.html')
