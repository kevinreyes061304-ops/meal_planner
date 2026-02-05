from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Template filter to get item from dictionary
    Usage: {{ my_dict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key, {})


@register.filter(name='add')
def add_strings(value, arg):
    """
    Template filter to concatenate strings
    Usage: {{ string1|add:string2 }}
    """
    try:
        return str(value) + str(arg)
    except:
        return value