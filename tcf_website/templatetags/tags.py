# pylint: disable=missing-function-docstring

"""TCF Custom Template Tags"""

from django import template

register = template.Library()


@register.filter(name="split_times")
def split_times(value, arg):
    times = value.split(arg)
    newtimes = []
    for time in times:
        if len(time) > 0:
            newtimes.append(time[:-1].split(","))
    return newtimes
