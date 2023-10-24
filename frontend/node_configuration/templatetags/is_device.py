from django import template

register = template.Library()


@register.filter(name='is_device')
def is_device(arg):
    '''Returns True if arg starts with "device", otherwise False'''
    return arg.startswith('device')
