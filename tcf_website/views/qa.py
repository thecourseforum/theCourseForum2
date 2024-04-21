"""View for question and answer creation."""

import datetime
from django import forms
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, get_object_or_404, render

from ..models import Question, Answer


class QuestionForm(forms.ModelForm):
    """Form for question creation"""
    class Meta:
        model = Question
        fields = ['text', 'course', 'instructor']


class DeleteQuestion(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Question deletion view."""
    model = Question

    def get_success_url(self):
        return reverse_lazy(
            'course_instructor',
            kwargs={
                'course_id': self.object.course_id,
                'instructor_id': self.object.instructor_id})

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate question belonging to user."""
        obj = super().get_object()
        # For security: Make sure target question belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied(
                "You are not allowed to delete this question!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        # get the course this review is about
        course = self.object.course
        instructor = self.object.instructor

        # return success message
        return f"Successfully deleted your question for {str(course)} and {str(instructor)}!"


# @login_required
def new_question(request): 
    """Question creation view."""
    # Collect form data into Question model instance.
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            # TODO: extend field
            instance.save()
            return render(request, 'qa/new_question.html')
        return render(request, 'qa/new_question.html', {'form': form})
    return render(request, 'qa/new_question.html')

    # Old Q&A Functionality
    """if request.method == 'POST':
        form = QuestionForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(request, f'Successfully added a question for {instance.course}!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))"""


@login_required
def edit_question(request, question_id):
    """Question modification view."""
    question = get_object_or_404(Question, pk=question_id)
    if question.user != request.user:
        raise PermissionDenied('You are not allowed to edit this question!')

    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Successfully updated your question for {form.instance.course}!')
            question.created = datetime.datetime.now()
            question.save()
            return render(request, 'qa/edit_question.html', {'form': form})
        messages.error(request, form.errors)
        return render(request, 'qa/edit_question.html', {'form': form})
    form = QuestionForm(instance=question)
    return render(request, 'qa/edit_question.html', {'form': form})


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


class DeleteAnswer(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Answer deletion view."""
    model = Answer

    def get_success_url(self):
        return reverse_lazy(
            'course_instructor',
            kwargs={
                'course_id': self.object.question.course_id,
                'instructor_id': self.object.question.instructor_id})

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate answer belonging to user."""
        obj = super().get_object()
        # For security: Make sure target question belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied(
                "You are not allowed to delete this answer!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        # get the course this review is about
        question = self.object.question

        # return success message
        return f"Successfully deleted your answer for {str(question)}!"


#@login_required
def new_answer(request):
    """Answer creation view."""
    # Collect form data into Answer model instance.
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        return render(request, 'qa/answer_form.html', {'form': form})
    return render(request, 'qa/answer_form.html')

    # Old Q&A Functionality
    """def new_answer(request):
        """"""Answer creation view.""""""

        if request.method == 'POST':
            form = AnswerForm(request.POST)
            
            print(form)
            #return redner(request, html, provide context)

            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = request.user

                instance.save()

                messages.success(request, 'Successfully added an answer!')
                return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
            messages.error(request, "Invalid Form")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))"""


@login_required
def edit_answer(request, answer_id):
    """Answer modification view."""
    answer = get_object_or_404(Answer, pk=answer_id)
    if answer.user != request.user:
        raise PermissionDenied('You are not allowed to edit this answer!')

    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Successfully updated your answer for {form.instance.question}!')
            answer.created = datetime.datetime.now()
            answer.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
        messages.error(request, form.errors)
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
