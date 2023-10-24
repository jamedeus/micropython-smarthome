from django import template

register = template.Library()


@register.filter(name='combine_dicts')
def combine_dicts(dict1, dict2):
    '''Takes 2 context dicts, combines and returns single dict'''
    return {**dict1, **dict2}
