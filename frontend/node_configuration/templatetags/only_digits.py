from django import template
import re

register = template.Library()


@register.filter(name='only_digits')
def only_digits(arg):
    '''Returns arg with all non-digit characters removed'''
    return ''.join(re.findall(r'\d+', arg))
