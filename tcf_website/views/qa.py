"""View for question and answer creation."""

from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect

from ..models import Question, Answer


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
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def upvote_question(request, question_id):
    """Upvote a view."""
    if request.method == 'POST':
        question = Question.objects.get(pk=question_id)
        question.upvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})


@login_required
def downvote_question(request, question_id):
    """Downvote a view."""
    if request.method == 'POST':
        question = Question.objects.get(pk=question_id)
        question.downvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})


class AnswerForm(forms.ModelForm):
    """Form for answer creation"""
    class Meta:
        model = Answer
        fields = ['text', 'semester', 'question']


@login_required
def new_answer(request):
    """Answer creation view."""

    if request.method == 'POST':
        form = AnswerForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(request, 'Successfully added a answer!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required()
def check_duplicate(request):
    """Check for duplicate answers on qa page when user
    submits an answer for the same question.
    Used for an Ajax request in new_review.html"""

    form = AnswerForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

        # First check if user has answered the question already
        answers_on_same_class = request.user.answer_set.filter(
            question=instance.question
        )

        # An answer already exists so it's a duplicate
        if answers_on_same_class.exists():
            response = {"duplicate": True}
            return JsonResponse(response)

        # User has not answered this question;
        # proceed with standard form submission
        response = {"duplicate": False}
        return JsonResponse(response)
    return redirect('new_answer')


@login_required
def upvote_answer(request, answer_id):
    """Upvote a view."""
    if request.method == 'POST':
        answer = Answer.objects.get(pk=answer_id)
        answer.upvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})


@login_required
def downvote_answer(request, answer_id):
    """Downvote a view."""
    if request.method == 'POST':
        answer = Answer.objects.get(pk=answer_id)
        answer.downvote(request.user)
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False})
