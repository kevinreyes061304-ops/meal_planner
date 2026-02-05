from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary"""
    if not dictionary:
        return {'recipe_id': None, 'custom_meal': '', 'notes': ''}
    return dictionary.get(key, {'recipe_id': None, 'custom_meal': '', 'notes': ''})