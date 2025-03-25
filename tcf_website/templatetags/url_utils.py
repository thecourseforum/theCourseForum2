from django import template

register = template.Library()

@register.filter(name='change_page')
def change_page(request, pageNum):
    """Change the 'pages' search parameter to pageNum while preserving other query parameters."""
    current = request.GET.copy()
    if 'pages' in current:
        current['pages'] = pageNum
    else:
        current.update({'pages': pageNum})
    return current.urlencode()
