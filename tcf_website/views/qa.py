"""View for question and answer creation."""

import datetime

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin  # For class-based views
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.postgres.search import TrigramSimilarity
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views import generic

from ..models import Answer, Course, Department, Instructor, Question, Semester


def _question_target_label(question):
    """Return user-facing label for what a question is about."""
    if question.course:
        return str(question.course)
    if question.department:
        return question.department.name
    return "selected topic"


def qa_dashboard(request):
    """Q&A Dashboard view."""
    search_query = request.GET.get("q", "").strip()
    department_filter = request.GET.get("department", "").strip()
    course_filter = request.GET.get("course", "")
    scope_filter = request.GET.get("scope", "").strip()
    selected_question_id = request.GET.get("question", None)
    try:
        selected_question_id = (
            int(selected_question_id) if selected_question_id else None
        )
    except (TypeError, ValueError):
        selected_question_id = None

    # Base queryset annotated with vote totals
    questions = (
        Question.objects.select_related(
            "course",
            "course__subdepartment",
            "course__subdepartment__department",
            "department",
            "instructor",
            "user",
        )
        .exclude(text="")
        .annotate(
            sum_q_votes=models.functions.Coalesce(
                models.Sum("votequestion__value"), models.Value(0)
            )
        )
    )

    if request.user.is_authenticated:
        questions = questions.annotate(
            user_q_vote=models.functions.Coalesce(
                models.Sum(
                    "votequestion__value",
                    filter=models.Q(votequestion__user=request.user),
                ),
                models.Value(0),
            )
        )

    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query)
            | Q(text__icontains=search_query)
            | Q(department__name__icontains=search_query)
            | Q(course__subdepartment__mnemonic__icontains=search_query)
            | Q(course__number__icontains=search_query)
        )

    if department_filter:
        questions = questions.filter(
            Q(department_id=department_filter)
            | Q(course__subdepartment__department_id=department_filter)
        )

    if course_filter:
        questions = questions.filter(course_id=course_filter)
    elif department_filter and scope_filter == "department_broad":
        questions = questions.filter(department_id=department_filter, course__isnull=True)

    questions = questions.order_by("-created")

    # Determine selected question
    selected_question = None
    answers = []
    answer_count = 0
    if selected_question_id:
        try:
            selected_question = questions.get(id=selected_question_id)
        except Question.DoesNotExist:
            pass
    if selected_question is None:
        selected_question = questions.first()

    if selected_question:
        answers = Answer.display_activity(
            question_id=selected_question.id,
            user=request.user,
        )
        answer_count = (
            Answer.objects.filter(question=selected_question).exclude(text="").count()
        )

    # Courses that have at least one course-targeted question (for filter dropdown)
    courses_with_questions = (
        Course.objects.filter(question__isnull=False, question__course__isnull=False)
        .select_related("subdepartment", "subdepartment__department")
        .distinct()
        .order_by(
            "subdepartment__department__name",
            "subdepartment__mnemonic",
            "number",
        )
    )

    # Departments represented in either course-targeted or department-targeted questions.
    departments_list = list(
        Department.objects.filter(
            Q(question__isnull=False) | Q(subdepartment__course__question__isnull=False)
        )
        .distinct()
        .order_by("name")
        .values("id", "name")
    )

    selected_course_obj = None
    selected_department = None
    selected_scope = "department_broad" if scope_filter == "department_broad" else ""
    if course_filter:
        selected_course_obj = courses_with_questions.filter(pk=course_filter).first()
        if selected_course_obj:
            selected_department = selected_course_obj.subdepartment.department.id
    elif department_filter:
        try:
            selected_department = int(department_filter)
        except (TypeError, ValueError):
            selected_department = None

    semesters = Semester.objects.order_by("-number")[:20]

    context = {
        "questions": questions,
        "selected_question": selected_question,
        "answers": answers,
        "courses_with_questions": courses_with_questions,
        "departments_list": departments_list,
        "search_query": search_query,
        "selected_course": course_filter,
        "selected_course_obj": selected_course_obj,
        "selected_department": selected_department,
        "selected_scope": selected_scope,
        "semesters": semesters,
        "answer_count": answer_count,
    }

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        posts_html = render_to_string(
            "qa/_question_list.html",
            context,
            request=request,
        )
        detail_html = render_to_string(
            "qa/_question_content.html",
            context,
            request=request,
        )
        return JsonResponse(
            {
                "posts_html": posts_html,
                "detail_html": detail_html,
                "selected_question_id": (
                    selected_question.id if selected_question else None
                ),
            }
        )

    return render(request, "qa/qa_dashboard.html", context)


