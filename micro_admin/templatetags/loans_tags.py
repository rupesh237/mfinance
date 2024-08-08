from django import template

register = template.Library()

@register.filter
def get_range(value):
    """
    Returns a range object from 0 to the given value.
    """
    return range(value)
