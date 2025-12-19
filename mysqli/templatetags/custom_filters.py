from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """
    Custom template filter to look up dictionary values by key
    Usage: {{ row|lookup:column }}
    """
    return dictionary.get(key, '')