@login_required
def create_question(request):
    """Create a new question via the Q&A dashboard modal."""
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
        return redirect("qa")
    return redirect("qa")


def question_detail(request, question_id):
    """AJAX endpoint: returns rendered HTML partial for a question + its answers."""
    qs = Question.objects.select_related(
        "course",
        "course__subdepartment",
        "course__subdepartment__department",
        "department",
        "instructor",
        "user",
    ).annotate(
        sum_q_votes=models.functions.Coalesce(
            models.Sum("votequestion__value"), models.Value(0)
        ),
    )
    if request.user.is_authenticated:
        qs = qs.annotate(
            user_q_vote=models.functions.Coalesce(
                models.Sum(
                    "votequestion__value",
                    filter=models.Q(votequestion__user=request.user),
                ),
                models.Value(0),
            ),
        )
    question = get_object_or_404(qs, pk=question_id)

    answers = Answer.display_activity(question_id=question.id, user=request.user)
    answer_count = Answer.objects.filter(question=question).exclude(text="").count()
    semesters = Semester.objects.order_by("-number")[
        :20
    ]  # for the answer form in _question_detail.html

    return render(
        request,
        "qa/_question_detail.html",
        {
            "question": question,
            "answers": answers,
            "answer_count": answer_count,
            "semesters": semesters,
        },
    )


def search_courses_qa(request):
    """API: search courses and departments for the New Post modal."""
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    # Shows recent courses
    recent_courses = Course.objects.filter(semester_last_taught__year__gte=2022)

    # Check for exact match
    courses = (
        recent_courses.filter(combined_mnemonic_number__istartswith=query)
        .select_related("subdepartment", "semester_last_taught")
        .order_by("combined_mnemonic_number")[:10]
    )

    ## Falls back to TrigramSimilarity if exact match doesnt exist
    if not courses.exists():
        courses = (
            recent_courses.annotate(
                similarity=TrigramSimilarity("combined_mnemonic_number", query)
            )
            .filter(similarity__gte=0.3)
            .select_related("subdepartment", "semester_last_taught")
            .order_by("-similarity")[:10]
        )

    departments = (
        Department.objects.filter(name__icontains=query)
        .order_by("name")[:10]
    )

    results = [
        {
            "id": course.id,
            "type": "course",
            "code": f"{course.subdepartment.mnemonic} {course.number}",
            "title": course.title,
        }
        for course in courses
    ]
    results.extend(
        {
            "id": department.id,
            "type": "department",
            "code": department.name,
            "title": "Department",
        }
        for department in departments
    )
    return JsonResponse({"results": results})


def get_instructors_for_course(request, course_id):
    """API: get instructors who have taught a given course."""
    course = get_object_or_404(Course, pk=course_id)
    instructors = (
        Instructor.objects.filter(section__course=course, hidden=False)
        .distinct()
        .order_by("last_name", "first_name")
    )
    return JsonResponse(
        {
            "instructors": [
                {"id": i.id, "name": f"{i.first_name} {i.last_name}".strip()}
                for i in instructors
            ]
        }
    )


class QuestionForm(forms.ModelForm):
    """Form for question creation"""

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get("course")
        department = cleaned_data.get("department")
        instructor = cleaned_data.get("instructor")

        if not course and not department:
            raise forms.ValidationError("Please select a course or a department.")

        if department:
            # Department target takes precedence and clears course/instructor noise.
            cleaned_data["course"] = None
            cleaned_data["instructor"] = None
        elif instructor and not course:
            raise forms.ValidationError(
                "Instructor can only be selected for course questions."
            )

        return cleaned_data

    class Meta:
        model = Question
        fields = ["title", "text", "course", "department", "instructor"]


