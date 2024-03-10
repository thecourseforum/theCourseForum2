from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(lst, index):
    try:
        return lst[index]
    except IndexError:
        return None
