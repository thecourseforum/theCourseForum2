""" custom tags to be used in templates """

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """This filter is used to access a dictonary context variable"""
    return dictionary.get(key)
