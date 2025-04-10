""" custom tags to be used in templates """

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """This filter is used to access a dictonary context variable"""
    return dictionary.get(key)


@register.filter
def remove_email(value):
    """This filter will remove the professors email from the string"""
    return str(value).split("(", maxsplit=1)[0]
