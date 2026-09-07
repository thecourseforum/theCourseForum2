"""Schedule builder queries, URLs, and compare resolution."""

from urllib.parse import urlencode

from django.db.models import Prefetch, Q
from django.urls import reverse

from ..models import Schedule, ScheduledCourse, Semester


def schedule_visible_q(user):
    """Schedules the user may open on /schedule (owned or bookmarked)."""
    return Q(user=user) | Q(viewer_bookmarks__viewer=user)


def schedule_page_url(
    *, semester_id: int | None = None, schedule_id: int | str | None = None
) -> str:
    """Builder URL: ``?schedule=`` when a row sets the term; else ``?semester=``."""
    if schedule_id:
        return f"{reverse('schedule')}?{urlencode({'schedule': schedule_id})}"
    if semester_id is not None:
        return f"{reverse('schedule')}?{urlencode({'semester': semester_id})}"
    return reverse("schedule")


def schedule_builder_return_url(request) -> str:
    """Canonical builder URL for form ``next=`` (drops ``partial`` from query)."""
    q = request.GET.copy()
    q.pop("partial", None)
    qs = q.urlencode()
    path = request.path
    return f"{path}?{qs}" if qs else path


def resolve_compare_schedule(
    request,
    user,
    selected_schedule: Schedule | None,
    active_semester: Semester | None,
) -> Schedule | None:
    """Load a schedule to compare with from ?compare= pk (any visible schedule)."""
    if active_semester is None:
        return None

    semester_id = (
        selected_schedule.semester_id
        if selected_schedule is not None
        else active_semester.pk
    )

    raw_compare = request.GET.get("compare")
    if raw_compare is None or raw_compare == "":
        return None
    try:
        pk = int(raw_compare)
    except (TypeError, ValueError):
        return None
    return (
        Schedule.objects.filter(pk=pk, semester_id=semester_id)
        .filter(schedule_visible_q(user))
        .select_related("user")
        .first()
    )


def resolve_builder_semester(request, user) -> Semester | None:
    """Pick builder term: explicit semester wins, then schedule id, else latest.

    The term combo sends ?semester= together with hidden ?schedule=. That schedule id
    may still point at the previous term until the client syncs; inferring the term
    from schedule would ignore the user's new semester and show the wrong courses.
    """
    raw_sem = request.GET.get("semester") or request.POST.get("semester")
    if raw_sem:
        sem = Semester.objects.filter(pk=raw_sem).first()
        if sem is not None:
            return sem

    raw_sched = request.GET.get("schedule") or request.POST.get("schedule_id")
    if raw_sched:
        try:
            sched = (
                Schedule.objects.filter(pk=int(raw_sched))
                .filter(schedule_visible_q(user))
                .select_related("semester")
                .first()
            )
            if sched:
                return sched.semester
        except (TypeError, ValueError):
            pass

    return Semester.latest()


def schedules_for_user(user, semester: Semester | None):
    """Owned and bookmarked schedules for one term, with courses prefetched."""
    if semester is None:
        return Schedule.objects.none()
    return (
        Schedule.objects.filter(schedule_visible_q(user), semester=semester)
        .distinct()
        .order_by("name")
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "scheduledcourse_set",
                queryset=ScheduledCourse.objects.select_related(
                    "section", "instructor"
                ),
            )
        )
    )


def schedule_data_helper(request, semester: Semester | None):
    """Schedule list and per-schedule aggregates for the schedule builder."""
    schedules = schedules_for_user(request.user, semester)
    courses_context = {}
    ratings_context = {}
    difficulty_context = {}
    credits_context = {}
    gpa_context = {}

    for s in schedules:
        s_data = s.get_schedule()
        courses_context[s.id] = s_data[0]
        credits_context[s.id] = s_data[1]
        ratings_context[s.id] = s_data[2]
        difficulty_context[s.id] = s_data[3]
        gpa_context[s.id] = s_data[4]

    return {
        "schedules": schedules,
        "courses": courses_context,
        "ratings": ratings_context,
        "difficulty": difficulty_context,
        "credits": credits_context,
        "schedules_gpa": gpa_context,
    }
