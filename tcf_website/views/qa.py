"""View for question and answer creation."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from ..models import Question


class QuestionForm(forms.ModelForm):
    """Form for question creation"""
    class Meta:
        model = Question
        fields = ['text', 'course', 'instructor']


@login_required
def new_question(request):
    """Question creation view."""

    if request.method == 'POST':
        form = QuestionForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(request, f'Successfully added a question for {instance.course}!')
            return redirect('browse')
        return render(request, 'browse', {'form': form})
    return render(request, 'browse')