class DeleteQuestion(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Question deletion view."""

    model = Question

    def get_success_url(self):
        return reverse_lazy("qa")

    def get_object(self):  # pylint: disable=arguments-differ
        """Override DeleteView's function to validate question belonging to user."""
        obj = super().get_object()
        # For security: Make sure target question belongs to the current user
        if obj.user != self.request.user:
            raise PermissionDenied("You are not allowed to delete this question!")
        return obj

    def get_success_message(self, cleaned_data) -> str:
        """Overrides SuccessMessageMixin's get_success_message method."""
        return f"Successfully deleted your question for {_question_target_label(self.object)}!"


@login_required
def new_question(request):
    """Question creation view."""

    if request.method == "POST":
        form = QuestionForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user

            instance.save()

            messages.success(
                request,
                f"Successfully added a question for {_question_target_label(instance)}!",
            )
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
            form.save()
            messages.success(
                request,
                f"Successfully updated your question for {_question_target_label(form.instance)}!",
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
    """Upvote a question."""
    if request.method == "POST":
        question = Question.objects.get(pk=question_id)
        question.upvote(request.user)
        net = (
            question.votequestion_set.aggregate(total=models.Sum("value"))["total"] or 0
        )
        vote_obj = question.votequestion_set.filter(user=request.user).first()
        user_vote = vote_obj.value if vote_obj else 0
        return JsonResponse({"ok": True, "votes": net, "user_vote": user_vote})
    return JsonResponse({"ok": False})


@login_required
def downvote_question(request, question_id):
    """Downvote a question."""
    if request.method == "POST":
        question = Question.objects.get(pk=question_id)
        question.downvote(request.user)
        net = (
            question.votequestion_set.aggregate(total=models.Sum("value"))["total"] or 0
        )
        vote_obj = question.votequestion_set.filter(user=request.user).first()
        user_vote = vote_obj.value if vote_obj else 0
        return JsonResponse({"ok": True, "votes": net, "user_vote": user_vote})
    return JsonResponse({"ok": False})


class AnswerForm(forms.ModelForm):
    """Form for answer creation"""

    class Meta:
        model = Answer
        fields = ["text", "semester", "question"]


class ReplyForm(forms.ModelForm):
    """Form for reply creation (reply to an answer)"""

    class Meta:
        model = Answer
        fields = ["text", "semester", "question", "parent_answer"]


class DeleteAnswer(LoginRequiredMixin, SuccessMessageMixin, generic.DeleteView):
    """Answer deletion view."""

    model = Answer

    def get_success_url(self):
        return reverse_lazy("qa")

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


@login_required
def new_reply(request):
    """Reply creation view (reply to an answer)."""
    if request.method == "POST":
        form = ReplyForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            messages.success(request, "Successfully added a reply!")
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))
        messages.error(request, "Invalid Form")
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
    return redirect("new_answer")


@login_required
def upvote_answer(request, answer_id):
    """Upvote an answer."""
    if request.method == "POST":
        answer = Answer.objects.get(pk=answer_id)
        answer.upvote(request.user)
        net = answer.voteanswer_set.aggregate(total=models.Sum("value"))["total"] or 0
        vote_obj = answer.voteanswer_set.filter(user=request.user).first()
        user_vote = vote_obj.value if vote_obj else 0
        return JsonResponse({"ok": True, "votes": net, "user_vote": user_vote})
    return JsonResponse({"ok": False})


@login_required
def downvote_answer(request, answer_id):
    """Downvote an answer."""
    if request.method == "POST":
        answer = Answer.objects.get(pk=answer_id)
        answer.downvote(request.user)
        net = answer.voteanswer_set.aggregate(total=models.Sum("value"))["total"] or 0
        vote_obj = answer.voteanswer_set.filter(user=request.user).first()
        user_vote = vote_obj.value if vote_obj else 0
        return JsonResponse({"ok": True, "votes": net, "user_vote": user_vote})
    return JsonResponse({"ok": False})
    return JsonResponse({"ok": False})
    return JsonResponse({"ok": False})
    return JsonResponse({"ok": False})
    return JsonResponse({"ok": False})
    return JsonResponse({"ok": False})
