"""XHR / JSON helpers for schedule builder views."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse

from ...utils import safe_next_url


def accepts_schedule_json(request) -> bool:
    """True when the client expects a JSON body (modal / fetch flows)."""
    accept = request.headers.get("Accept", "")
    return "application/json" in accept


def is_schedule_grid_partial_request(request):
    """True when client requests the schedule builder grid HTML fragment only."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "grid"
    )


def is_schedule_compare_pick_partial_request(request):
    """XHR fragment: list of schedules to compare with (modal body)."""
    return (
        request.headers.get("X-Requested-With") == "XMLHttpRequest"
        and request.GET.get("partial") == "compare_pick"
    )


def is_schedule_add_modal_get(request):
    """XHR GET that only loads the add-course modal body."""
    return (
        request.method == "GET"
        and request.GET.get("partial") == "modal"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


def schedule_messages_list(request) -> list[dict[str, str]]:
    """Consume pending Django messages and return JSON-serializable rows for async clients."""
    return [
        {"message": str(m.message), "tags": m.tags}
        for m in messages.get_messages(request)
    ]


def schedule_json_error_text(msgs: list[dict[str, str]], fallback: str) -> str:
    """Pick the best error string from consumed Django messages."""
    last_any = None
    last_error = None
    for item in msgs:
        text = item["message"]
        tags = item["tags"]
        last_any = text
        if "error" in tags:
            last_error = text
    return last_error or last_any or fallback


def schedule_json_redirect(request, redirect_to: str):
    """JSON redirect payload for async clients, else HTTP redirect."""
    if accepts_schedule_json(request):
        payload: dict = {"ok": True, "redirect": redirect_to}
        msgs = schedule_messages_list(request)
        if msgs:
            payload["messages"] = msgs
        return JsonResponse(payload)
    return redirect(redirect_to)


def schedule_json_error(
    request, message: str, *, fallback_url: str | None = None, status: int = 400
):
    """Return JSON error for async clients; otherwise flash and redirect."""
    if accepts_schedule_json(request):
        msgs = schedule_messages_list(request)
        if not msgs:
            msgs = [{"message": message, "tags": "error"}]
        err = schedule_json_error_text(msgs, message)
        return JsonResponse(
            {"ok": False, "error": err, "messages": msgs},
            status=status,
        )
    messages.error(request, message)
    dest = fallback_url if fallback_url is not None else reverse("schedule")
    return redirect(safe_next_url(request, dest))


def schedule_json_fail(
    request, *, status: int = 400, fallback_message: str
) -> JsonResponse:
    """JSON error after views used ``messages.*`` (consumes message storage)."""
    msgs = schedule_messages_list(request)
    if not msgs:
        msgs = [{"message": fallback_message, "tags": "error"}]
    err = schedule_json_error_text(msgs, fallback_message)
    return JsonResponse({"ok": False, "error": err, "messages": msgs}, status=status)
