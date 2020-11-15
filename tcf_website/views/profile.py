"""Views for user profile."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from ..models import User


class ProfileForm(ModelForm):
    """Form updating user profile."""
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'graduation_year',
            'first_major',
            'second_major']

        # Add the form-control class to make the form work with Bootstrap
        widgets = {
            'first_name': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'last_name': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'graduation_year': forms.NumberInput(
                attrs={
                    'class': 'form-control'}),
            'first_major': forms.TextInput(
                attrs={
                    'class': 'form-control'}),
            'second_major': forms.TextInput(
                attrs={
                    'class': 'form-control'}), }


@login_required
def profile(request):
    """User profile view."""
    if request.method == 'POST':
        form = ProfileForm(
            request.POST,
            label_suffix='',
            instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile was updated successfully!')
        else:
            messages.error(request, form.errors)
        return HttpResponseRedirect('/profile')

    form = ProfileForm(label_suffix='', instance=request.user)
    return render(request, 'profile/profile.html', {'form': form})


@login_required
def reviews(request):
    """User reviews view."""
    return render(request, 'reviews/user_reviews.html')
