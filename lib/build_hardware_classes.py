#!/usr/bin/env python3
'''
This script is called by firmware/build.sh, do not upload it to ESP32s.
Generates a mapping dict used to dynamically import device/sensor classes.
Output is frozen into firmware, automatically updates when metadata changes.
'''

import os
import json


def get_hardware_classes():
    '''Iterates all device and sensor metadata objects and builds a mapping
    dict used by core/Config.py to determine the correct hardware class to
    instantiate based on config file _type param of each device and sensor.
    '''
    output = {'devices': {}, 'sensors': {}}

    # Resolve paths to util/metadata/devices and util/metadata/sensors
    lib = os.path.dirname(os.path.realpath(__file__))
    repo = os.path.split(lib)[0]
    device_metadata = os.path.join(repo, 'util', 'metadata', 'devices')
    sensor_metadata = os.path.join(repo, 'util', 'metadata', 'sensors')

    # Load each device metadata, map config name to python class name
    for i in os.listdir(device_metadata):
        with open(os.path.join(device_metadata, i), 'r') as file:
            params = json.load(file)
            output['devices'][params['config_name']] = params['class_name']

    # Load each sensor metadata, map config name to python class name
    for i in os.listdir(sensor_metadata):
        with open(os.path.join(sensor_metadata, i), 'r') as file:
            params = json.load(file)
            output['sensors'][params['config_name']] = params['class_name']

    return output


if __name__ == '__main__':
    # Generate mapping dict
    hardware_classes = get_hardware_classes()

    # Create single-line python file with variable containing mapping dict
    output_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'hardware_classes.py'
    )
    with open(output_path, 'w') as file:
        file.write(f'hardware_classes = {json.dumps(hardware_classes)}')
