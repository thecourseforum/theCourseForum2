from django.http import HttpResponsePermanentRedirect
from django.urls import reverse

from ...models import InstructorRedirect


def merged_instructor_redirect(request, instructor_id):
    target = (
        InstructorRedirect.objects.filter(old_id=instructor_id)
        .values_list("instructor_id", flat=True)
        .first()
    )
    if target is None:
        return None
    match = request.resolver_match
    url = reverse(match.view_name, kwargs={**match.kwargs, "instructor_id": target})
    query = request.META.get("QUERY_STRING", "")
    return HttpResponsePermanentRedirect(f"{url}?{query}" if query else url)
