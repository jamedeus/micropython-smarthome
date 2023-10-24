from django import template

register = template.Library()


@register.filter(name='is_sensor')
def is_sensor(arg):
    '''Returns True if arg starts with "sensor", otherwise False'''
    return arg.startswith('sensor')
