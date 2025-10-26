""" custom tags to be used in templates """

from django import template
import hashlib

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """This filter is used to access a dictonary context variable"""
    return dictionary.get(key)


@register.filter
def remove_email(value):
    """This filter will remove the professors email from the string"""
    return str(value).split("(", maxsplit=1)[0]


@register.filter
def tag_color(tag_name):
    """Returns a consistent Bootstrap color class for a given tag name"""
    if not tag_name:
        return "bg-secondary"
    
    # Normalize tag name for comparison
    normalized_tag = tag_name.lower().strip().replace('-', ' ').replace('_', ' ')
    
    # Special color mappings for common tags
    special_colors = {
        "first year": "bg-danger",  # Dark red color
        "second year": "bg-warning",  # Orange color
        "third year": "bg-info",
        "fourth year": "bg-success",
        "graduate": "bg-dark",
        "undergraduate": "bg-secondary",
        "social": "bg-success",
        "academic": "bg-info",
        "professional": "bg-dark",
        "cultural": "bg-danger",
        "sports": "bg-primary",
        "volunteer": "bg-success",
        "leadership": "bg-warning",
        "networking": "bg-info",
        "workshop": "bg-secondary",
        "seminar": "bg-dark",
        "meeting": "bg-primary",
        "event": "bg-success",
        "fundraiser": "bg-danger",
        "community": "bg-info",
    }
    
    # Check for special mappings first
    if normalized_tag in special_colors:
        return special_colors[normalized_tag]
    
    # Define available Bootstrap color classes for fallback
    colors = [
        "bg-primary",
        "bg-success", 
        "bg-info",
        "bg-warning",
        "bg-danger",
        "bg-dark",
        "bg-secondary"
    ]
    
    # Create a hash of the tag name to get consistent color
    tag_hash = int(hashlib.md5(tag_name.lower().encode()).hexdigest(), 16)
    color_index = tag_hash % len(colors)
    
    return colors[color_index]
