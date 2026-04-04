"""New review page (GET context + POST create)."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from ...models import Club, Course, Instructor, Semester
from ...review.forms import ReviewForm
from ...review.services import (
    club_semester_choices_payload,
    instructors_for_course_semester,
)
from ...utils import parse_mode, recent_semesters, semesters_for_course, with_mode


@login_required
def new_review(request):
    """Review creation view with context-required logic."""
    mode, is_club = parse_mode(request)

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()

            if instance.club:
                messages.success(request, f"Successfully reviewed {instance.club}!")
            else:
                messages.success(request, f"Successfully reviewed {instance.course}!")

            if instance.club:
                club_url = reverse(
                    "club",
                    kwargs={
                        "category_slug": instance.club.category.slug,
                        "club_id": instance.club.id,
                    },
                )
                return redirect(with_mode(club_url, "clubs"))
            return redirect(
                "course",
                mnemonic=instance.course.subdepartment.mnemonic,
                course_number=instance.course.number,
            )

        return _render_review_form_with_errors(request, form, is_club, mode)

    if is_club:
        return _handle_club_review_get(request, mode)
    return _handle_course_review_get(request, mode)


def _handle_course_review_get(request, mode):
    """Handle GET for course reviews."""
    course_id = request.GET.get("course")
    instructor_id = request.GET.get("instructor")

    if not course_id:
        return render(
            request,
            "site/review/review.html",
            {
                "is_club": False,
                "mode": mode,
                "course": None,
                "club": None,
                "instructor": None,
                "instructors": [],
                "semesters": recent_semesters(),
                "review_main_unlocked": False,
            },
        )

    course = get_object_or_404(
        Course.objects.select_related("subdepartment"), id=course_id
    )
    semesters = semesters_for_course(course)
    prefill_instructor = None
    prefill_semester = None
    instructors_list = []
    if instructor_id:
        prefill_instructor = get_object_or_404(Instructor, id=instructor_id)
        prefill_semester = semesters.filter(
            section__instructors=prefill_instructor
        ).first()
        if prefill_semester:
            instructors_list = list(
                instructors_for_course_semester(course.id, prefill_semester.id)
            )

    return render(
        request,
        "site/review/review.html",
        {
            "is_club": False,
            "mode": mode,
            "course": course,
            "club": None,
            "instructor": None,
            "prefill_instructor": prefill_instructor,
            "prefill_semester": prefill_semester,
            "instructors": instructors_list,
            "semesters": semesters,
            "review_main_unlocked": False,
        },
    )


def _handle_club_review_get(request, mode):
    """Handle GET for club reviews."""
    club_id = request.GET.get("club")
    semesters = recent_semesters()

    if not club_id:
        return render(
            request,
            "site/review/review.html",
            {
                "is_club": True,
                "mode": mode,
                "club": None,
                "course": None,
                "semesters": semesters,
                "club_semester_choices": club_semester_choices_payload(),
                "review_main_unlocked": False,
            },
        )

    club = get_object_or_404(Club.objects.select_related("category"), id=club_id)

    return render(
        request,
        "site/review/review.html",
        {
            "is_club": True,
            "mode": mode,
            "club": club,
            "course": None,
            "semesters": semesters,
            "club_semester_choices": club_semester_choices_payload(),
            "review_main_unlocked": True,
        },
    )


def _render_review_form_with_errors(request, form, is_club, mode):
    """Re-render the form with validation errors."""
    context: dict = {"form": form, "is_club": is_club, "mode": mode}
    base_semesters = recent_semesters()

    if is_club:
        club = form.cleaned_data.get("club")
        if not club:
            raw = form.data.get("club")
            club = (
                Club.objects.filter(pk=raw).select_related("category").first()
                if raw
                else None
            )
        context["club"] = club
        context["course"] = None
        context["instructor"] = None
        context["semesters"] = base_semesters
        context["instructors"] = []
        context["club_semester_choices"] = club_semester_choices_payload()
        context["review_main_unlocked"] = bool(form.errors) or bool(
            form.data.get("club") and form.data.get("semester")
        )
        return render(request, "site/review/review.html", context)

    course = form.cleaned_data.get("course")
    if not course:
        raw = form.data.get("course")
        course = (
            Course.objects.filter(pk=raw).select_related("subdepartment").first()
            if raw
            else None
        )

    if not course:
        context["course"] = None
        context["club"] = None
        context["instructor"] = None
        context["semesters"] = base_semesters
        context["instructors"] = []
        context["review_main_unlocked"] = bool(form.errors)
        return render(request, "site/review/review.html", context)

    context["course"] = course
    context["club"] = None
    instructor = form.cleaned_data.get("instructor")
    if not instructor:
        iid = form.data.get("instructor")
        instructor = Instructor.objects.filter(pk=iid).first() if iid else None
    context["instructor"] = instructor

    context["semesters"] = semesters_for_course(course)

    semester = form.cleaned_data.get("semester")
    if not semester:
        sid = form.data.get("semester")
        semester = Semester.objects.filter(pk=sid).first() if sid else None
    if semester:
        context["instructors"] = list(
            instructors_for_course_semester(course.id, semester.id)
        )
    else:
        context["instructors"] = []

    context["review_main_unlocked"] = bool(form.errors) or bool(
        form.data.get("course")
        and form.data.get("semester")
        and form.data.get("instructor")
    )

    return render(request, "site/review/review.html", context)
