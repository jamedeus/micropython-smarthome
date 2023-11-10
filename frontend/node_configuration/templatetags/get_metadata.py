from copy import deepcopy
from django import template
from helper_functions import convert_celsius_temperature

register = template.Library()


@register.filter(name='get_metadata')
def get_metadata(metadata_context, instance_params):
    '''Takes full metdata context and instance params, returns metadata'''

    # Instance is sensor if targets key present
    if "targets" in instance_params.keys():
        metadata = deepcopy(metadata_context['sensors'][instance_params['_type']])

        # If instance is thermostat convert limits to configured units
        if "units" in instance_params.keys():
            metadata['rule_limits'][0] = int(convert_celsius_temperature(
                metadata['rule_limits'][0],
                instance_params['units']
            ))
            metadata['rule_limits'][1] = int(convert_celsius_temperature(
                metadata['rule_limits'][1],
                instance_params['units']
            ))

    # Instance is device if no targets key
    else:
        metadata = metadata_context['devices'][instance_params['_type']]

    return metadata
