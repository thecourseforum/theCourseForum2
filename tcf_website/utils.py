from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.utils.http import url_has_allowed_host_and_scheme


def paginate(items, page_number, per_page=10):
    """Paginate a queryset or list. Returns a Page object."""
    paginator = Paginator(items, per_page)
    try:
        return paginator.page(page_number)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


def safe_next_url(request, default_url: str) -> str:
    """Return validated next URL when present, otherwise default."""
    next_url = request.POST.get("next") or request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default_url
