from django.http import HttpResponse, JsonResponse
from django.db import connection


def healthz(request):
    """
    Lightweight health endpoint.
    - Returns 200 "ok" if process is up and DB is reachable.
    - Returns 500 if DB check fails.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:  # pylint: disable=broad-except
        return JsonResponse({"status": "unhealthy"}, status=500)
    return HttpResponse("ok", content_type="text/plain")
