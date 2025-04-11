"""Template tags for URL manipulation and query parameter handling."""

from django import template

register = template.Library()

@register.filter(name='change_page')
def change_page(request, page_num):
    """Change the 'pages' search parameter to page_num while preserving other query parameters."""
    current = request.GET.copy()
    if 'pages' in current:
        current['pages'] = page_num
    else:
        current.update({'pages': page_num})
    return current.urlencode()
