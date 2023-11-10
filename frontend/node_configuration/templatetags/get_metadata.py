from django import template

register = template.Library()


@register.filter(name='get_metadata')
def get_metadata(metadata_context, instance_params):
    '''Takes full metdata context and instance params, returns metadata'''

    # Instance is sensor if targets key present
    if "targets" in instance_params.keys():
        metadata = metadata_context['sensors'][instance_params['_type']]

        # If instance is thermostat convert limits to configured units
        if "units" in instance_params.keys():
            if instance_params['units'] == 'fahrenheit':
                metadata['rule_limits'][0] = '65'
                metadata['rule_limits'][1] = '80'
            elif instance_params['units'] == 'kelvin':
                metadata['rule_limits'][0] = '291.15'
                metadata['rule_limits'][1] = '300.15'

    # Instance is device if no targets key
    else:
        metadata = metadata_context['devices'][instance_params['_type']]

    return metadata
