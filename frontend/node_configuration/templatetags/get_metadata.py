from django import template

register = template.Library()


@register.filter(name='get_metadata')
def get_metadata(metadata_context, instance_params,):
    '''Takes full metdata context and instance params, returns metadata'''
    if "targets" in instance_params.keys():
        return metadata_context['sensors'][instance_params['_type']]
    else:
        return metadata_context['devices'][instance_params['_type']]
