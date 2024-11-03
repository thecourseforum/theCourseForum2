"""View for question and answer creation."""

import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic.list import ListView

from ..models import Answer, Question


class QAView(ListView):
    template_name = "qa/qa.html"
    model = Question
    # context_object_name = 'questions'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Prepare Questions list
        context["questions"] = Question.display_activity(self.request.user)

        # Prepare Answers list
        questions = Question.objects.all()
        answers = {}
        for question in questions:
            answers[question.id] = Answer.display_activity(question.id, self.request.user)
        context["answers"] = answers
        return context


class QuestionForm(forms.ModelForm):
    """Form for question creation"""

    class Meta:
        model = Question
        fields = ["text", "course", "instructor"]


class DeleteQuestion(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Question deletion view."""

    model = Question

    def get_success_url(self):
        return reverse_lazy(
            "course_instructor",
            kwargs={
                "course_id": self.object.course_id,
                "instructor_id": self.object.instructor_id,
            },
        )

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate question belonging to user."""
        obj = super().get_object()
        # For security: Make sure target question belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied("You are not allowed to delete this question!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        # get the course this review is about
        course = self.object.course
        instructor = self.object.instructor

        # return success message
        return f"Successfully deleted your question for {str(course)} and {str(instructor)}!"


@login_required
def new_question(request):
    """Question creation view."""

    if request.method == "POST":
        form = QuestionForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(request, f"Successfully added a question for {instance.course}!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def edit_question(request, question_id):
    """Question modification view."""
    question = get_object_or_404(Question, pk=question_id)
    if question.user != request.user:
        raise PermissionDenied("You are not allowed to edit this question!")

    if request.method == "POST":
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            ## may have to move this to inner check
            form.save()
            instructor = question.instructor
            if instructor.objects.filter(last_name=form.fields[2]).exists():
                # check if instructor is in set of instructors for course
                # check if course chosen is taught (instructor has a set of courese)
                if form.fields[1] in instructor.departments:
                    messages.success(
                        request,
                        f"Successfully updated your question for {form.instance.course}!",
                    )
                    question.created = datetime.datetime.now()
                    question.save()
                    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        messages.error(request, form.errors)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    form = QuestionForm(instance=question)
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def upvote_question(request, question_id):
    """Upvote a view."""
    if request.method == "POST":
        question = Question.objects.get(pk=question_id)
        question.upvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


@login_required
def downvote_question(request, question_id):
    """Downvote a view."""
    if request.method == "POST":
        question = Question.objects.get(pk=question_id)
        question.downvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


class AnswerForm(forms.ModelForm):
    """Form for answer creation"""

    class Meta:
        model = Answer
        fields = ["text", "semester", "question"]


class DeleteAnswer(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Answer deletion view."""

    model = Answer

    def get_success_url(self):
        return reverse_lazy(
            "course_instructor",
            kwargs={
                "course_id": self.object.question.course_id,
                "instructor_id": self.object.question.instructor_id,
            },
        )

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate answer belonging to user."""
        obj = super().get_object()
        # For security: Make sure target question belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied("You are not allowed to delete this answer!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        # get the course this review is about
        question = self.object.question

        # return success message
        return f"Successfully deleted your answer for {str(question)}!"


@login_required
def new_answer(request):
    """Answer creation view."""

    if request.method == "POST":
        form = AnswerForm(request.POST)

        print(form)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(request, "Successfully added an answer!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        messages.error(request, "Invalid Form")
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def edit_answer(request, answer_id):
    """Answer modification view."""
    answer = get_object_or_404(Answer, pk=answer_id)
    if answer.user != request.user:
        raise PermissionDenied("You are not allowed to edit this answer!")

    if request.method == "POST":
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Successfully updated your answer for {form.instance.question}!",
            )
            answer.created = datetime.datetime.now()
            answer.save()
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        messages.error(request, form.errors)
        return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
    return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))


@login_required()
def check_duplicate(request):
    """Check for duplicate answers on qa page when user
    submits an answer for the same question.
    Used for an Ajax request in new_review.html"""

    form = AnswerForm(request.POST)
    if form.is_valid():
        instance = form.save(commit=False)

        # First check if user has answered the question already
        answers_on_same_class = request.user.answer_set.filter(question=instance.question)

        # An answer already exists so it's a duplicate
        if answers_on_same_class.exists():
            response = {"duplicate": True}
            return JsonResponse(response)

        # User has not answered this question;
        # proceed with standard form submission
        response = {"duplicate": False}
        return JsonResponse(response)
    return redirect("new_answer")


@login_required
def upvote_answer(request, answer_id):
    """Upvote a view."""
    if request.method == "POST":
        answer = Answer.objects.get(pk=answer_id)
        answer.upvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})


@login_required
def downvote_answer(request, answer_id):
    """Downvote a view."""
    if request.method == "POST":
        answer = Answer.objects.get(pk=answer_id)
        answer.downvote(request.user)
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False})
