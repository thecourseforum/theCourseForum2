"""Quick-rate page: rate several past courses with a few taps each."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from ...models import Course, Instructor, QuickRateDismissal
from ...review.forms import ReviewForm
from ...review.quick_rate import candidates_for
from ...review.services import is_duplicate_review_for_user
from ...utils import semesters_for_course


@login_required
def quick_rate(request):
    """List the user's ratable courses; `?course=<id>` adds one ad-hoc row."""
    adhoc_course = None
    adhoc_semesters = []
    course_id = request.GET.get("course", "")
    if course_id.isdigit():
        adhoc_course = get_object_or_404(
            Course.objects.select_related("subdepartment"), id=int(course_id)
        )
        adhoc_semesters = semesters_for_course(adhoc_course)

    return render(
        request,
        "site/review/quick_rate.html",
        {
            "candidates": candidates_for(request.user),
            "adhoc_course": adhoc_course,
            "adhoc_semesters": adhoc_semesters,
            "rated_count": request.user.review_set.filter(course__isnull=False).count(),
        },
    )


@login_required
@require_POST
def quick_rate_submit(request):
    """Create one course review from a quick-rate row. JSON in, JSON out."""
    form = ReviewForm(request.POST)
    if not form.is_valid():
        return JsonResponse(
            {"ok": False, "errors": form.errors.get_json_data()}, status=400
        )

    instance = form.save(commit=False)
    if instance.club_id:
        return JsonResponse(
            {
                "ok": False,
                "errors": {"__all__": [{"message": "Quick rate is for courses only."}]},
            },
            status=400,
        )
    if is_duplicate_review_for_user(request.user, instance):
        return JsonResponse({"ok": False, "duplicate": True}, status=409)

    instance.user = request.user
    instance.save()
    return JsonResponse(
        {"ok": True, "review_id": instance.id, "has_text": bool(instance.text)}
    )


@login_required
@require_POST
def quick_rate_dismiss(request):
    """Record that the user did not take a suggested course–instructor pair."""
    try:
        course_id = int(request.POST["course"])
        instructor_id = int(request.POST["instructor"])
    except (KeyError, ValueError):
        return JsonResponse({"ok": False}, status=400)

    if not Course.objects.filter(id=course_id).exists():
        return JsonResponse({"ok": False}, status=400)
    if not Instructor.objects.filter(id=instructor_id).exists():
        return JsonResponse({"ok": False}, status=400)

    QuickRateDismissal.objects.get_or_create(
        user=request.user, course_id=course_id, instructor_id=instructor_id
    )
    return JsonResponse({"ok": True})
